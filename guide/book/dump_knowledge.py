"""Export what the guide pipeline knows about the pack into guide/book/knowledge.json.

The Modonomicon book builder (build_book.py) reads only that JSON, so the book can be rebuilt without
re-scanning every jar. Rerun this after recipe or worldgen changes:

    python guide/book/dump_knowledge.py --instance "<prism instance>/minecraft" --repo . \
        --vanilla <mcmeta-data> <mcmeta-assets> <forge generated resources>
"""
import argparse, collections, glob, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import build_guide as bg  # noqa: E402
import yaml  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--instance', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--vanilla', nargs='*', default=[])
    ap.add_argument('--out', default=os.path.join(HERE, 'knowledge.json'))
    a = ap.parse_args()
    args = argparse.Namespace(instance=a.instance, repo=a.repo, vanilla=a.vanilla,
                              yaml=os.path.join(a.repo, 'guide', 'guide.yaml'), out='/tmp/gbuild', pdf=None,
                              quicreate_jar_fallback=False, extra_mods=[], no_pdf=True)
    cfg = yaml.safe_load(open(args.yaml, encoding='utf-8'))
    cl = sorted(glob.glob(os.path.join(a.repo, 'quicreate_cleanup_*.ps1')))
    cleanup = bg.parse_cleanup_ps1(cl[-1]) if cl else {'scripts': [], 'data': set()}
    ct_removals, ct_recipes, _ = bg.parse_ct_scripts(os.path.join(args.instance, 'scripts'), cleanup['scripts'])
    pool, loaded, _jars = bg.build_pool(args, cleanup)
    w = bg.World(pool, loaded, cleanup['data']); w.load_lang(); w.load_tags(); w.load_recipes(ct_removals, ct_recipes)
    loot = bg.Loot(w); wg = bg.Worldgen(w, loot); scan = bg.StructureScan(w)
    k = bg.Knowledge(w, loot, wg, scan, cfg, args)
    groups, quests = bg.load_quests(os.path.join(args.instance, 'config', 'heracles'))
    os.makedirs('/tmp/gbuild/icons', exist_ok=True)
    icons = bg.Icons(w, '/tmp/gbuild/icons', cfg.get('icon_overrides'))
    g = bg.Guide(w, k, icons, groups, quests, cfg, args).plan()
    k.build(quests)

    def ing(gg):
        d = {'count': gg.count}
        if gg.fluid:
            d.update(fluid=gg.fluid, amount=gg.amount, name=w.name(gg.fluid))
        else:
            d.update(item=g.ing_display_item(gg), name=g.ing_name(gg))
            if gg.tag and len(gg.items) != 1:
                d['tag'] = gg.tag
        if gg.chance is not None and gg.chance < 0.9995:
            d['chance'] = gg.chance
        return d

    def recipe(r):
        label, _mi, extra, mitem = g.machine(r)
        d = {'id': r.id, 'type': r.type, 'machine': label, 'machine_item': mitem, 'extra': extra,
             'origin': g.origin_label(r), 'from_script': r.origin.startswith('CraftTweaker'),
             'inputs': [ing(x) for x in g.collapse(r.inputs)], 'outputs': [ing(x) for x in r.outputs[:6]]}
        if r.type == 'create:sequenced_assembly':
            d['loops'] = r.extra.get('loops', 1)
            d['steps'] = []
            for st in r.steps or []:
                lab, _m, ex, mit = g.machine(st)
                d['steps'].append({'machine': lab, 'adds': [ing(x) for x in (st.inputs[1:] if st.inputs else [])]})
        return d

    def gather(key):
        out = []
        rs = [r for r in w.by_output.get(key, []) if r.type in ('createsifter:sifting', 'create_mechanical_extruder:extruding')]
        rs.sort(key=lambda r: -max((o.chance for o in r.outputs if o.items and o.items[0] == key), default=0))
        for r in rs[:8]:
            os_ = [o for o in r.outputs if o.items and o.items[0] == key]
            p = 1 - math.prod(1 - (x.chance if x.chance is not None else 1) for x in os_) if os_ else 1
            if r.type == 'createsifter:sifting':
                out.append({'kind': 'sift', 'input': g.ing_name(r.inputs[0]) if r.inputs else '?',
                            'input_item': g.ing_display_item(r.inputs[0]) if r.inputs else None,
                            'mesh': r.extra.get('mesh'), 'mesh_name': w.name(r.extra.get('mesh') or ''),
                            'waterlogged': bool(r.extra.get('waterlogged')), 'chance': p})
            else:
                cat = r.extra.get('catalyst')
                out.append({'kind': 'extrude', 'catalyst': cat, 'catalyst_name': w.name(cat) if cat else None,
                            'fluids': [w.name(x.fluid) for x in r.inputs if x.fluid]})
        return out

    items = {}

    def describe(it, step_n=None):
        if not it or it.startswith('#') or it in items:
            return
        rs, more = g.best_recipes(it, step_n, 2, max_score=9, skip_gather=True)
        if not rs:
            rs, more = g.best_recipes(it, step_n, 1, skip_gather=True)
        items[it] = {'name': w.name(it), 'recipes': [recipe(r) for r in rs], 'more_recipes': more,
                     'gather': gather(it),
                     'natural': [d['text'] for d in k.natural_sources(it)[:6]],
                     'has_source': g.has_any_source(it)}

    qout = []
    for q in g.steps:
        n = g.step_no[q.id]
        for t in q.items():
            it = t.get('item', '')
            if it.startswith('#'):
                for x in w.tag_items(it[1:])[:3]:
                    describe(x, n)
            else:
                describe(bg.rl(it), n)
        qout.append({'id': q.id, 'group': q.group, 'step': n, 'title': q.title, 'subtitle': q.subtitle,
                     'desc': q.desc, 'deps': q.deps, 'soft_deps': g.soft_deps(q, {x.id for x in quests.values() if x.group == q.group}),
                     'tasks': q.tasks, 'icon': q.icon, 'pos': q.pos,
                     'tag_items': {t['item']: w.tag_items(t['item'][1:])[:12] for t in q.items() if t.get('item', '').startswith('#')}})

    # every item/block id the game knows by name (used to validate ids in hand-written content)
    known = set()
    for key in w.lang:
        m = re.match(r'(item|block)\.([a-z0-9_]+)\.([a-z0-9_./]+)$', key)
        if m:
            known.add(f'{m.group(2)}:{m.group(3)}')
    entities = sorted({f'{m.group(1)}:{m.group(2)}' for key in w.lang
                       for m in [re.match(r'entity\.([a-z0-9_]+)\.([a-z0-9_]+)$', key)] if m})

    planets = {}
    for key, p in k.planets.items():
        planets[key] = {
            'name': k.planet_name(key), 'dim': p['dim'],
            'biomes': [{'id': b, 'name': w.name(b)} for b in p['biomes']],
            'ores': [{'id': f, 'blocks': o['blocks'], 'height': o.get('height')} for f, o in p['ores'].items()],
            'mobs': [{'id': m, 'name': w.name(m), 'weight': d['weight'], 'cats': sorted(d['cats'])} for m, d in p['mobs'].items()],
            'structures': [{'id': s['id'], 'name': w.name(s['id']), 'biomes': s['biomes'],
                            'mobs': sorted(set(s['spawns']) | set(k.structures.get(s['id'], {}).get('mobs', [])))}
                           for s in p['structures']],
            'terrain': p['terrain'],
        }
    for key, p in planets.items():
        for m in p['mobs']:
            m['drops'] = [{'item': d['item'], 'name': w.name(d['item']), 'chance': d['chance']}
                          for d in loot.drops_of_entity(m['id']) if d.get('item')][:6]
        for s in p['structures']:
            for m in s['mobs']:
                describe_mob = [{'item': d['item'], 'name': w.name(d['item']), 'chance': d['chance']}
                                for d in loot.drops_of_entity(m) if d.get('item')][:6]
                s.setdefault('mob_drops', {})[m] = describe_mob

    bosses = []
    for b in cfg.get('bosses', []):
        bosses.append({'entity': b['entity'], 'name': w.name(b['entity']), 'planet': b.get('planet'),
                       'structure': b.get('structure'), 'quest': b.get('quest'),
                       'drops': [{'item': d['item'], 'name': w.name(d['item']), 'chance': d['chance'],
                                  'min': d.get('min'), 'max': d.get('max')}
                                 for d in loot.drops_of_entity(b['entity']) if d.get('item')][:8]})

    # sifting tables and extruder catalysts
    sift = collections.defaultdict(list)
    extrude = []
    for r in w.recipes:
        if r.type == 'createsifter:sifting' and r.inputs:
            sift[(g.ing_display_item(r.inputs[0]), r.extra.get('mesh'), bool(r.extra.get('waterlogged')))].append(
                [{'item': o.items[0], 'name': w.name(o.items[0]), 'chance': o.chance, 'count': o.count}
                 for o in r.outputs if o.items])
        elif r.type == 'create_mechanical_extruder:extruding':
            extrude.append({'catalyst': r.extra.get('catalyst'), 'catalyst_name': w.name(r.extra.get('catalyst') or ''),
                            'outputs': [o.items[0] for o in r.outputs if o.items],
                            'fluids': [x.fluid for x in r.inputs if x.fluid],
                            'blocks': [x.items[0] for x in r.inputs if x.items], 'id': r.id})
    sift_out = [{'input': i, 'input_name': w.name(i or ''), 'mesh': m, 'mesh_name': w.name(m or ''), 'waterlogged': wl,
                 'outputs': [o for lst in v for o in lst]} for (i, m, wl), v in sift.items()]

    out = {'quests': qout, 'groups': groups, 'items': items, 'known_items': sorted(known), 'entities': entities,
           'planets': planets, 'bosses': bosses, 'sifting': sift_out, 'extruding': extrude,
           'names': {}, 'island': k.island,
           'fishing': [{'rod': t['rod'], 'tier': t['tier'], 'data': t['t']} for t in (k.fishing or [])]}
    # names for every id we mention (filled lazily by the builder through 'name_of')
    for i in list(known):
        out['names'][i] = w.name(i)
    for e in entities:
        out['names'][e] = w.name(e)
    for p in planets.values():
        for b in p['biomes']:
            out['names'][b['id']] = b['name']
        for s in p['structures']:
            out['names'][s['id']] = s['name']
    # recipe ids that exist as plain crafting/smelting json (safe for Modonomicon recipe pages)
    out['page_recipes'] = {}
    for r in w.recipes:
        if r.type in ('minecraft:crafting_shaped', 'minecraft:crafting_shapeless', 'minecraft:smelting',
                      'minecraft:blasting', 'minecraft:smoking', 'minecraft:stonecutting', 'minecraft:smithing_transform') \
                and not r.origin.startswith('CraftTweaker') and r.outputs and r.outputs[0].items:
            out['page_recipes'].setdefault(r.outputs[0].items[0], []).append({'id': r.id, 'type': r.type})
    out['obtainable'] = sorted(i for i in known if g.has_any_source(i))
    json.dump(out, open(a.out, 'w'), indent=1, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
    print('wrote', a.out, len(items), 'items', len(qout), 'quests')


if __name__ == '__main__':
    main()
