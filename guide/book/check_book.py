"""Sanity checks for the generated book. Run after build_book.py:

    python guide/book/check_book.py --resources src/main/resources
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_book as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resources', required=True)
    a = ap.parse_args()
    res = a.resources
    k = json.load(open(os.path.join(HERE, 'knowledge.json')))
    import book_text as T
    known = set(k['known_items']) | set(T.EXTRA_KNOWN)
    ents = set(k['entities'])
    lang = json.load(open(os.path.join(res, 'assets/quicreate/lang/en_us.json'), encoding='utf-8'))
    base = os.path.join(res, 'data/quicreate/modonomicon/books/skyblock')
    cats = {f'quicreate:{os.path.basename(p)[:-5]}' for p in glob.glob(f'{base}/categories/*.json')}
    entries = {}
    for p in glob.glob(f'{base}/entries/*/*.json'):
        cat = os.path.basename(os.path.dirname(p))
        entries[f'quicreate:{cat}/{os.path.basename(p)[:-5]}'] = json.load(open(p, encoding='utf-8'))
    advs = set()
    for p in glob.glob(os.path.join(res, 'data/quicreate/advancements/**/*.json'), recursive=True):
        rel = os.path.relpath(p, os.path.join(res, 'data/quicreate/advancements'))[:-5].replace(os.sep, '/')
        advs.add(f'quicreate:{rel}')
    mbs = {f'quicreate:{os.path.basename(p)[:-5]}' for p in glob.glob(os.path.join(res, 'data/quicreate/modonomicon/multiblocks/*.json'))}
    recipes = set()
    for lst in k['page_recipes'].values():
        recipes |= {r['id'] for r in lst}
    errs, warns = [], []

    def txt(key):
        if key not in lang:
            errs.append(f'missing lang {key}')
            return ''
        return lang[key]

    def cond_check(c, where):
        if not c:
            return
        t = c['type']
        if t == 'modonomicon:advancement':
            if c['advancement_id'] not in advs:
                errs.append(f'{where}: advancement {c["advancement_id"]} missing')
        elif t in ('modonomicon:entry_read', 'modonomicon:entry_unlocked'):
            if c['entry_id'] not in entries:
                errs.append(f'{where}: entry {c["entry_id"]} missing')
        elif t in ('modonomicon:and', 'modonomicon:or'):
            for ch in c['children']:
                cond_check(ch, where)
        else:
            errs.append(f'{where}: odd condition {t}')
        if 'tooltip' in c:
            txt(c['tooltip'])

    positions = {}
    for eid, e in entries.items():
        if e['category'] not in cats:
            errs.append(f'{eid}: category {e["category"]} missing')
        if e['icon'] not in known:
            errs.append(f'{eid}: icon {e["icon"]} unknown')
        pos = (e['category'], e['x'], e['y'])
        if pos in positions:
            errs.append(f'{eid}: same spot as {positions[pos]}')
        positions[pos] = eid
        txt(e['name'])
        if 'description' in e:
            txt(e['description'])
        cond_check(e.get('condition'), eid)
        for p in e.get('parents', []):
            if p['entry'] not in entries:
                errs.append(f'{eid}: parent {p["entry"]} missing')
            elif entries[p['entry']]['category'] != e['category']:
                errs.append(f'{eid}: parent {p["entry"]} in another tab')
        if 'category_to_open' in e and e['category_to_open'] not in cats:
            errs.append(f'{eid}: links to missing tab {e["category_to_open"]}')
        for i, pg in enumerate(e.get('pages', [])):
            w = f'{eid} page {i}'
            cond_check(pg.get('condition'), w)
            t = pg['type']
            body = txt(pg['text']) if 'text' in pg else ''
            if 'title' in pg:
                txt(pg['title'])
            cap = {'modonomicon:text': B.LINES_TITLED if 'title' in pg else B.LINES_PLAIN,
                   'modonomicon:spotlight': B.LINES_SPOTLIGHT, 'modonomicon:entity': B.LINES_ENTITY,
                   'modonomicon:image': B.LINES_IMAGE, 'modonomicon:multiblock': B.LINES_MULTIBLOCK}.get(t, B.LINES_RECIPE)
            n = B.count_lines(body) if body else 0
            if n > cap:
                warns.append(f'{w}: {n} lines > {cap} ({t})')
            for m in re.finditer(r'\]\(entry://([^)#@]+)', body):
                link = m.group(1)
                if not link.startswith('quicreate:skyblock/'):
                    errs.append(f'{w}: entry link without the book id: {link}')
                    continue
                if 'quicreate:' + link.split('/', 1)[1] not in entries:
                    errs.append(f'{w}: link to missing entry {m.group(1)}')
            for m in re.finditer(r'\]\(item://([^)]+)\)', body):
                if m.group(1) not in known:
                    errs.append(f'{w}: item link {m.group(1)} unknown')
            if t == 'modonomicon:spotlight':
                it = pg['item'].get('item')
                if it and it not in known:
                    errs.append(f'{w}: spotlight item {it} unknown')
            if t == 'modonomicon:entity' and pg['entity_id'].split('{')[0] not in ents:
                errs.append(f'{w}: entity {pg["entity_id"]} unknown')
            if t == 'modonomicon:multiblock' and pg['multiblock_id'] not in mbs:
                errs.append(f'{w}: multiblock {pg["multiblock_id"]} missing')
            if t.endswith('_recipe'):
                for f in ('recipe_id_1', 'recipe_id_2'):
                    if f in pg and pg[f] not in recipes:
                        errs.append(f'{w}: recipe {pg[f]} not found')
            if t == 'modonomicon:image':
                for im in pg['images']:
                    ns, path = im.split(':')
                    if ns == 'quicreate' and not os.path.exists(os.path.join(res, 'assets', ns, path)):
                        errs.append(f'{w}: image {im} missing')
    for p in glob.glob(os.path.join(res, 'data/quicreate/advancements/**/*.json'), recursive=True):
        j = json.load(open(p))
        par = j.get('parent')
        if par and par not in advs:
            errs.append(f'{p}: parent {par} missing')
        for c in j.get('criteria', {}).values():
            cc = c.get('conditions', {})
            it = cc.get('item')
            if it and it not in known:
                errs.append(f'{p}: item {it} unknown')
            for ip in cc.get('items', []):
                for x in ip.get('items', []):
                    if x not in known:
                        errs.append(f'{p}: item {x} unknown')
            e = (cc.get('entity') or {}).get('type')
            if e and e not in ents:
                errs.append(f'{p}: entity {e} unknown')
        d = j.get('display')
        if d and d['icon']['item'] not in known:
            errs.append(f'{p}: icon {d["icon"]["item"]} unknown')
    print(f'{len(entries)} entries, {len(cats)} tabs, {len(advs)} advancements')
    for e in errs:
        print('ERROR', e)
    for w in warns:
        print('warn', w)
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
