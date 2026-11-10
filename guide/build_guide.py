#!/usr/bin/env python3
"""
Quicreate Skyblock walkthrough builder.

Reads the pack's own files (Heracles quest book, CraftTweaker scripts, the Quicreate
datapack in this repo, every mod jar in the instance and the vanilla client data),
works out recipes and where every raw material comes from, renders item icons from the
real textures, and writes an HTML walkthrough that is printed to PDF with WeasyPrint.

Nothing about recipes, drops or worldgen is typed in by hand: the prose lives in
guide.yaml, the facts come from the files.  Run with --help for the options, and see
README.md next to this file.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import html
import io
import json
import math
import os
import re
import sys
import zipfile

import yaml
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))


def log(*a):
    print(*a, file=sys.stderr)


def esc(s):
    return html.escape(str(s), quote=True)


def loads_lenient(raw: bytes):
    """JSON with // comments or trailing commas (some mods ship those)."""
    txt = raw.decode('utf-8-sig', 'replace')
    try:
        return json.loads(txt)
    except Exception:
        txt = re.sub(r'(?m)^\s*//.*$', '', txt)
        txt = re.sub(r',\s*([}\]])', r'\1', txt)
        return json.loads(txt)


# =====================================================================================
# 1. Resource sources (folders and jars), stacked like Minecraft's resource/datapacks
# =====================================================================================

class Source:
    """A folder or a zip/jar that contains assets/ and/or data/."""

    def __init__(self, name, path, prefix_filter=None, skip=None):
        self.name = name
        self.path = path
        self.skip = skip or set()
        self.is_zip = os.path.isfile(path)
        self.files = {}
        if self.is_zip:
            self.zip = zipfile.ZipFile(path)
            for n in self.zip.namelist():
                if n.endswith('/'):
                    continue
                if n.startswith('assets/') or n.startswith('data/') or n.startswith('META-INF/mods.toml'):
                    self.files[n] = n
        else:
            for root, _dirs, fnames in os.walk(path):
                for f in fnames:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, path).replace(os.sep, '/')
                    if rel.startswith('assets/') or rel.startswith('data/'):
                        self.files[rel] = full
        for s in list(self.files):
            if s in self.skip:
                del self.files[s]

    def read(self, rel):
        p = self.files[rel]
        if self.is_zip:
            return self.zip.read(p)
        with open(p, 'rb') as fh:
            return fh.read()

    def mod_ids(self):
        if not self.is_zip or 'META-INF/mods.toml' not in self.files:
            return []
        t = self.zip.read('META-INF/mods.toml').decode('utf-8', 'replace')
        ids = []
        for block in re.split(r'(?m)^\s*\[\[', t):
            if block.startswith('mods]]'):
                m = re.search(r'(?m)^\s*modId\s*=\s*"([^"]+)"', block)
                if m:
                    ids.append(m.group(1))
        return ids


class Pool:
    """Ordered sources, low priority first. The highest source with a path wins."""

    def __init__(self, sources):
        self.sources = sources
        self.index = {}
        for s in sources:
            for rel in s.files:
                self.index[rel] = s
        self._json_cache = {}

    def has(self, rel):
        return rel in self.index

    def read(self, rel):
        return self.index[rel].read(rel)

    def json(self, rel):
        if rel not in self._json_cache:
            try:
                self._json_cache[rel] = loads_lenient(self.read(rel))
            except Exception as e:  # broken json in some jar
                log('  ! bad json', rel, e)
                self._json_cache[rel] = None
        return self._json_cache[rel]

    def source_of(self, rel):
        return self.index[rel].name

    def list(self, prefix, suffix=''):
        return sorted(r for r in self.index if r.startswith(prefix) and r.endswith(suffix))

    def all_layers(self, rel):
        """Every source that has rel (for tags, which merge across packs)."""
        return [s for s in self.sources if rel in s.files]


def rl(s, default_ns='minecraft'):
    s = s.strip()
    if s.startswith('#'):
        s = s[1:]
    return s if ':' in s else f'{default_ns}:{s}'


def split_rl(s):
    ns, path = rl(s).split(':', 1)
    return ns, path


# =====================================================================================
# 2. Cleanup script (files Jake will delete) and CraftTweaker scripts
# =====================================================================================

def parse_cleanup_ps1(path):
    """Return (removed data paths, removed script names, moves) listed in the cleanup script."""
    res = {'data': set(), 'scripts': set(), 'moves': [], 'path': path}
    if not path or not os.path.exists(path):
        return res
    s = open(path, encoding='utf-8-sig').read()

    def block(name):
        m = re.search(r'\$' + name + r'\s*=\s*@\((.*?)\n\)', s, re.S)
        return m.group(1) if m else ''
    for a, b in re.findall(r'@\("([^"]+)",\s*"([^"]+)"\)', block('moves')):
        res['moves'].append((a, b))
        res['data'].add('data/' + a)          # the old name disappears after the move
    for f in re.findall(r'"([^"]+)"', block('deleteData')):
        res['data'].add('data/' + f)
    for f in re.findall(r'"([^"]+)"', block('deleteScripts')):
        res['scripts'].add(f)
    return res


CT_ITEM = re.compile(r'<(item|tag:items|tag):([a-z0-9_.\-]+:[a-z0-9_./\-]+)>(?:\s*\*\s*(\d+))?')


def ct_ing(tok):
    tok = tok.strip()
    m = CT_ITEM.fullmatch(tok)
    if not m:
        return None
    kind, ident, n = m.groups()
    if kind == 'item' and ident == 'minecraft:air':
        return None
    d = {'tag': ident} if kind.startswith('tag') else {'item': ident}
    if n:
        d['count'] = int(n)
    return d


def parse_ct_scripts(folder, skip_names=()):
    """Parse the simple CraftTweaker calls this pack uses.

    Returns (removals, recipes, unparsed) where removals is a list of (manager, output item)
    and recipes are vanilla-style JSON dicts with an extra '_ct' key (script name)."""
    removals, recipes, unparsed = [], [], []
    if not folder or not os.path.isdir(folder):
        return removals, recipes, unparsed
    for path in sorted(glob.glob(os.path.join(folder, '**', '*.zs'), recursive=True)):
        name = os.path.basename(path)
        if name in skip_names:
            continue
        src = open(path, encoding='utf-8-sig').read()
        body = re.sub(r'(?m)^\s*import [^;]+;', '', src)
        body = re.sub(r'//[^\n]*', '', body)
        for stmt in [x.strip() for x in body.split(';') if x.strip()]:
            m = re.match(r'(craftingTable|furnace|blastFurnace|smoker|campfire|stoneCutter)\.remove\((.*)\)$', stmt, re.S)
            if m:
                ing = ct_ing(m.group(2))
                if ing:
                    removals.append((m.group(1), ing.get('item') or ('#' + ing['tag']), name))
                else:
                    unparsed.append((name, stmt))
                continue
            m = re.match(r'craftingTable\.(addShaped|addShapedMirrored|addShapeless)\((.*)\)$', stmt, re.S)
            if m:
                kind, args = m.groups()
                args = re.sub(r'MirrorAxis\.\w+\s*,', '', args)
                mname = re.match(r'\s*"([^"]+)"\s*,', args)
                rest = args[mname.end():] if mname else args
                out_m = CT_ITEM.search(rest)
                if not out_m:
                    unparsed.append((name, stmt))
                    continue
                out = ct_ing(out_m.group(0))
                grid_txt = rest[out_m.end():]
                if kind == 'addShapeless':
                    ings = [ct_ing(t.group(0)) for t in CT_ITEM.finditer(grid_txt)]
                    recipes.append({'type': 'minecraft:crafting_shapeless',
                                    'ingredients': [i for i in ings if i],
                                    'result': {'item': out['item'], 'count': out.get('count', 1)},
                                    '_ct': name, '_id': 'crafttweaker:' + (mname.group(1) if mname else name)})
                else:
                    rows = re.findall(r'\[([^\[\]]*)\]', grid_txt)
                    grid = []
                    for row in rows:
                        cells = [c.strip() for c in row.split(',') if c.strip()]
                        grid.append([ct_ing(c) for c in cells])
                    # trim empty outer rows/cols like the game does
                    key, pattern, letters = {}, [], {}
                    for row in grid:
                        line = ''
                        for c in row:
                            if c is None:
                                line += ' '
                                continue
                            k = json.dumps(c, sort_keys=True)
                            if k not in letters:
                                letters[k] = chr(ord('A') + len(letters))
                                key[letters[k]] = c
                            line += letters[k]
                        pattern.append(line)
                    while pattern and not pattern[0].strip():
                        pattern.pop(0)
                    while pattern and not pattern[-1].strip():
                        pattern.pop()
                    if pattern:
                        w = max(len(p) for p in pattern)
                        pattern = [p.ljust(w) for p in pattern]
                        left = min(len(p) - len(p.lstrip()) for p in pattern if p.strip())
                        right = min(len(p) - len(p.rstrip()) for p in pattern if p.strip())
                        pattern = [p[left:len(p) - right] for p in pattern]
                    recipes.append({'type': 'minecraft:crafting_shaped', 'pattern': pattern, 'key': key,
                                    'result': {'item': out['item'], 'count': out.get('count', 1)},
                                    '_ct': name, '_id': 'crafttweaker:' + (mname.group(1) if mname else name)})
                continue
            m = re.match(r'(furnace|blastFurnace|smoker)\.addRecipe\((.*)\)$', stmt, re.S)
            if m:
                mgr, args = m.groups()
                mname = re.match(r'\s*"([^"]+)"\s*,', args)
                toks = [t.group(0) for t in CT_ITEM.finditer(args)]
                if len(toks) >= 2:
                    out, inp = ct_ing(toks[0]), ct_ing(toks[1])
                    typ = {'furnace': 'minecraft:smelting', 'blastFurnace': 'minecraft:blasting',
                           'smoker': 'minecraft:smoking'}[mgr]
                    nums = re.findall(r',\s*([0-9.]+)\s*(?=,|$)', args)
                    recipes.append({'type': typ, 'ingredient': inp, 'result': out['item'],
                                    'cookingtime': int(float(nums[-1])) if nums else 200,
                                    '_ct': name, '_id': 'crafttweaker:' + (mname.group(1) if mname else name)})
                    continue
            unparsed.append((name, stmt))
    return removals, recipes, unparsed


# =====================================================================================
# 3. The world: tags, names, recipe normalisation
# =====================================================================================

class Ing:
    """One recipe slot: a list of accepted items (or a fluid), a count and maybe a chance."""
    __slots__ = ('items', 'tag', 'count', 'fluid', 'amount', 'chance', 'note')

    def __init__(self, items=(), tag=None, count=1, fluid=None, amount=0, chance=1.0, note=None):
        self.items = list(items)
        self.tag = tag
        self.count = count
        self.fluid = fluid
        self.amount = amount
        self.chance = chance
        self.note = note

    def key(self):
        return self.fluid or self.tag or (self.items[0] if self.items else '?')

    def __repr__(self):
        return f'Ing({self.key()} x{self.count or self.amount} p{self.chance})'


class Recipe:
    __slots__ = ('id', 'type', 'inputs', 'outputs', 'grid', 'extra', 'origin', 'steps')

    def __init__(self, rid, typ, inputs, outputs, grid=None, extra=None, origin='', steps=None):
        self.id = rid
        self.type = typ
        self.inputs = inputs
        self.outputs = outputs
        self.grid = grid          # list of rows of Ing|None for shaped / mechanical crafting
        self.extra = extra or {}
        self.origin = origin      # which pack/script added it
        self.steps = steps        # sequenced assembly steps (list of Recipe)

    def output_items(self):
        return [o.items[0] for o in self.outputs if o.items]

    def __repr__(self):
        return f'Recipe({self.id} {self.type} {self.inputs} -> {self.outputs})'


class World:
    def __init__(self, pool: Pool, loaded_mods: set, removed_data: set):
        self.pool = pool
        self.loaded_mods = loaded_mods
        self.removed = removed_data
        self.lang = {}
        self.item_tags = {}
        self.block_tags = {}
        self.biome_tags = {}
        self.entity_tags = {}
        self.recipes = []
        self.by_output = collections.defaultdict(list)
        self.by_input = collections.defaultdict(list)
        self.known_items = set()
        self.ct_removed = []
        self.notes = []

    # ---------------------------------------------------------------- names
    def load_lang(self):
        for rel in self.pool.list('assets/', '/lang/en_us.json'):
            for s in self.pool.all_layers(rel):
                try:
                    self.lang.update(loads_lenient(s.read(rel)))
                except Exception:
                    pass
        for k in self.lang:
            m = re.match(r'(item|block)\.([a-z0-9_]+)\.([a-z0-9_/.]+)$', k)
            if m:
                self.known_items.add(f'{m.group(2)}:{m.group(3)}')
        for rel in self.pool.list('assets/', '.json'):
            m = re.match(r'assets/([^/]+)/models/item/(.+)\.json$', rel)
            if m:
                self.known_items.add(f'{m.group(1)}:{m.group(2)}')

    def name(self, ident):
        n = self._name(ident)
        n = re.sub(r'§k.*?(?=§|$)', '', n)        # obfuscated text
        n = re.sub(r'§.', '', n).strip()
        n = re.sub(r'([a-z])([A-Z])', r'\1 \2', n) if '§' in self._name(ident) else n
        if n in ('Card', 'Huge Card', '') and ':' in str(ident):
            n = split_rl(ident)[1].replace('_', ' ').title()
            n = n if 'Card' in n else n + ' Card'
        return n

    def _name(self, ident):
        ident = rl(ident)
        ns, path = ident.split(':', 1)
        for k in (f'item.{ns}.{path}', f'block.{ns}.{path}', f'fluid.{ns}.{path}',
                  f'fluid_type.{ns}.{path}', f'entity.{ns}.{path}', f'biome.{ns}.{path}',
                  f'structure.{ns}.{path}', f'item.{ns}.{path.replace("/", ".")}'):
            if k in self.lang:
                return self.lang[k]
        # fluids are often named after their bucket or block
        for k in (f'block.{ns}.{path}', f'item.{ns}.{path}_bucket'):
            if k in self.lang:
                return self.lang[k].replace(' Bucket', '')
        return path.replace('_', ' ').replace('/', ' ').title()

    # ---------------------------------------------------------------- tags
    def _load_tag_dir(self, kind, store):
        pat = re.compile(r'data/([^/]+)/tags/' + kind + r'/(.+)\.json$')
        raw = collections.defaultdict(list)
        for rel in self.pool.list('data/', '.json'):
            m = pat.match(rel)
            if not m:
                continue
            tid = f'{m.group(1)}:{m.group(2)}'
            for s in self.pool.all_layers(rel):
                if rel in self.removed and s.name.startswith('quicreate'):
                    continue
                try:
                    j = loads_lenient(s.read(rel))
                except Exception:
                    continue
                if j.get('replace'):
                    raw[tid] = []
                raw[tid].extend(j.get('values', []))
        resolved = {}

        def res(tid, depth=0):
            if tid in resolved:
                return resolved[tid]
            if depth > 30:
                return []
            out = []
            for v in raw.get(tid, []):
                req = True
                if isinstance(v, dict):
                    req = v.get('required', True)
                    v = v.get('id')
                if not isinstance(v, str):
                    continue
                if v.startswith('#'):
                    out.extend(res(rl(v[1:]), depth + 1))
                else:
                    out.append(rl(v))
            seen, uniq = set(), []
            for x in out:
                if x not in seen:
                    seen.add(x)
                    uniq.append(x)
            resolved[tid] = uniq
            return uniq
        for tid in raw:
            res(tid)
        store.update(resolved)

    def load_tags(self):
        self._load_tag_dir('items', self.item_tags)
        self._load_tag_dir('blocks', self.block_tags)
        self._load_tag_dir('worldgen/biome', self.biome_tags)
        self._load_tag_dir('entity_types', self.entity_tags)

    def tag_items(self, tag):
        items = self.item_tags.get(rl(tag), [])
        known = [i for i in items if i in self.known_items]
        return known or items

    # ---------------------------------------------------------------- conditions
    def cond_ok(self, conds):
        if not conds:
            return True
        if isinstance(conds, dict):
            conds = [conds]
        for c in conds:
            if not self._cond(c):
                return False
        return True

    def _cond(self, c):
        t = c.get('type') or c.get('condition') or ''
        if t in ('forge:mod_loaded', 'fabric:all_mods_loaded'):
            mods = [c['modid']] if 'modid' in c else c.get('values', [])
            return all(m in self.loaded_mods for m in mods)
        if t == 'forge:not':
            return not self._cond(c['value'])
        if t == 'forge:and':
            return all(self._cond(x) for x in c['values'])
        if t == 'forge:or':
            return any(self._cond(x) for x in c['values'])
        if t == 'forge:false':
            return False
        if t == 'forge:true':
            return True
        if t == 'forge:item_exists':
            return rl(c['item']) in self.known_items
        if t == 'forge:tag_empty':
            return not self.item_tags.get(rl(c['tag']))
        if t.endswith('mod_loaded') or t.endswith('modloaded'):
            return c.get('modid', '') in self.loaded_mods
        return True  # unknown condition types (configs) are assumed true

    # ---------------------------------------------------------------- ingredients
    def ing(self, j, count_key='count'):
        if j is None:
            return None
        if isinstance(j, list):
            alts, tag = [], None
            for x in j:
                g = self.ing(x)
                if g:
                    alts.extend(g.items)
                    tag = tag or g.tag
            return Ing(alts, tag=None if len(j) > 1 else tag) if alts else None
        if isinstance(j, str):
            if j.startswith('#'):
                return Ing(self.tag_items(j[1:]), tag=rl(j[1:]))
            return Ing([rl(j)])
        if not isinstance(j, dict):
            return None
        if 'ingredient' in j and isinstance(j['ingredient'], (dict, list)):  # ad astra / wrappers
            g = self.ing(j['ingredient'])
            if g:
                g.count = j.get('count', g.count)
                if 'millibuckets' in j:
                    g.fluid, g.amount = g.tag or (g.items[0] if g.items else None), j['millibuckets']
            return g
        n = j.get(count_key, j.get('count', 1))
        if 'fluid' in j or 'fluidTag' in j or 'fluid_tag' in j:
            f = j.get('fluid') or j.get('fluidTag') or j.get('fluid_tag')
            if isinstance(f, dict):
                f = f.get('name') or f.get('id')
            amount = j.get('amount', j.get('millibuckets', 1000))
            return Ing([], fluid=rl(f), amount=amount, chance=j.get('chance', 1.0))
        if 'tag' in j:
            return Ing(self.tag_items(j['tag']), tag=rl(j['tag']), count=n, chance=j.get('chance', 1.0))
        if 'item' in j or 'id' in j:
            item = j.get('item') or j.get('id')
            return Ing([rl(item)], count=n, chance=j.get('chance', 1.0))
        t = j.get('type', '')
        if t in ('forge:compound', 'forge:difference', 'forge:intersection'):
            base = j.get('children') or j.get('base')
            return self.ing(base)
        if t == 'forge:nbt' or 'nbt' in j:
            return Ing([rl(j.get('item', '?'))], count=n)
        return None

    def result(self, j):
        if j is None:
            return []
        if isinstance(j, str):
            return [Ing([rl(j)])]
        if isinstance(j, list):
            out = []
            for x in j:
                out.extend(self.result(x))
            return out
        if 'fluid' in j:
            return [Ing([], fluid=rl(j['fluid']), amount=j.get('amount', j.get('millibuckets', 1000)),
                        chance=j.get('chance', 1.0))]
        item = j.get('item') or j.get('id')
        if not item:
            return []
        return [Ing([rl(item)], count=j.get('count', 1), chance=j.get('chance', 1.0))]

    # ---------------------------------------------------------------- recipes
    def norm(self, rid, j, origin):
        if not isinstance(j, dict):
            return None
        t = j.get('type', '')
        if t == 'forge:conditional':
            for r in j.get('recipes', []):
                if self.cond_ok(r.get('conditions')):
                    return self.norm(rid, r.get('recipe'), origin)
            return None
        if not self.cond_ok(j.get('conditions')):
            return None
        ns = t.split(':')[0]
        if ns not in ('minecraft', 'forge') and ns not in self.loaded_mods:
            return None  # recipe type from a mod that is not installed
        res = self.result
        I = self.ing
        try:
            if t in ('minecraft:crafting_shaped', 'create:mechanical_crafting'):
                key = {k: I(v) for k, v in j.get('key', {}).items()}
                grid = [[key.get(ch) if ch != ' ' else None for ch in row] for row in j.get('pattern', [])]
                inputs = [g for row in grid for g in row if g]
                return Recipe(rid, t, inputs, res(j.get('result')), grid=grid, origin=origin)
            if t == 'minecraft:crafting_shapeless':
                return Recipe(rid, t, [g for g in (I(x) for x in j.get('ingredients', [])) if g],
                              res(j.get('result')), origin=origin)
            if t in ('minecraft:smelting', 'minecraft:blasting', 'minecraft:smoking',
                     'minecraft:campfire_cooking', 'minecraft:stonecutting'):
                r = j.get('result')
                outs = res(r) if not isinstance(r, str) else [Ing([rl(r)], count=j.get('count', 1))]
                return Recipe(rid, t, [I(j.get('ingredient'))], outs,
                              extra={'time': j.get('cookingtime')}, origin=origin)
            if t == 'minecraft:smithing_transform':
                return Recipe(rid, t, [g for g in (I(j.get('template')), I(j.get('base')), I(j.get('addition'))) if g],
                              res(j.get('result')), origin=origin)
            if t == 'create:sequenced_assembly':
                steps = []
                for st in j.get('sequence', []):
                    sr = self.norm(rid + '#step', st, origin)
                    if sr:
                        steps.append(sr)
                return Recipe(rid, t, [I(j.get('ingredient'))], res(j.get('results')),
                              extra={'loops': j.get('loops', 1),
                                     'transitional': (I(j.get('transitionalItem')) or Ing()).key()},
                              origin=origin, steps=steps)
            if t.startswith('create:') or t in ('createsifter:sifting', 'create_new_age:energising',
                                                'createutilities:mixing', 'createutilities:pressing'):
                ins = [g for g in (I(x) for x in j.get('ingredients', [])) if g]
                extra = {}
                if j.get('heatRequirement'):
                    extra['heat'] = j['heatRequirement']
                if j.get('keepHeldItem'):
                    extra['keep_held'] = True
                if t == 'createsifter:sifting':
                    mesh = [g for g in ins if g.items and ('mesh' in g.items[0])]
                    extra['mesh'] = mesh[0].items[0] if mesh else None
                    ins = [g for g in ins if g not in mesh]
                    extra['waterlogged'] = bool(j.get('waterlogged'))
                if t == 'create_new_age:energising':
                    extra['energy'] = j.get('energy_needed')
                if 'processingTime' in j:
                    extra['time'] = j['processingTime']
                return Recipe(rid, t, ins, res(j.get('results')), extra=extra, origin=origin)
            if t == 'create_mechanical_extruder:extruding':
                ins = [g for g in (I(x) for x in j.get('ingredients', [])) if g]
                extra = {'catalyst': (I(j['catalyst']).items[0] if j.get('catalyst') and I(j['catalyst']) else None),
                         'bonks': j.get('requiredBonks')}
                return Recipe(rid, t, ins, res(j.get('result')), extra=extra, origin=origin)
            if t == 'ad_astra:nasa_workbench':
                ins = [g for g in (I(x) for x in j.get('ingredients', [])) if g]
                return Recipe(rid, t, ins, res(j.get('result')), origin=origin)
            if t in ('ad_astra:alloying', 'ad_astra:compressing'):
                ins = [g for g in (I(x) for x in (j.get('ingredients') or [j.get('ingredient')])) if g]
                return Recipe(rid, t, ins, res(j.get('result')),
                              extra={'energy': j.get('energy'), 'time': j.get('cookingtime')}, origin=origin)
            if t in ('ad_astra:cryo_freezing', 'ad_astra:refining', 'ad_astra:oxygen_loading'):
                src = j.get('ingredient') or j.get('input')
                g = I(src)
                if g and 'millibuckets' in (src or {}) and not g.fluid:
                    g.fluid, g.amount = g.tag or g.items[0], src['millibuckets']
                out = j.get('result') or {}
                outs = [Ing([], fluid=rl(out['fluid']), amount=out.get('millibuckets', 0))] if 'fluid' in out else res(out)
                return Recipe(rid, t, [g] if g else [], outs,
                              extra={'energy': j.get('energy'), 'time': j.get('cookingtime')}, origin=origin)
            if t == 'cataclysm:weapon_fusion':
                return Recipe(rid, t, [g for g in (I(j.get('base')), I(j.get('addition'))) if g],
                              res(j.get('result')), origin=origin)
            if t.startswith('cards:') and t.endswith('_cards'):
                g = I((j.get('ingredients') or [None])[0])
                return Recipe(rid, 'cards:pack_contents', [g] if g else [], res(j.get('output')),
                              extra={'pack_type': t}, origin=origin)
            if t == 'cards:card_pack_creator_recipe_type' or t.endswith('card_packs'):
                return Recipe(rid, t, [g for g in (I(x) for x in j.get('ingredients', [])) if g],
                              res(j.get('output')), origin=origin)
        except Exception as e:
            log('  ! could not read recipe', rid, t, e)
            return None
        return None  # special / unsupported type

    def load_recipes(self, ct_removals, ct_recipes):
        pat = re.compile(r'data/([^/]+)/recipes/(.+)\.json$')
        for rel in self.pool.list('data/', '.json'):
            m = pat.match(rel)
            if not m:
                continue
            j = self.pool.json(rel)
            r = self.norm(f'{m.group(1)}:{m.group(2)}', j, self.pool.source_of(rel))
            if r and r.outputs:
                self.recipes.append(r)
        # CraftTweaker removals: craftingTable.remove(<item>) drops every crafting-table recipe
        # (shaped/shapeless) that outputs the item; furnace.remove the smelting ones.
        crafting = {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'}
        mgr_types = {'craftingTable': crafting, 'furnace': {'minecraft:smelting'},
                     'blastFurnace': {'minecraft:blasting'}, 'smoker': {'minecraft:smoking'}}
        keep = []
        for r in self.recipes:
            hit = None
            for mgr, item, script in ct_removals:
                if r.type in mgr_types.get(mgr, set()) and item in r.output_items():
                    hit = script
                    break
            if hit:
                self.ct_removed.append((r, hit))
            else:
                keep.append(r)
        self.recipes = keep
        for j in ct_recipes:
            r = self.norm(j['_id'], j, 'CraftTweaker ' + j['_ct'])
            if r:
                self.recipes.append(r)
        for r in self.recipes:
            for o in r.outputs:
                k = o.fluid or (o.items[0] if o.items else None)
                if k:
                    self.by_output[k].append(r)
            for g in r.inputs + [s for st in (r.steps or []) for s in st.inputs]:
                for it in (g.items if not g.fluid else [g.fluid]):
                    self.by_input[it].append(r)


# =====================================================================================
# 4. Building the pool from the instance / repo / vanilla paths
# =====================================================================================

def build_pool(args, cleanup):
    sources = []
    for v in args.vanilla:
        if os.path.exists(v):
            sources.append(Source('vanilla:' + os.path.basename(v.rstrip('/\\')), v))
        else:
            log('  ! vanilla path missing', v)
    mods_dir = os.path.join(args.instance, 'mods')
    jars = sorted(glob.glob(os.path.join(mods_dir, '*.jar')), key=lambda p: os.path.basename(p).lower())
    loaded = {'minecraft', 'forge'}
    qc_jar = None
    for j in jars:
        try:
            s = Source('jar:' + os.path.basename(j), j)
        except zipfile.BadZipFile:
            log('  ! not a zip', j)
            continue
        loaded.update(s.mod_ids())
        if os.path.basename(j).lower().startswith('quicreate-'):
            qc_jar = s
            continue
        sources.append(s)
    repo_res = os.path.join(args.repo, 'src', 'main', 'resources') if args.repo else None
    removed = set(cleanup['data'])
    if qc_jar and (args.quicreate_jar_fallback or not (repo_res and os.path.isdir(repo_res))):
        qc_jar.skip = removed
        for r in list(qc_jar.files):
            if r in removed:
                del qc_jar.files[r]
        sources.append(qc_jar)
    if repo_res and os.path.isdir(repo_res):
        rs = Source('quicreate-src', repo_res, skip=removed)
        sources.append(rs)
    loaded.update(args.extra_mods or [])
    return Pool(sources), loaded, [os.path.basename(j) for j in jars]


# =====================================================================================
# 5. Loot tables
# =====================================================================================

def _num(v, default=1.0):
    """(min, max, mean) of a number provider."""
    if v is None:
        return default, default, default
    if isinstance(v, (int, float)):
        return v, v, v
    if isinstance(v, dict):
        t = v.get('type', 'minecraft:uniform' if 'min' in v else 'minecraft:constant')
        if t.endswith('constant'):
            x = v.get('value', default)
            return x, x, x
        if t.endswith('uniform'):
            lo, hi = v.get('min', 0), v.get('max', 0)
            lo = _num(lo)[0] if isinstance(lo, dict) else lo
            hi = _num(hi)[1] if isinstance(hi, dict) else hi
            return lo, hi, (lo + hi) / 2
        if t.endswith('binomial'):
            n, p = v.get('n', 1), v.get('p', 0.5)
            n = _num(n)[2] if isinstance(n, dict) else n
            return 0, n, n * p
    return default, default, default


class Loot:
    def __init__(self, world: World):
        self.w = world

    def table(self, tid):
        ns, path = split_rl(tid)
        return self.w.pool.json(f'data/{ns}/loot_tables/{path}.json') if self.w.pool.has(
            f'data/{ns}/loot_tables/{path}.json') else None

    def summary(self, tid, depth=0, silk=False):
        """List of drops: {'item', 'min', 'max', 'chance', 'notes'} merged per item."""
        j = self.table(tid)
        if not j or depth > 4:
            return []
        out = collections.OrderedDict()
        for pool in j.get('pools', []):
            rmin, rmax, ravg = _num(pool.get('rolls', 1))
            ravg += _num(pool.get('bonus_rolls', 0))[2] * 0
            pchance, pnotes = self._conds(pool.get('conditions', []))
            if pchance is None:
                continue
            leaves = []
            for e in pool.get('entries', []):
                self._entry(e, 1.0, [], leaves, depth, silk)
            total = sum(l[1] for l in leaves) or 1
            for item, weight, cchance, notes, cmin, cmax in leaves:
                p_roll = weight / total * cchance
                p_any = 1 - (1 - p_roll) ** max(ravg, 0) if p_roll < 1 else 1.0
                p_any *= pchance
                k = item
                d = out.setdefault(k, {'item': item, 'min': 0, 'max': 0, 'chance': 0.0, 'notes': set()})
                d['min'] += cmin * rmin if (p_roll >= 0.999 and pchance >= 0.999) else 0
                d['max'] += cmax * max(rmax, 1)
                d['chance'] = 1 - (1 - d['chance']) * (1 - p_any)
                d['notes'].update(notes + pnotes)
        return list(out.values())

    def _conds(self, conds):
        chance, notes = 1.0, []
        for c in conds or []:
            t = c.get('condition', '')
            if t.endswith('random_chance'):
                chance *= c.get('chance', 1)
            elif t.endswith('random_chance_with_looting'):
                chance *= c.get('chance', 1)
                notes.append('looting')
            elif t.endswith('killed_by_player'):
                notes.append('player kill')
            elif t.endswith('match_tool'):
                pred = json.dumps(c.get('predicate', {}))
                if 'silk_touch' in pred:
                    return None, notes  # silk touch only branch: skip for normal drops
                if 'shears' in pred:
                    notes.append('shears')
            elif t.endswith('inverted'):
                inner = json.dumps(c.get('term', {}))
                if 'silk_touch' in inner:
                    continue
            elif t.endswith('survives_explosion'):
                continue
            elif t.endswith('table_bonus'):
                ch = c.get('chances', [1])
                chance *= ch[0] if ch else 1
                notes.append('fortune')
        return chance, notes

    def _entry(self, e, mult, notes, leaves, depth, silk):
        t = e.get('type', 'minecraft:item')
        cchance, cnotes = self._conds(e.get('conditions', []))
        if cchance is None:
            return False
        notes = notes + cnotes
        weight = e.get('weight', 1)
        if t.endswith('alternatives'):
            for ch in e.get('children', []):
                if self._entry(ch, mult * cchance, notes, leaves, depth, silk):
                    break   # first child that can apply wins
            return True
        if t.endswith('group') or t.endswith('sequence'):
            for ch in e.get('children', []):
                self._entry(ch, mult * cchance, notes, leaves, depth, silk)
            return True
        if t.endswith('loot_table'):
            name = e.get('name') or e.get('value')
            if isinstance(name, str):
                for d in self.summary(name, depth + 1):
                    leaves.append((d['item'], weight * d['chance'], mult * cchance, notes + sorted(d['notes']),
                                   d['min'], d['max']))
            return True
        if t.endswith('empty'):
            leaves.append((None, weight, 1.0, notes, 0, 0))
            return True
        cmin, cmax, n2 = 1, 1, list(notes)
        for f in e.get('functions', []):
            fn = f.get('function', '')
            if fn.endswith('set_count'):
                a, b, _ = _num(f.get('count'))
                if f.get('add'):
                    cmin, cmax = cmin + a, cmax + b
                else:
                    cmin, cmax = a, b
            elif fn.endswith('looting_enchant'):
                n2.append('looting')
            elif fn.endswith('apply_bonus'):
                n2.append('fortune')
            elif fn.endswith('set_enchantments') or fn.endswith('enchant_randomly') or fn.endswith('enchant_with_levels'):
                n2.append('enchanted')
            elif fn.endswith('set_potion'):
                n2.append(f.get('id', 'potion'))
        if t.endswith('tag'):
            items = self.w.tag_items(e.get('name', ''))
            for it in items:
                leaves.append((it, weight / max(len(items), 1), mult * cchance, n2, cmin, cmax))
            return True
        if t.endswith('item'):
            leaves.append((rl(e.get('name', 'minecraft:air')), weight, mult * cchance, n2, cmin, cmax))
            return True
        return True

    def drops_of_entity(self, eid):
        ns, path = split_rl(eid)
        return [d for d in self.summary(f'{ns}:entities/{path}') if d['item']]

    def drops_of_block(self, bid):
        ns, path = split_rl(bid)
        return [d for d in self.summary(f'{ns}:blocks/{path}') if d['item']]


# =====================================================================================
# 6. Worldgen: what is on each planet
# =====================================================================================

class Worldgen:
    def __init__(self, world: World, loot: Loot):
        self.w = world
        self.loot = loot
        self.pool = world.pool
        self._structures = None
        self._modifiers = None

    def j(self, kind, ident):
        ns, path = split_rl(ident)
        rel = f'data/{ns}/{kind}/{path}.json'
        return self.pool.json(rel) if self.pool.has(rel) else None

    def biome_matches(self, spec, biome):
        """spec: '#tag', 'id', or list."""
        if spec is None:
            return False
        if isinstance(spec, list):
            return any(self.biome_matches(s, biome) for s in spec)
        if isinstance(spec, dict):   # forge 'any'/'tag' holder sets
            if spec.get('type') == 'forge:any':
                return True
            return self.biome_matches(spec.get('biomes') or spec.get('tag'), biome)
        if spec.startswith('#'):
            return biome in self.w.biome_tags.get(rl(spec[1:]), [])
        return rl(spec) == biome

    def dimension_biomes(self, dim):
        d = self.j('dimension', dim)
        if not d:
            return []
        src = d.get('generator', {}).get('biome_source', {})
        if 'biomes' in src and isinstance(src['biomes'], list):
            return [b['biome'] if isinstance(b, dict) else b for b in src['biomes']]
        if 'biome' in src:
            return [src['biome']]
        return []

    def dimension_settings(self, dim):
        d = self.j('dimension', dim) or {}
        s = d.get('generator', {}).get('settings')
        return self.j('worldgen/noise_settings', s) if isinstance(s, str) else (s or {})

    def modifiers(self):
        if self._modifiers is None:
            self._modifiers = []
            for rel in self.pool.list('data/', '.json'):
                if '/forge/biome_modifier/' in rel:
                    m = self.pool.json(rel)
                    if isinstance(m, dict):
                        self._modifiers.append((rel, m))
        return self._modifiers

    def structures(self):
        if self._structures is None:
            in_set = set()
            for rel in self.pool.list('data/', '.json'):
                if '/worldgen/structure_set/' in rel:
                    s = self.pool.json(rel) or {}
                    for e in s.get('structures', []):
                        in_set.add(rl(e.get('structure', '')))
            self._structures = {}
            for rel in self.pool.list('data/', '.json'):
                m = re.match(r'data/([^/]+)/worldgen/structure/(.+)\.json$', rel)
                if m:
                    sid = f'{m.group(1)}:{m.group(2)}'
                    self._structures[sid] = (self.pool.json(rel) or {}, sid in in_set)
        return self._structures

    def feature_info(self, placed_id):
        """Return dict(kind='ore'|'feature', blocks=[...], size, count, heights)."""
        pf = self.j('worldgen/placed_feature', placed_id) if isinstance(placed_id, str) else placed_id
        if not pf:
            return None
        cf = pf.get('feature')
        cfj = self.j('worldgen/configured_feature', cf) if isinstance(cf, str) else cf
        if not cfj:
            return None
        info = {'id': placed_id if isinstance(placed_id, str) else '?', 'type': cfj.get('type'),
                'blocks': [], 'size': None, 'count': None, 'height': None, 'rarity': None}
        cfg = cfj.get('config', {})
        if cfj.get('type') in ('minecraft:ore', 'minecraft:scattered_ore'):
            info['kind'] = 'ore'
            for t in cfg.get('targets', []):
                n = t.get('state', {}).get('Name')
                if n and n not in info['blocks']:
                    info['blocks'].append(n)
            info['size'] = cfg.get('size')
        else:
            info['kind'] = 'feature'
            seen = []

            def walk(x):
                if isinstance(x, dict):
                    n = x.get('Name')
                    if isinstance(n, str) and n not in seen and not n.endswith(':air') and not n.endswith('cave_air'):
                        seen.append(n)
                    for v in x.values():
                        walk(v)
                elif isinstance(x, list):
                    for v in x:
                        walk(v)
            walk(cfg)
            info['blocks'] = seen
        for p in pf.get('placement', []):
            t = p.get('type', '')
            if t.endswith(':count'):
                info['count'] = _num(p.get('count'))[2]
            elif t.endswith('rarity_filter'):
                info['rarity'] = p.get('chance')
            elif t.endswith('height_range'):
                h = p.get('height', {})
                lo = h.get('min_inclusive', {})
                hi = h.get('max_inclusive', {})

                def anchor(a):
                    if 'absolute' in a:
                        return str(a['absolute'])
                    if 'above_bottom' in a:
                        return f'bottom+{a["above_bottom"]}'
                    if 'below_top' in a:
                        return f'top-{a["below_top"]}'
                    return '?'
                info['height'] = f'{anchor(lo)} to {anchor(hi)}'
        return info

    def planet(self, dim):
        biomes = self.dimension_biomes(dim)
        res = {'dim': dim, 'biomes': biomes, 'ores': collections.OrderedDict(), 'features': collections.OrderedDict(),
               'mobs': collections.OrderedDict(), 'structures': [], 'terrain': []}
        for b in biomes:
            bj = self.j('worldgen/biome', b) or {}
            feats = [f for step in bj.get('features', []) for f in step]
            for rel, m in self.modifiers():
                t = m.get('type', '')
                if t == 'forge:add_features' and self.biome_matches(m.get('biomes'), b):
                    f = m.get('features')
                    feats += f if isinstance(f, list) else [f]
                if t == 'forge:add_spawns' and self.biome_matches(m.get('biomes'), b):
                    sp = m.get('spawners')
                    for s in (sp if isinstance(sp, list) else [sp]):
                        bj.setdefault('spawners', {}).setdefault('monster', []).append(s)
            for f in feats:
                if not isinstance(f, str):
                    continue
                fi = self.feature_info(f)
                if not fi:
                    continue
                bucket = res['ores'] if fi['kind'] == 'ore' else res['features']
                e = bucket.setdefault(f, dict(fi, biomes=[]))
                e['biomes'].append(b)
            for cat, lst in (bj.get('spawners') or {}).items():
                for s in lst or []:
                    if not isinstance(s, dict):
                        continue
                    e = res['mobs'].setdefault(s['type'], {'type': s['type'], 'cats': set(), 'biomes': [],
                                                            'weight': 0})
                    e['cats'].add(cat)
                    e['biomes'].append(b)
                    e['weight'] = max(e['weight'], s.get('weight', 0))
        for sid, (sj, placed) in sorted(self.structures().items()):
            spec = sj.get('biomes')
            hit = [b for b in biomes if self.biome_matches(spec, b)]
            if hit and placed:
                spawns = []
                for cat, ov in (sj.get('spawn_overrides') or {}).items():
                    for s in ov.get('spawns', []):
                        spawns.append(s.get('type'))
                if isinstance(sj.get('structure'), dict):
                    for cat, ov in (sj['structure'].get('spawn_overrides') or {}).items():
                        for s in ov.get('spawns', []):
                            if s.get('type') not in spawns:
                                spawns.append(s.get('type'))
                res['structures'].append({'id': sid, 'biomes': hit, 'spawns': spawns})
        ns = self.dimension_settings(dim)
        blocks = []

        def walk(x):
            if isinstance(x, dict):
                for k in ('default_block', 'result_state'):
                    if isinstance(x.get(k), dict) and x[k].get('Name') and x[k]['Name'] not in blocks:
                        blocks.append(x[k]['Name'])
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(ns)
        res['terrain'] = [b for b in blocks if not b.endswith(':air') and b != 'minecraft:bedrock']
        fl = (ns.get('default_fluid') or {}).get('Name')
        res['fluid'] = fl
        return res


# =====================================================================================
# 7. Icons: real textures, flat items and a small isometric block renderer
# =====================================================================================

ICON_PX = 64          # saved icon size (nearest-neighbour)
BLOCK_RENDER = 8      # pixels per model unit when drawing blocks (16 units -> 128 px)


class Icons:
    def __init__(self, world: World, out_dir, overrides=None):
        self.w = world
        self.pool = world.pool
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.cache = {}
        self.missing = {}
        self.overrides = overrides or {}

    # ------------------------------------------------------------ helpers
    def texture(self, ref):
        """Load a texture by resource reference ('ns:block/x'), first animation frame only."""
        if not ref or ref.startswith('#'):
            return None
        ns, path = split_rl(ref)
        rel = f'assets/{ns}/textures/{path}.png'
        if not self.pool.has(rel):
            return None
        try:
            im = Image.open(io.BytesIO(self.pool.read(rel))).convert('RGBA')
        except Exception:
            return None
        w, h = im.size
        if h > w and h % w == 0:           # animated strip: keep the first frame
            im = im.crop((0, 0, w, w))
        return im

    def model(self, ref, depth=0):
        """Resolve a model with its parents: returns (textures, elements, chain)."""
        if depth > 20 or not ref:
            return {}, None, []
        ns, path = split_rl(ref)
        if path.startswith('builtin/'):
            return {}, None, [path]
        rel = f'assets/{ns}/models/{path}.json'
        if not self.pool.has(rel):
            return {}, None, [f'missing:{ns}:{path}']
        j = self.pool.json(rel) or {}
        tex, elems, chain = {}, None, []
        if 'parent' in j:
            tex, elems, chain = self.model(j['parent'], depth + 1)
        tex = dict(tex)
        tex.update(j.get('textures', {}))
        if 'elements' in j:
            elems = j['elements']
        if j.get('loader') and not elems:
            chain = chain + ['loader:' + j['loader']]
        return tex, elems, [f'{ns}:{path}'] + chain

    def obj_model(self, ref, depth=0):
        """Find a forge:obj model in the parent chain: (obj path, flip_v)."""
        if depth > 20 or not ref:
            return None
        ns, path = split_rl(ref)
        rel = f'assets/{ns}/models/{path}.json'
        if not self.pool.has(rel):
            return None
        j = self.pool.json(rel) or {}
        if j.get('loader') == 'forge:obj' and j.get('model'):
            return j['model'], j.get('flip_v', False)
        return self.obj_model(j.get('parent'), depth + 1) if j.get('parent') else None

    @staticmethod
    def resolve(tex, key, depth=0):
        v = tex.get(key.lstrip('#'))
        while isinstance(v, str) and v.startswith('#') and depth < 10:
            v = tex.get(v[1:])
            depth += 1
        return v

    # ------------------------------------------------------------ rendering
    def flat(self, tex):
        layers = []
        for i in range(8):
            t = self.texture(self.resolve(tex, f'layer{i}'))
            if t is None:
                if i == 0:
                    return None
                break
            layers.append(t)
        base = layers[0]
        size = max(l.size[0] for l in layers)
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        for l in layers:
            if l.size[0] != size:
                l = l.resize((size, size), Image.NEAREST)
            canvas.alpha_composite(l)
        return canvas

    @staticmethod
    def _proj(x, y, z):
        c30 = math.cos(math.radians(30))
        return ((x + z) * c30 * BLOCK_RENDER, ((x - z) * 0.5 - y) * BLOCK_RENDER)

    @staticmethod
    def _shaded(img, shade):
        if shade >= 0.999:
            return img
        r, g, b, a = img.split()
        lut = [int(v * shade) for v in range(256)]
        return Image.merge('RGBA', (r.point(lut), g.point(lut), b.point(lut), a))

    def _draw(self, polys):
        """polys: (depth, [3D points of the polygon], [uv in texture px for points 0, 1 and the last], img, shade)."""
        if not polys:
            return None
        pts = [self._proj(*p) for _, P, _, _, _ in polys for p in P]
        minx, miny = min(p[0] for p in pts), min(p[1] for p in pts)
        maxx, maxy = max(p[0] for p in pts), max(p[1] for p in pts)
        W, H = int(maxx - minx) + 3, int(maxy - miny) + 3
        if W > 4000 or H > 4000:
            return None
        canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        shaded = {}
        for _d, P, T, img, shade in sorted(polys, key=lambda p: p[0]):
            S = [(x - minx + 1, y - miny + 1) for x, y in (self._proj(*p) for p in P)]
            S0, S1, S2 = S[0], S[1], S[-1]
            ax, ay = S1[0] - S0[0], S1[1] - S0[1]
            bx, by = S2[0] - S0[0], S2[1] - S0[1]
            det = ax * by - ay * bx
            if abs(det) < 1e-6:
                continue
            du1, dv1 = T[1][0] - T[0][0], T[1][1] - T[0][1]
            du2, dv2 = T[2][0] - T[0][0], T[2][1] - T[0][1]
            ia, ib, ic, id_ = by / det, -bx / det, -ay / det, ax / det
            a = du1 * ia + du2 * ic
            b = du1 * ib + du2 * id_
            c = T[0][0] - a * S0[0] - b * S0[1]
            dd = dv1 * ia + dv2 * ic
            e = dv1 * ib + dv2 * id_
            f_ = T[0][1] - dd * S0[0] - e * S0[1]
            key = (id(img), round(shade, 2))
            if key not in shaded:
                shaded[key] = self._shaded(img, shade)
            # clamp sampling to the texture: build a slightly padded source
            warped = shaded[key].transform(canvas.size, Image.AFFINE, (a, b, c, dd, e, f_), resample=Image.NEAREST)
            mask = Image.new('L', canvas.size, 0)
            ImageDraw.Draw(mask).polygon(S, fill=255)
            amask = Image.composite(warped.split()[3], Image.new('L', canvas.size, 0), mask)
            warped.putalpha(amask)
            canvas.alpha_composite(warped)
        bbox = canvas.getbbox()
        if not bbox:
            return None
        canvas = canvas.crop(bbox)
        side = max(canvas.size)
        sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        sq.paste(canvas, ((side - canvas.size[0]) // 2, (side - canvas.size[1]) // 2))
        return sq

    def iso(self, tex, elems):
        polys = []
        for el in elems:
            f, t = el.get('from', [0, 0, 0]), el.get('to', [16, 16, 16])
            x1, y1, z1 = f
            x2, y2, z2 = t
            depth = (x1 + x2) / 2 - (z1 + z2) / 2 + (y1 + y2) / 2
            for name in ('up', 'north', 'east'):
                fd = (el.get('faces') or {}).get(name)
                if not fd:
                    continue
                img = self.texture(self.resolve(tex, fd.get('texture', '')))
                if img is None:
                    continue
                uv = fd.get('uv')
                if name == 'up':
                    uv = uv or [x1, z1, x2, z2]
                    P = [(x1, y2, z1), (x2, y2, z1), (x1, y2, z2), (x2, y2, z2)]
                    shade, d = 1.0, depth + 0.01
                elif name == 'north':
                    uv = uv or [16 - x2, 16 - y2, 16 - x1, 16 - y1]
                    P = [(x2, y2, z1), (x1, y2, z1), (x2, y1, z1), (x1, y1, z1)]
                    shade, d = 0.8, depth
                else:
                    uv = uv or [16 - z2, 16 - y2, 16 - z1, 16 - y1]
                    P = [(x2, y2, z2), (x2, y2, z1), (x2, y1, z2), (x2, y1, z1)]
                    shade, d = 0.6, depth
                u1, v1, u2, v2 = uv
                quad = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
                k = ((fd.get('rotation', 0) or 0) // 90) % 4
                quad = quad[k:] + quad[:k]
                sx, sy = img.size[0] / 16.0, img.size[1] / 16.0
                T = [(quad[0][0] * sx, quad[0][1] * sy), (quad[1][0] * sx, quad[1][1] * sy),
                     (quad[3][0] * sx, quad[3][1] * sy)]
                poly = [P[0], P[1], P[3], P[2]]
                polys.append((d, poly, T, img, shade))
        return self._draw(polys)

    def iso_obj(self, model_ref, tex, flip_v=True):
        ns, path = split_rl(model_ref)
        rel = f'assets/{ns}/{path}'
        if not self.pool.has(rel):
            return None
        txt = self.pool.read(rel).decode('utf-8', 'replace')
        mtl_tex = {}
        m = re.search(r'(?m)^mtllib\s+(\S+)', txt)
        if m:
            mrel = rel.rsplit('/', 1)[0] + '/' + m.group(1)
            if self.pool.has(mrel):
                cur = None
                for line in self.pool.read(mrel).decode('utf-8', 'replace').splitlines():
                    p = line.split()
                    if p[:1] == ['newmtl']:
                        cur = p[1]
                    elif p[:1] == ['map_Kd'] and cur:
                        mtl_tex[cur] = p[1]
        V, VT, faces, cur = [], [], [], None
        for line in txt.splitlines():
            p = line.split()
            if not p:
                continue
            if p[0] == 'v':
                V.append(tuple(float(x) for x in p[1:4]))
            elif p[0] == 'vt':
                VT.append((float(p[1]), float(p[2])))
            elif p[0] == 'usemtl':
                cur = p[1]
            elif p[0] == 'f':
                idx = []
                for q in p[1:]:
                    a = q.split('/')
                    vi = int(a[0])
                    ti = int(a[1]) if len(a) > 1 and a[1] else None
                    idx.append((vi - 1 if vi > 0 else len(V) + vi, (ti - 1 if ti and ti > 0 else (len(VT) + ti if ti else None))))
                faces.append((cur, idx))
        if not V or not faces:
            return None
        xs, ys, zs = [v[0] for v in V], [v[1] for v in V], [v[2] for v in V]
        span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) or 1
        scale = 16.0 / span
        V = [((x - min(xs)) * scale, (y - min(ys)) * scale, (z - min(zs)) * scale) for x, y, z in V]
        polys = []
        for mat, idx in faces:
            ref = mtl_tex.get(mat, '#0')
            img = self.texture(self.resolve(tex, ref) if ref.startswith('#') else ref)
            if img is None or len(idx) < 3:
                continue
            tw, th = img.size
            for k in range(1, len(idx) - 1):
                tri = [idx[0], idx[k], idx[k + 1]]
                P = [V[i] for i, _ in tri]
                if any(t is None for _, t in tri):
                    continue
                T = []
                for _, ti in tri:
                    u, v = VT[ti]
                    if flip_v:
                        v = 1 - v
                    T.append((u * tw, v * th))
                # normal for culling / shading
                ux, uy, uz = (P[1][0] - P[0][0], P[1][1] - P[0][1], P[1][2] - P[0][2])
                vx, vy, vz = (P[2][0] - P[0][0], P[2][1] - P[0][1], P[2][2] - P[0][2])
                nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
                ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
                nx, ny, nz = nx / ln, ny / ln, nz / ln
                # viewer direction ~ (+x, +y, -z)
                if nx * 1 + ny * 1 + nz * -1 <= 0:
                    continue
                shade = 0.55 + 0.45 * max(ny, 0) + 0.25 * max(-nz, 0) * 0.8
                shade = min(shade, 1.0)
                d = sum(p[0] - p[2] + p[1] for p in P) / 3
                polys.append((d, P, T, img, shade))
        return self._draw(polys)

    def render(self, item):
        item = rl(item)
        ns, path = item.split(':', 1)
        if item in self.overrides:
            t = self.texture(self.overrides[item])
            if t is not None:
                return t, 'override'
        tex, elems, chain = self.model(f'{ns}:item/{path}')
        gen = any(c.endswith('item/generated') or c.endswith('builtin/generated') or c.endswith('item/handheld')
                  or 'handheld' in c for c in chain)
        if chain and chain[0].startswith('missing:'):
            # some mods put the item model under a different name: try the block model
            tex, elems, chain = self.model(f'{ns}:block/{path}')
        if 'layer0' in tex and (gen or not elems):
            im = self.flat(tex)
            if im is not None:
                return im, 'flat'
        if elems:
            im = self.iso(tex, elems)
            if im is not None:
                return im, 'block'
        objm = self.obj_model(f'{ns}:item/{path}')
        if objm:
            im = self.iso_obj(objm[0], tex, objm[1])
            if im is not None:
                return im, 'obj'
        # last resorts: a texture that is named after the item
        for cand in (f'{ns}:item/{path}', f'{ns}:block/{path}', self.resolve(tex, 'particle') or ''):
            t = self.texture(cand)
            if t is not None:
                return t, 'texture'
        return None, ' > '.join(chain[:4]) or 'no model'

    def get(self, item):
        """Return file name (relative to out_dir) of a crisp PNG, or None."""
        item = rl(item)
        if item in self.cache:
            return self.cache[item]
        try:
            im, how = self.render(item)
        except Exception as e:
            im, how = None, f'error {e}'
        if im is None:
            self.missing[item] = how
            self.cache[item] = None
            return None
        im = im.resize((ICON_PX, ICON_PX), Image.NEAREST) if im.size[0] <= ICON_PX else \
            im.resize((ICON_PX * 2, ICON_PX * 2), Image.NEAREST)
        fn = re.sub(r'[^a-z0-9_]', '_', item) + '.png'
        im.save(os.path.join(self.out_dir, fn))
        self.cache[item] = fn
        return fn


# =====================================================================================
# 8. Structures: which loot tables and mobs live in each structure (read from the .nbt)
# =====================================================================================

def _nbt_bytes(raw):
    import gzip
    try:
        return gzip.decompress(raw)
    except Exception:
        return raw


class StructureScan:
    def __init__(self, world: World):
        self.w = world
        self.pool = world.pool
        self.nbt_files = [r for r in self.pool.list('data/', '.nbt') if '/structures/' in r]
        self._strings = {}

    def strings(self, rel):
        if rel not in self._strings:
            b = _nbt_bytes(self.pool.read(rel))
            self._strings[rel] = set(m.decode() for m in re.findall(rb'[a-z0-9_.\-]+:[a-z0-9_/.\-]+', b))
        return self._strings[rel]

    def nbt_for_location(self, loc):
        ns, path = split_rl(loc)
        rel = f'data/{ns}/structures/{path}.nbt'
        return rel if self.pool.has(rel) else None

    def files_for(self, sid, sj):
        """All .nbt files that make up a structure."""
        files, seen_pools = set(), set()
        todo = []
        inner = sj.get('structure') if isinstance(sj.get('structure'), dict) else sj
        if inner.get('start_pool'):
            todo.append(rl(inner['start_pool']))
        while todo:
            p = todo.pop()
            if p in seen_pools or len(seen_pools) > 400:
                continue
            seen_pools.add(p)
            ns, path = split_rl(p)
            pj = self.pool.json(f'data/{ns}/worldgen/template_pool/{path}.json') if self.pool.has(
                f'data/{ns}/worldgen/template_pool/{path}.json') else None
            if not pj:
                continue
            for e in pj.get('elements', []):
                el = e.get('element', {})
                locs = [el.get('location')] + [x.get('location') for x in el.get('elements', []) if isinstance(x, dict)]
                for loc in locs:
                    if isinstance(loc, str):
                        rel = self.nbt_for_location(loc)
                        if rel and rel not in files:
                            files.add(rel)
                            for s in self.strings(rel):
                                n2, p2 = split_rl(s)
                                if self.pool.has(f'data/{n2}/worldgen/template_pool/{p2}.json'):
                                    todo.append(s)
        if not files:
            # custom (non-jigsaw) structures: their pieces are named after the structure type
            t = inner.get('type', sid)
            ns, path = split_rl(t if ':' in t and not t.startswith('minecraft:') else sid)
            if path in ('jigsaw', 'repositioned'):
                ns, path = split_rl(sid)
            prefix = f'data/{ns}/structures/{path}'
            files = {r for r in self.nbt_files if r.startswith(prefix)}
        return sorted(files)

    def contents(self, sid, sj):
        files = self.files_for(sid, sj)
        loot, mobs = set(), set()
        for rel in files:
            for s in self.strings(rel):
                ns, path = split_rl(s.lstrip('0123456789'))
                if '/chests/' in f'/{path}' or path.startswith('chests/'):
                    if self.pool.has(f'data/{ns}/loot_tables/{path}.json'):
                        loot.add(f'{ns}:{path}')
                elif f'entity.{ns}.{path}' in self.w.lang and not path.startswith('chests'):
                    mobs.add(f'{ns}:{path}')
        return {'files': files, 'loot': sorted(loot), 'mobs': sorted(mobs)}


# =====================================================================================
# 9. Quests
# =====================================================================================

class Quest:
    def __init__(self, qid, group, j):
        self.id = qid
        self.group = group
        d = j.get('display', {})

        def txt(x):
            if isinstance(x, dict):
                return x.get('text') or x.get('translate') or ''
            return x or ''
        self.title = txt(d.get('title')) or qid
        self.subtitle = txt(d.get('subtitle'))
        self.desc = [l for l in d.get('description', []) if isinstance(l, str)]
        while self.desc and not self.desc[-1].strip():
            self.desc.pop()
        while self.desc and not self.desc[0].strip():
            self.desc.pop(0)
        self.deps = j.get('dependencies', [])
        self.tasks = []
        for k in sorted(j.get('tasks', {})):
            self.tasks.append(j['tasks'][k])
        self.icon = d.get('icon', {}).get('item', {}).get('id')
        groups = d.get('groups', {})
        self.pos = (groups.get(group) or next(iter(groups.values()), {})).get('position', [0, 0])
        self.rewards = j.get('rewards', {})

    def items(self):
        return [t for t in self.tasks if t.get('type') == 'heracles:item']


def load_quests(heracles_dir):
    groups = [l.strip() for l in open(os.path.join(heracles_dir, 'groups.txt'), encoding='utf-8-sig') if l.strip()]
    quests = {}
    for path in sorted(glob.glob(os.path.join(heracles_dir, 'quests', '*', '*.json'))):
        folder = os.path.basename(os.path.dirname(path))
        j = json.load(open(path, encoding='utf-8-sig'))
        qid = os.path.basename(path)[:-5]
        g = next(iter(j.get('display', {}).get('groups', {}) or {folder: 0}))
        q = Quest(qid, g, j)
        q.folder = folder
        quests[qid] = q
    return groups, quests


# =====================================================================================
# 10. Knowledge: where every item comes from
# =====================================================================================

MACHINES = {
    # recipe type: (label, machine item)
    'minecraft:crafting_shaped': ('Crafting Table', 'minecraft:crafting_table'),
    'minecraft:crafting_shapeless': ('Crafting Table (shapeless)', 'minecraft:crafting_table'),
    'minecraft:smelting': ('Furnace', 'minecraft:furnace'),
    'minecraft:blasting': ('Blast Furnace', 'minecraft:blast_furnace'),
    'minecraft:smoking': ('Smoker', 'minecraft:smoker'),
    'minecraft:campfire_cooking': ('Campfire', 'minecraft:campfire'),
    'minecraft:stonecutting': ('Stonecutter', 'minecraft:stonecutter'),
    'minecraft:smithing_transform': ('Smithing Table', 'minecraft:smithing_table'),
    'create:milling': ('Millstone', 'create:millstone'),
    'create:crushing': ('Crushing Wheels', 'create:crushing_wheel'),
    'create:mixing': ('Mechanical Mixer + Basin', 'create:mechanical_mixer'),
    'create:compacting': ('Mechanical Press + Basin (compacting)', 'create:mechanical_press'),
    'create:pressing': ('Mechanical Press', 'create:mechanical_press'),
    'create:deploying': ('Deployer', 'create:deployer'),
    'create:item_application': ('Use item on block (hand or Deployer)', 'create:deployer'),
    'create:filling': ('Spout', 'create:spout'),
    'create:emptying': ('Item Drain', 'create:item_drain'),
    'create:splashing': ('Encased Fan + Water (washing)', 'create:encased_fan'),
    'create:haunting': ('Encased Fan + Soul Fire (haunting)', 'create:encased_fan'),
    'create:cutting': ('Mechanical Saw', 'create:mechanical_saw'),
    'create:sandpaper_polishing': ('Sand Paper (hold and use)', 'create:sand_paper'),
    'create:mechanical_crafting': ('Mechanical Crafters', 'create:mechanical_crafter'),
    'create:sequenced_assembly': ('Sequenced Assembly', 'create:deployer'),
    'createutilities:mixing': ('Mechanical Mixer + Basin', 'create:mechanical_mixer'),
    'createutilities:pressing': ('Mechanical Press', 'create:mechanical_press'),
    'createsifter:sifting': ('Sifter', 'createsifter:sifter'),
    'create_new_age:energising': ('Energiser', 'create_new_age:basic_energiser'),
    'create_mechanical_extruder:extruding': ('Mechanical Extruder', 'create_mechanical_extruder:mechanical_extruder'),
    'ad_astra:alloying': ('Etrionic Blast Furnace (alloying)', 'ad_astra:etrionic_blast_furnace'),
    'ad_astra:compressing': ('Compressor', 'ad_astra:compressor'),
    'ad_astra:nasa_workbench': ('NASA Workbench', 'ad_astra:nasa_workbench'),
    'ad_astra:cryo_freezing': ('Cryo Freezer', 'ad_astra:cryo_freezer'),
    'ad_astra:refining': ('Fuel Refinery', 'ad_astra:fuel_refinery'),
    'ad_astra:oxygen_loading': ('Oxygen Loader', 'ad_astra:oxygen_loader'),
    'cataclysm:weapon_fusion': ('Mechanical Fusion Anvil', 'cataclysm:mechanical_fusion_anvil'),
    'cards:pack_contents': ('Open the card pack', None),
}

TYPE_RANK = {
    'createsifter:sifting': 0, 'create_mechanical_extruder:extruding': 0,
    'minecraft:crafting_shaped': 1, 'minecraft:crafting_shapeless': 1, 'create:mechanical_crafting': 1,
    'create:mixing': 1, 'create:compacting': 1, 'create:pressing': 1, 'create:deploying': 1,
    'create:sequenced_assembly': 1, 'create_new_age:energising': 1, 'create:item_application': 1,
    'create:milling': 1, 'create:cutting': 1, 'ad_astra:nasa_workbench': 1, 'cataclysm:weapon_fusion': 1,
    'create:filling': 2, 'create:emptying': 2, 'minecraft:smelting': 2, 'create:crushing': 2,
    'create:splashing': 2, 'ad_astra:alloying': 3, 'minecraft:blasting': 3, 'create:haunting': 3,
    'ad_astra:compressing': 3, 'ad_astra:refining': 1, 'ad_astra:oxygen_loading': 1, 'ad_astra:cryo_freezing': 1,
    'minecraft:smithing_transform': 1, 'cards:pack_contents': 4, 'minecraft:stonecutting': 5,
    'minecraft:smoking': 6, 'minecraft:campfire_cooking': 6,
}


def fmt_pct(p):
    """0.0025 -> '0.25%', 1 -> '100%'."""
    if p is None:
        return ''
    if p >= 0.9995:
        return '100%'
    v = p * 100
    if v >= 1:
        s = f'{v:.1f}'
    elif v >= 0.1:
        s = f'{v:.2f}'
    else:
        s = f'{v:.3f}'
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s + '%'


class Knowledge:
    def __init__(self, world, loot, wg, scan, cfg, args):
        self.w, self.loot, self.wg, self.scan, self.cfg, self.args = world, loot, wg, scan, cfg, args
        self.natural = collections.defaultdict(list)   # item -> list of source dicts
        self.planets = {}                               # key -> planet data
        self.structures = {}                            # sid -> {'planet', 'loot', 'mobs', ...}
        self.mob_places = collections.defaultdict(set)  # mob -> planet keys
        self.island = {}
        self.fishing = None
        self.kelpy = {}

    # -------------------------------------------------------------- collect
    def add(self, item, kind, text, score, **kw):
        if not item:
            return
        d = {'kind': kind, 'text': text, 'score': score}
        d.update(kw)
        for x in self.natural[item]:
            if x['kind'] == kind and x['text'] == text:
                return
        self.natural[item].append(d)

    def planet_name(self, key):
        return self.cfg.get('planets', {}).get(key, {}).get('name', key)

    def build(self, quests=None):
        self._island()
        self._planets()
        # a boss lives on the planet of the structure its quest depends on
        for b in self.cfg.get('bosses', []):
            q = (quests or {}).get(b.get('quest'))
            for d in (q.deps if q else []):
                dq = quests.get(d)
                for t in (dq.tasks if dq else []):
                    sid = t.get('structures')
                    if t.get('type') == 'heracles:structure' and sid and rl(sid) in self.structures:
                        b['planet'] = self.structures[rl(sid)]['planet']
                        b['structure'] = rl(sid)
        self._fishing()
        self._bosses()
        self._all_mob_drops()
        return self

    def _all_mob_drops(self):
        """Any entity loot table, for mobs whose spawn place is not in the data (spawned by code, eggs, etc.)."""
        placed = set(self.mob_places) | {b['entity'] for b in self.cfg.get('bosses', [])}
        for rel in self.w.pool.list('data/', '.json'):
            m = re.match(r'data/([^/]+)/loot_tables/entities/([^/]+)\.json$', rel)
            if not m:
                continue
            eid = f'{m.group(1)}:{m.group(2)}'
            if eid in placed or f'entity.{m.group(1)}.{m.group(2)}' not in self.w.lang:
                continue
            for d in self.loot.drops_of_entity(eid):
                self.add(d['item'], 'mob', f'{self.w.name(eid)} drops it ({fmt_pct(d["chance"])} per kill; '
                         f'where it spawns is not in the data files)', 40, mob=eid)

    def _island(self):
        inst = self.args.instance
        for key, fn, label in (('island', 'default.nbt', 'Starting island'), ('nether_island', 'nether.nbt', 'Nether island')):
            path = os.path.join(inst, 'config', 'easy_skyblock_island', 'islands', fn)
            if not os.path.exists(path):
                continue
            try:
                import nbtlib
                n = nbtlib.load(path)
                pal = n['palette']
                cnt = collections.Counter(str(pal[int(b['state'])]['Name']) for b in n['blocks'])
                chest = collections.Counter()
                for b in n['blocks']:
                    if 'nbt' in b and 'Items' in b['nbt']:
                        for it in b['nbt']['Items']:
                            chest[str(it['id'])] += int(it.get('Count', 1))
            except Exception as e:
                log('  ! could not read island', path, e)
                continue
            cnt.pop('easy_skyblock_island:spawn_marker', None)
            self.island[key] = {'label': label, 'blocks': dict(cnt), 'chest': dict(chest), 'file': fn}
            for b, c in cnt.items():
                drops = self.loot.drops_of_block(b) or [{'item': b}]
                for d in drops:
                    self.add(d['item'], 'island', f'{label}: {c}× {self.w.name(b)}' +
                             ('' if d['item'] == b else f' (drops {self.w.name(d["item"])})'), 0 if key == 'island' else 3)
            for it, c in chest.items():
                self.add(it, 'island', f'{label}: {c}× in the starting chest', 0)

    def _planets(self):
        for key, p in (self.cfg.get('planets') or {}).items():
            dim = p.get('dimension')
            if not dim:
                continue
            data = self.wg.planet(dim)
            data['biomes'] = list(dict.fromkeys(data['biomes']))
            self.planets[key] = data
            name = p.get('name', key)
            tier = p.get('tier', 5)
            for b in data['terrain']:
                for d in (self.loot.drops_of_block(b) or [{'item': b}]):
                    self.add(d['item'], 'terrain', f'{name}: mine the {self.w.name(b)} terrain', 10 + tier, planet=key)
            for fid, o in data['ores'].items():
                for b in o['blocks']:
                    where = f'Y {o["height"]}' if o.get('height') else ''
                    for d in (self.loot.drops_of_block(b) or [{'item': b}]):
                        extra = '' if d['item'] == b else f' → {self.w.name(d["item"])}'
                        self.add(d['item'], 'ore', f'{name}: {self.w.name(b)}{extra}' + (f' ({where})' if where else ''),
                                 10 + tier, planet=key)
            for fid, o in data['features'].items():
                for b in o['blocks']:
                    if b.startswith('minecraft:') and b.split(':')[1] in ('lava', 'water', 'snow_block', 'netherrack',
                                                                            'basalt', 'blackstone'):
                        continue
                    for d in (self.loot.drops_of_block(b) or [{'item': b}]):
                        self.add(d['item'], 'feature', f'{name}: found in world features ({self.w.name(b)})',
                                 11 + tier, planet=key)
            for mob, m in data['mobs'].items():
                self.mob_places[mob].add(key)
                for d in self.loot.drops_of_entity(mob):
                    self.add(d['item'], 'mob', f'{self.w.name(mob)} ({name}) drops it, {fmt_pct(d["chance"])} per kill',
                             12 + tier, planet=key, mob=mob)
            for s in data['structures']:
                sid = s['id']
                sj = self.wg.structures()[sid][0]
                cont = self.scan.contents(sid, sj)
                self.structures[sid] = dict(s, planet=key, **cont)
                mobs = set(s['spawns']) | set(cont['mobs'])
                for mob in mobs:
                    self.mob_places[mob].add(key)
                    for d in self.loot.drops_of_entity(mob):
                        self.add(d['item'], 'mob', f'{self.w.name(mob)} in the {self.w.name(sid)} ({name}), '
                                 f'{fmt_pct(d["chance"])} per kill', 13 + tier, planet=key, mob=mob)
                for lt in cont['loot']:
                    for d in self.loot.summary(lt):
                        if d['item']:
                            self.add(d['item'], 'chest', f'Chest loot in the {self.w.name(sid)} ({name}), '
                                     f'{fmt_pct(d["chance"])} per chest', 20 + tier, planet=key)

    def _fishing(self):
        rel = 'data/quicreate/loot_modifiers/fishing_kelpy_balls.json'
        if not self.w.pool.has(rel):
            return
        j = self.w.pool.json(rel)
        rods = {0: 'any vanilla rod'}
        reg = os.path.join(self.args.repo or '', 'src', 'main', 'java', 'IGoByJake', 'quicreate', 'ModRegistry.java')
        if os.path.exists(reg):
            for name, tier in re.findall(r'register\("(\w+_fishing_rod)".*?TieredFishingRodItem\((\d+)', open(reg).read()):
                rods[int(tier)] = self.w.name('quicreate:' + name)
        for k, v in (self.cfg.get('fishing_rods') or {}).items():
            rods.setdefault(int(k), v)
        tiers = []
        for i, t in enumerate(j.get('tiers', [])):
            tiers.append({'rod': rods.get(i, f'tier {i} rod'), 'tier': i, 't': t})
            # the modifier rolls extras, then heavy, medium, light in that order (KelpyFishingModifier)
            left = 1.0
            for ex in t.get('extras', []):
                self.add(ex['item'], 'fish', f'Fishing with the {rods.get(i)}: {fmt_pct(ex["chance"] * left)} per catch', 9)
                left *= 1 - ex['chance']
            for w in ('heavy', 'medium', 'light'):
                if t.get(f'{w}_item') and t.get(w):
                    self.kelpy.setdefault(t[f'{w}_item'], []).append((rods.get(i), t[w] * left))
                    left *= 1 - t[w]
        self.fishing = tiers
        for ball, lst in self.kelpy.items():
            best = max(lst, key=lambda x: x[1])
            self.add(ball, 'fish', f'Fishing: up to {fmt_pct(best[1])} per catch with the {best[0]}', 2)
            ns, path = split_rl(ball)
            table = {'light_kelpy_ball': 'quicreate:kelpy_ball_light', 'medium_kelpy_ball': 'quicreate:kelpy_ball_medium',
                     'heavy_kelpy_ball': 'quicreate:kelpy_ball_heavy'}.get(path)
            if table:
                for d in self.loot.summary(table):
                    if d['item']:
                        self.add(d['item'], 'kelpy', f'Open a {self.w.name(ball)} (fishing): {fmt_pct(d["chance"])} per ball',
                                 4, ball=ball)

    def _bosses(self):
        for b in self.cfg.get('bosses', []):
            eid = b['entity']
            for d in self.loot.drops_of_entity(eid):
                self.add(d['item'], 'boss', f'{self.w.name(eid)} boss drop ({self.planet_name(b.get("planet", ""))}), '
                         f'{fmt_pct(d["chance"])}', 14 + self.cfg.get('planets', {}).get(b.get('planet'), {}).get('tier', 5),
                         planet=b.get('planet'), mob=eid)

    # -------------------------------------------------------------- queries
    def producers(self, key):
        return self.w.by_output.get(key, [])

    def natural_sources(self, item):
        return sorted(self.natural.get(item, []), key=lambda d: d['score'])


# =====================================================================================
# 11. The guide: plan the chapters/steps and write HTML
# =====================================================================================

class Guide:
    def __init__(self, world, know, icons, groups, quests, cfg, args):
        self.w, self.k, self.icons = world, know, icons
        self.groups, self.quests, self.cfg, self.args = groups, quests, cfg, args
        self.steps = []                 # ordered Quest list
        self.step_no = {}               # quest id -> number
        self.item_steps = collections.defaultdict(list)  # item -> [step numbers that ask for it]
        self.chapters = []
        self.problems = []              # progression issues found while tracing
        self.no_source = {}             # item -> where it was needed
        self.used_icons = set()
        self.recipe_shown = 0
        self.audit = {}

    # ------------------------------------------------------------ planning
    def plan(self):
        ch_cfg = self.cfg.get('chapters', [])
        listed = [c['group'] for c in ch_cfg]
        for g in self.groups:
            if g not in listed:
                log('  ! quest group not in guide.yaml, appended:', g)
                ch_cfg.append({'group': g, 'title': g})
        for c in ch_cfg:
            if c['group'] not in self.groups:
                log('  ! guide.yaml chapter has no quest group:', c['group'])
        n = 0
        for c in ch_cfg:
            qs = [q for q in self.quests.values() if q.group == c['group']]
            ordered = self.order(qs, c.get('order') or [])
            hidden = set(c.get('hide') or [])
            ordered = [q for q in ordered if q.id not in hidden]
            for q in ordered:
                n += 1
                self.step_no[q.id] = n
                self.steps.append(q)
                for t in q.items():
                    it = t.get('item', '')
                    if not it.startswith('#'):
                        self.item_steps[rl(it)].append(n)
            self.chapters.append({'cfg': c, 'quests': ordered})
        # bosses from kill tasks
        bosses = []
        for ch in self.chapters:
            for q in ch['quests']:
                for t in q.tasks:
                    if t.get('type') == 'heracles:kill_entity':
                        eid = t.get('entity', {}).get('type')
                        if eid:
                            pl = (self.cfg.get('steps') or {}).get(q.id, {}) or {}
                            planet = pl.get('planet') or ch['cfg'].get('planet') or (ch['cfg'].get('planets') or [None])[0]
                            bosses.append({'entity': eid, 'planet': planet, 'quest': q.id})
        self.cfg['bosses'] = bosses
        return self

    def order(self, qs, explicit):
        ids = {q.id for q in qs}
        byid = {q.id: q for q in qs}
        for e in explicit:
            if e not in ids:
                log('  ! order lists unknown quest', e)
        first = [byid[e] for e in explicit if e in ids]
        rest = [q for q in qs if q.id not in explicit]
        # dependency-respecting order inside the chapter, ties broken by the quest-book layout (top to bottom)
        done, out = {q.id for q in first}, []
        remaining = sorted(rest, key=lambda q: (q.pos[1], q.pos[0]))
        while remaining:
            for q in remaining:
                local = [d for d in q.deps if d in ids] + [d for d in self.soft_deps(q, ids) if d not in done and d != q.id]
                if all(d in done for d in local):
                    out.append(q)
                    done.add(q.id)
                    remaining.remove(q)
                    break
            else:
                out.extend(remaining)
                break
        return first + out

    def soft_deps(self, q, ids):
        """Quests in the same chapter whose items the quest's main recipe needs (when the book has no arrow)."""
        if q.deps:
            return []
        if not hasattr(self, '_task_owner'):
            self._task_owner = {}
            for qq in self.quests.values():
                for t in qq.items():
                    self._task_owner.setdefault(rl(t.get('item', '#')) if not t.get('item', '').startswith('#') else '#', qq.id)
        out = []
        for t in q.items():
            it = t.get('item', '')
            if it.startswith('#'):
                continue
            rs = [r for r in self.w.by_output.get(rl(it), []) if r.type not in ('createsifter:sifting',)]
            rs.sort(key=lambda r: (0 if r.origin.startswith('CraftTweaker') else 1 if 'quicreate' in r.origin else 2,
                                   TYPE_RANK.get(r.type, 4)))
            for r in rs[:1]:
                for g in r.inputs:
                    for x in g.items[:3]:
                        o = self._task_owner.get(x)
                        if o and o in ids and o not in out:
                            out.append(o)
        return out

    # ------------------------------------------------------------ small html helpers
    def icon(self, item, cls='m', title=None):
        if not item:
            return '<span class="ic ic-%s ic-none"></span>' % cls
        fn = self.icons.get(item)
        t = esc(title or self.w.name(item))
        if fn:
            self.used_icons.add(item)
            return f'<img class="ic ic-{cls}" src="icons/{fn}" alt="{t}" title="{t}"/>'
        return f'<span class="ic ic-{cls} ic-none" title="{t}">{esc(self.w.name(item)[:2])}</span>'

    def fluid_icon_item(self, fluid):
        ns, path = split_rl(fluid)
        for cand in (f'{ns}:{path}_bucket', f'{ns}:{path.replace("flowing_", "")}_bucket',
                     'minecraft:water_bucket' if path == 'water' else None):
            if cand and cand in self.w.known_items:
                return cand
        tagged = self.w.item_tags.get(rl(fluid), [])
        return None

    def ing_display_item(self, g):
        if g.fluid:
            return self.fluid_icon_item(g.fluid)
        if not g.items:
            return None
        if len(g.items) == 1:
            return g.items[0]
        # for a tag, show the member the player is most likely to have
        cur = getattr(self, 'cur_step', None) or 10 ** 6
        prefer = self.cfg.get('prefer_items') or []

        def rank(it):
            steps = self.item_steps.get(it, [])
            nat = self.k.natural_sources(it)
            return (0 if any(n <= cur for n in steps) else 1,
                    nat[0]['score'] if nat else 99,
                    prefer.index(it) if it in prefer else 50,
                    0 if self.w.by_output.get(it) else 1,
                    0 if self.icons.get(it) else 1,
                    0 if it.startswith('minecraft:') or it.startswith('create:') else 1,
                    it)
        return min(g.items, key=rank)

    def ing_name(self, g):
        if g.fluid:
            return f'{g.amount} mB {self.w.name(g.fluid)}'
        if g.tag and len(g.items) != 1:
            base = self.w.name(self.ing_display_item(g)) if g.items else g.tag
            return f'any {self.tag_label(g.tag, base)}'
        return self.w.name(g.items[0]) if g.items else '?'

    def tag_label(self, tag, base):
        ns, path = split_rl(tag)
        nice = {'forge:ingots/iron': 'Iron Ingot', 'minecraft:planks': 'Planks', 'minecraft:logs': 'Log',
                'minecraft:saplings': 'Sapling', 'minecraft:coals': 'Coal or Charcoal'}.get(tag)
        if nice:
            return nice
        last = path.split('/')[-1].replace('_', ' ')
        if '/' in path:
            return f'{last.title()} {path.split("/")[0].rstrip("s").replace("_", " ").title()}'.strip()
        return base if base else last.title()

    def slot(self, g, show_count=True):
        if g is None:
            return '<span class="slot empty"></span>'
        it = self.ing_display_item(g)
        name = self.ing_name(g)
        cnt = ''
        if g.fluid:
            cnt = f'<b class="cnt fl">{g.amount if g.amount < 1000 or g.amount % 1000 else str(g.amount // 1000) + "B"}</b>'
        elif show_count and g.count and g.count > 1:
            cnt = f'<b class="cnt">{g.count}</b>'
        chance = f'<i class="ch">{fmt_pct(g.chance)}</i>' if g.chance is not None and g.chance < 0.9995 else ''
        tag = '<i class="tg">#</i>' if (g.tag and len(g.items) != 1) else ''
        return f'<span class="slot" title="{esc(name)}">{self.icon(it, "s", name)}{cnt}{chance}{tag}</span>'

    def chip(self, item, count=None, cls=''):
        c = f'{count}× ' if count and count > 1 else ''
        return f'<span class="chip {cls}">{self.icon(item, "xs")}{esc(c)}{esc(self.w.name(item))}</span>'

    def ing_chip(self, g):
        it = self.ing_display_item(g)
        c = '' if g.fluid else (f'{g.count}× ' if g.count > 1 else '')
        return f'<span class="chip">{self.icon(it, "xs")}{esc(c)}{esc(self.ing_name(g))}</span>'

    def step_ref(self, n):
        q = self.steps[n - 1]
        return f'<a class="sref" href="#s{n}">#{n} {esc(q.title)}</a>'

    # ------------------------------------------------------------ recipe choice
    def recipe_score(self, r, target, step_n):
        s = TYPE_RANK.get(r.type, 4) * 2
        cat = r.extra.get('catalyst')
        if cat:
            if any(target == o for rr in self.w.by_input.get(target, []) for o in rr.output_items() if o == cat) or \
                    any(cat in rr.output_items() for rr in self.w.by_input.get(target, [])):
                s += 6
            later = [n for n in self.item_steps.get(cat, []) if step_n and n > step_n]
            if later and not [n for n in self.item_steps.get(cat, []) if step_n and n <= step_n]:
                s += 3
        if r.origin.startswith('CraftTweaker'):
            s -= 4
        elif r.origin.startswith('quicreate') or 'quicreate-' in r.origin:
            s -= 2
        mach = MACHINES.get(r.type, (None, None))[1]
        if mach and step_n:
            ms = self.item_steps.get(mach, [])
            if ms and min(ms) > step_n:
                s += 4
        if re.search(r'recycl|from_block|decompact|item_copying|_from_compacting|undo|uncraft', r.id):
            s += 8
        cyc = False
        col = self.collapse(r.inputs)
        outc = r.outputs[0].count if r.outputs else 1
        if len(col) == 1 and col[0].count == 1 and outc >= 4 and not col[0].fluid and r.type in (
                'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'):
            s += 4       # unpacking a storage block
        if len(col) == 1 and col[0].count >= 4 and r.type in ('minecraft:crafting_shaped', 'minecraft:crafting_shapeless'):
            s += 3       # packing nuggets: fine, but the smelting route reads better
        if r.type in ('create:crushing', 'create:milling', 'minecraft:smelting', 'minecraft:blasting', 'create:haunting'):
            for g in col:
                if g.items and any(g.items[0] in rr.output_items() for rr in self.w.by_input.get(target, [])):
                    cyc = True   # recycling something that is made from the target
        for g in col:
            for it in g.items[:1]:
                later = [n for n in self.item_steps.get(it, []) if step_n and n > step_n + 0]
                earlier = [n for n in self.item_steps.get(it, []) if step_n and n <= step_n]
                if later and not earlier:
                    s += 3
        if cyc:
            s += 6
        for g in r.inputs:
            if g.fluid:
                if not self.has_any_source(g.fluid, True):
                    s += 8
            elif g.items and not any(self.has_any_source(it) or self.item_steps.get(it) for it in g.items):
                s += 8
        if target not in r.output_items():
            s += 20
        # main output, not a by-product
        if r.outputs and r.outputs[0].items and r.outputs[0].items[0] != target:
            s += 20
        return s

    def best_recipes(self, target, step_n=None, limit=2, max_score=None, skip_gather=False):
        rs = [r for r in self.w.by_output.get(target, []) if r.type != 'cards:pack_contents' or 'card' in target]
        if skip_gather:
            rs = [r for r in rs if r.type not in ('createsifter:sifting', 'create_mechanical_extruder:extruding')]
        scored = sorted(((self.recipe_score(r, target, step_n), r.id, r) for r in rs), key=lambda x: (x[0], x[1]))
        seen, out = set(), []
        for s, _id, r in scored:
            sig = (MACHINES.get(r.type, (r.type,))[0], tuple(sorted(g.key() for g in r.inputs)),
                   tuple(o.key() for o in r.outputs))
            if sig in seen:
                continue
            seen.add(sig)
            if max_score is not None and s > max_score:
                continue
            out.append(r)
        return out[:limit], max(0, len(rs) - min(limit, len(out)))

    # ------------------------------------------------------------ recipe rendering
    def machine(self, r):
        label, item = MACHINES.get(r.type, (r.type.split(':')[1].replace('_', ' ').title(), None))
        extra = []
        e = r.extra
        if e.get('heat') and e['heat'] != 'none':
            extra.append({'heated': 'Heated', 'superheated': 'Superheated'}.get(e['heat'], e['heat']))
        if r.type == 'createsifter:sifting':
            if e.get('mesh'):
                extra.append(self.w.name(e['mesh']))
            if e.get('waterlogged'):
                extra.append('waterlogged sifter')
        if r.type == 'create_mechanical_extruder:extruding':
            if e.get('catalyst'):
                extra.append(f'{self.w.name(e["catalyst"])} below')
        if e.get('energy') and r.type == 'create_new_age:energising':
            extra.append(f'{e["energy"]} energy')
        if e.get('keep_held'):
            extra.append('held item is kept')
        mi = e.get('mesh') if r.type == 'createsifter:sifting' else item
        return label, mi, extra, item

    def recipe_html(self, r, compact=False):
        self.recipe_shown += 1
        label, mi, extra, mitem = self.machine(r)
        src = self.origin_label(r)
        outs = ''.join(self.slot(o) for o in r.outputs[:8])
        head = (f'<div class="rhead">{self.icon(mitem, "xs") if mitem else ""}<b>{esc(label)}</b>'
                + (f' <span class="tagx">{esc(" · ".join(extra))}</span>' if extra else '')
                + f'<span class="rsrc">{esc(src)}</span></div>')
        if r.grid:
            rows = ''.join('<div class="grow">' + ''.join(self.slot(c, False) for c in row) + '</div>' for row in r.grid)
            body = f'<div class="grid g{max(len(row) for row in r.grid)}">{rows}</div>'
        elif r.type == 'create:sequenced_assembly':
            steps = []
            for st in r.steps or []:
                adds = [g for g in st.inputs[1:]] if st.inputs else []
                lab, _mi, ex, mit = self.machine(st)
                steps.append(f'<span class="sq">{self.icon(mit, "xs")}' + ''.join(self.slot(g) for g in adds) + '</span>')
            body = (f'<div class="ins">{"".join(self.slot(g) for g in r.inputs)}</div>'
                    f'<div class="seq">{"<span class=arr>›</span>".join(steps)}<span class="loops">× {r.extra.get("loops", 1)} loop{"s" if r.extra.get("loops", 1) != 1 else ""}</span></div>')
        else:
            ins = list(r.inputs)
            if r.type == 'createsifter:sifting' and r.extra.get('mesh'):
                pass
            body = f'<div class="ins">{"".join(self.slot(g) for g in ins)}</div>'
        return (f'<div class="recipe">{head}<div class="rbody">{body}<span class="arrow">→</span>'
                f'<div class="outs">{outs}</div></div></div>')

    def origin_label(self, r):
        o = r.origin
        if o.startswith('CraftTweaker'):
            return 'pack script'
        if 'quicreate' in o:
            return 'Quicreate'
        if o.startswith('vanilla'):
            return 'vanilla'
        m = re.match(r'jar:([A-Za-z_\-]+?)[-_]?(?:forge|mc)?[-_]?\d', o)
        return (m.group(1) if m else o.replace('jar:', '')).replace('_', ' ').strip('-')

    # ------------------------------------------------------------ sources
    def source_lines(self, key, step_n, depth=0, is_fluid=False, limit=4):
        """HTML list items describing where an item (or fluid) comes from."""
        lines = []
        if not is_fluid:
            st = self.item_steps.get(key, [])
            if st and step_n:
                prev = [n for n in st if n < step_n]
                nxt = [n for n in st if n > step_n]
                if prev:
                    lines.append(f'Made in {self.step_ref(prev[-1])}')
                elif nxt:
                    lines.append(f'Covered later in {self.step_ref(nxt[0])}')
            scored = [(d['score'], esc(d['text'])) for d in self.k.natural_sources(key)]
            scored += [(1, l) for l in self.gather_lines(key)[:3]]
            made_here = bool(lines)
            if not made_here:
                rl_ = self.recipe_line(key, step_n)
                if rl_:
                    scored.append((rl_[0] + 2, rl_[1]))
            scored.sort(key=lambda x: x[0])
            lines += [l for _, l in scored[:(2 if made_here else limit)]]
            lines += self.mechanic_lines(key)
        else:
            lines += self.gather_lines(key)[:3]
            rl_ = self.recipe_line(key, step_n)
            if rl_:
                lines.append(rl_[1])
        if key.endswith('_bucket') and not is_fluid:
            fluid = key[:-7]
            if self.w.by_output.get(fluid) or self.k.natural.get(fluid):
                lines.append(f'Fill a bucket with {esc(self.w.name(fluid))} (Spout, or pick it up)')
        if not lines:
            rl_ = self.recipe_line(key, step_n, cutoff=None)
            if rl_:
                lines.append(rl_[1])
        return lines

    def recipe_line(self, key, step_n, cutoff=7):
        rs, _ = self.best_recipes(key, step_n, 1, max_score=cutoff, skip_gather=True)
        if not rs:
            return None
        r = rs[0]
        lab, _mi, extra, mitem = self.machine(r)
        ins = ' + '.join(self.ing_chip(g) for g in self.collapse(r.inputs)[:6])
        oc = r.outputs[0].count if r.outputs else 1
        txt = (f'{self.icon(mitem, "xs") if mitem else ""}{esc(lab)}' + (f' ({esc(", ".join(extra))})' if extra else '')
               + f': {ins}' + (f' → {oc}' if oc > 1 else ''))
        return self.recipe_score(r, key, step_n), txt

    def gather_lines(self, key):
        lines = []
        gather = [r for r in self.w.by_output.get(key, []) if r.type in ('createsifter:sifting', 'create_mechanical_extruder:extruding')]
        gather.sort(key=lambda r: -max((o.chance for o in r.outputs if (o.items and o.items[0] == key)), default=0))
        seen_g = set()
        for r in gather[:6]:
            if r.id in seen_g:
                continue
            seen_g.add(r.id)
            os_ = [o for o in r.outputs if o.items and o.items[0] == key]
            o = Ing([key], chance=1 - math.prod(1 - x.chance for x in os_)) if os_ else None
            if r.type == 'createsifter:sifting':
                inp = self.ing_name(r.inputs[0]) if r.inputs else '?'
                lines.append(f'Sift {esc(inp)} with {self.icon(r.extra.get("mesh"), "xs")}{esc(self.w.name(r.extra.get("mesh") or ""))}'
                             + (' (waterlogged)' if r.extra.get('waterlogged') else '')
                             + f': <b>{fmt_pct(o.chance if o else 1)}</b>')
            else:
                cat = r.extra.get('catalyst')
                fl = ' + '.join(self.w.name(g.fluid) for g in r.inputs if g.fluid)
                lines.append('Mechanical Extruder' + (f' with {self.icon(cat, "xs")}{esc(self.w.name(cat))} below' if cat else ' (nothing below)')
                             + (f' ({esc(fl)})' if fl else ''))
        return lines

    def mechanic_lines(self, key):
        out = []
        for pat, text in (self.cfg.get('mechanics') or {}).items():
            if re.fullmatch(pat.replace('*', '.*'), key):
                out.append(self.md(text)[3:-4] + ' <span class="small">(game mechanic)</span>')
        return out

    def ingredient_table(self, r, it, n, q):
        ings = self.collapse([g for g in r.inputs])
        if r.type == 'create:sequenced_assembly':
            for st in r.steps or []:
                ings += [g for g in st.inputs[1:]]
            ings = self.collapse(ings)
        rows = []
        for g in ings:
            key = g.fluid if g.fluid else self.ing_display_item(g)
            if not key or key == it:
                continue
            if r.type == 'create:sequenced_assembly' and key == r.extra.get('transitional') and \
                    key not in [x for gg in r.inputs for x in gg.items]:
                continue
            lines = self.source_lines(key, n, is_fluid=bool(g.fluid))
            if not self.has_any_source(key, bool(g.fluid)) and not self.item_steps.get(key):
                self.no_source.setdefault(key, set()).add(f'#{n} {q.title}')
                lines = ['<span class="warn">No source found in the pack files</span>']
            ic = self.icon(self.ing_display_item(g), "s") if self.ing_display_item(g) else self.icon(None, "s")
            rows.append(f'<tr><td class="ii">{ic}</td><td class="in">{esc(self.ing_name(g))}</td><td class="iw">{"<br/>".join(lines)}</td></tr>')
        cat = r.extra.get('catalyst')
        if cat:
            rows.append(f'<tr><td class="ii">{self.icon(cat, "s")}</td><td class="in">{esc(self.w.name(cat))} (below)</td>'
                        f'<td class="iw">{"<br/>".join(self.source_lines(cat, n))}</td></tr>')
        if not rows:
            return ''
        return f'<table class="srcs"><tr><th colspan="2">Ingredient</th><th>Where it comes from</th></tr>{"".join(rows)}</table>'

    def collapse(self, ings):
        out, seen = [], {}
        for g in ings:
            k = g.key()
            if k in seen:
                seen[k].count += g.count
            else:
                c = Ing(g.items, g.tag, g.count, g.fluid, g.amount, g.chance)
                seen[k] = c
                out.append(c)
        return out

    def has_any_source(self, key, is_fluid=False):
        if self.w.by_output.get(key) or self.k.natural.get(key):
            return True
        for pat in (self.cfg.get('mechanics') or {}):
            if re.fullmatch(pat.replace('*', '.*'), key):
                return True
        if key.endswith('_bucket') and (self.w.by_output.get(key[:-7]) or self.k.natural.get(key[:-7])):
            return True
        return False

    # ------------------------------------------------------------ markdown-ish text from yaml / quests
    def md(self, text):
        if not text:
            return ''
        t = esc(text)
        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
        t = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*', r'<i>\1</i>', t)
        t = re.sub(r'/\d+/(.+?)/\d+/', r'<b>\1</b>', t)        # heracles colour codes like /5/Creative/5/
        t = re.sub(r'\[\[([a-z0-9_]+:[a-z0-9_/]+)\]\]', lambda m: self.chip(m.group(1)), t)
        t = re.sub(r'\[\[#([a-z0-9_]+)\]\]', lambda m: self.step_ref(self.step_no[m.group(1)])
                   if m.group(1) in self.step_no else m.group(0), t)
        paras = [p.strip() for p in t.split('\n\n') if p.strip()]
        return ''.join(f'<p>{p}</p>' for p in paras)

    # ------------------------------------------------------------ a step
    def task_line(self, t, ch):
        typ = t.get('type', '')
        if typ == 'heracles:item':
            it = t.get('item', '')
            n = t.get('amount', 1)
            if it.startswith('#'):
                items = self.w.tag_items(it[1:])
                rep = items[0] if items else None
                return f'Collect {n}× {self.icon(rep, "xs")}<b>{esc(t.get("title") or "any " + it[1:])}</b>'
            return f'Collect {n}× {self.icon(it, "xs")}<b>{esc(self.w.name(it))}</b>'
        if typ == 'heracles:kill_entity':
            e = t.get('entity', {}).get('type', '?')
            return f'Defeat <b>{esc(self.w.name(e))}</b>'
        if typ == 'heracles:structure':
            s = t.get('structures', '?')
            info = self.k.structures.get(rl(s))
            where = f' on {esc(self.k.planet_name(info["planet"]))}' if info else ''
            return f'Find the <b>{esc(self.w.name(s))}</b>{where}'
        if typ == 'heracles:changed_dimension':
            return f'Travel to <b>{esc(self.w.name(t.get("to", "?")) if t.get("to") else "?")}</b>'
        if typ == 'heracles:check':
            return f'<b>{esc(t.get("title") or "Read the quest")}</b> (tick it in the quest book)'
        return esc(t.get('title') or typ)

    def step_html(self, q, ch):
        n = self.step_no[q.id]
        sc = (self.cfg.get('steps') or {}).get(q.id, {}) or {}
        deps = [d for d in q.deps if d in self.step_no]
        dep_html = ''
        if deps:
            dep_html = '<div class="deps">After ' + ', '.join(self.step_ref(self.step_no[d]) for d in deps) + '</div>'
        missing_deps = [d for d in q.deps if d not in self.step_no]
        for d in missing_deps:
            self.problems.append(f'Quest "{q.id}" depends on "{d}", which is not in the quest book.')
        tasks = ''.join(f'<li>{self.task_line(t, ch)}</li>' for t in q.tasks)
        desc = ''
        if q.desc:
            desc = '<div class="qdesc">' + '<br/>'.join(self.md(l)[3:-4] if self.md(l) else '' for l in q.desc) + '</div>'
        note = f'<div class="note">{self.md(sc["note"])}</div>' if sc.get('note') else ''
        body = []
        kind = 'read' if all(t.get('type') == 'heracles:check' for t in q.tasks) else ''
        # recipes for each item asked for
        self.cur_step = n
        max_score = (self.cfg.get('settings') or {}).get('recipe_score_cutoff', 7)
        for t in q.items():
            it = t.get('item', '')
            if it.startswith('#'):
                continue
            it = rl(it)
            if sc.get('hide_recipe'):
                continue
            gl = self.gather_lines(it)
            nat = self.k.natural_sources(it)
            easy = bool(gl) or (nat and nat[0]['score'] <= 4)
            rs, more = self.best_recipes(it, n, 1 if easy else sc.get('recipes', 2), max_score=max_score, skip_gather=True)
            if not rs and not easy:
                rs, more = self.best_recipes(it, n, 1, skip_gather=True)
            gathered = [l for _, l in sorted([(1, l) for l in gl[:3]] + [(d['score'], esc(d['text'])) for d in nat], key=lambda x: x[0])[:6]]
            gathered += self.mechanic_lines(it)
            src_tab = ''
            if gathered:
                head = 'Also from' if (rs and not easy) else 'Where it comes from'
                src_tab = (f'<table class="srcs"><tr><th colspan="2">Item</th><th>{head}</th></tr>'
                           f'<tr><td class="ii">{self.icon(it, "s")}</td><td class="in">{esc(self.w.name(it))}</td>'
                           f'<td class="iw">{"<br/>".join(gathered)}</td></tr></table>')
            if easy:
                body.append(src_tab)
            if rs:
                if easy:
                    body.append('<div class="more">Or make it:</div>')
                body.append(''.join(self.recipe_html(r) for r in rs))
                if more:
                    body.append(f'<div class="more">+{more} other recipe{"s" if more > 1 else ""} in JEI</div>')
                body.append(self.ingredient_table(rs[0], it, n, q))
            if not easy:
                body.append(src_tab)
            if not rs and not gathered:
                lines = self.source_lines(it, None, limit=5)
                if not self.has_any_source(it):
                    self.no_source.setdefault(it, set()).add(f'#{n} {q.title}')
                    lines = ['<span class="warn">No recipe or natural source found in the pack files</span>']
                body.append(f'<table class="srcs"><tr><th colspan="2">Item</th><th>Where it comes from</th></tr>'
                            f'<tr><td class="ii">{self.icon(it, "s")}</td><td class="in">{esc(self.w.name(it))}</td>'
                            f'<td class="iw">{"<br/>".join(lines)}</td></tr></table>')
        for t in q.tasks:
            if t.get('type') == 'heracles:kill_entity':
                body.append(self.boss_html(t.get('entity', {}).get('type'), ch))
        for extra in sc.get('show_recipes_for', []) or []:
            rs, _ = self.best_recipes(rl(extra), n, 1)
            body.append(''.join(self.recipe_html(r) for r in rs))
        icon = q.icon
        return (f'<section class="step {kind}" id="s{n}"><div class="shead">{self.icon(icon, "l")}'
                f'<div class="stitle"><span class="sno">#{n}</span> {esc(q.title)}'
                f'{"<div class=ssub>" + self.md(q.subtitle)[3:-4] + "</div>" if q.subtitle else ""}</div></div>'
                f'{dep_html}<ul class="tasks">{tasks}</ul>{desc}{note}{"".join(body)}</section>')

    def boss_html(self, eid, ch):
        if not eid:
            return ''
        drops = self.k.loot.drops_of_entity(eid)
        if not drops:
            return f'<div class="boss"><b>Drops:</b> {esc(self.w.name(eid))} has no loot table in the files (its drops are handled by the game code).</div>'
        cells = ''.join(f'<span class="drop">{self.icon(d["item"], "s")}<span>{esc(self.w.name(d["item"]))}'
                        f'<br/><i>{self.count_range(d)} · {fmt_pct(d["chance"])}</i></span></span>' for d in drops)
        return f'<div class="boss"><div class="bh">Drops (from the loot table)</div><div class="drops">{cells}</div></div>'

    @staticmethod
    def count_range(d):
        lo, hi = d.get('min', 1), d.get('max', 1)
        lo = int(lo) if float(lo).is_integer() else lo
        hi = int(hi) if float(hi).is_integer() else hi
        if hi and lo != hi:
            return f'{lo}–{hi}'
        return f'{hi or 1}'

    # ------------------------------------------------------------ planets
    def planet_box(self, key):
        p = self.k.planets.get(key)
        pc = (self.cfg.get('planets') or {}).get(key, {})
        if not p:
            return ''
        out = [f'<div class="planet"><h3>{esc(pc.get("name", key))}: what is here</h3>']
        if pc.get('intro'):
            out.append(f'<div class="pintro">{self.md(pc["intro"])}</div>')
        biomes = ', '.join(esc(self.w.name(b)) for b in p['biomes'])
        out.append(f'<p class="small"><b>Biomes:</b> {biomes}</p>')
        terr = ''.join(self.chip(b) for b in p['terrain'] if b in self.w.known_items)
        if terr:
            out.append(f'<p class="small"><b>Terrain:</b> {terr}</p>')
        if p['ores']:
            rows = []
            for fid, o in p['ores'].items():
                for b in o['blocks']:
                    drops = self.k.loot.drops_of_block(b)
                    drop = ', '.join(self.chip(d['item']) for d in drops if d['item'] != b) or '<span class="small">itself</span>'
                    per = f'{o["count"]:g}' if o.get('count') else '?'
                    rows.append(f'<tr><td>{self.chip(b)}</td><td>{drop}</td><td>{esc(o.get("height") or "")}</td>'
                                f'<td class="num">{per}</td><td class="num">{o.get("size") or ""}</td></tr>')
            out.append('<table class="ptab"><tr><th>Ore / deposit</th><th>Drops</th><th>Height</th>'
                       '<th>Veins / chunk</th><th>Vein size</th></tr>' + ''.join(rows) + '</table>')
        feats = []
        for fid, o in p['features'].items():
            if fid.startswith('quicreate:') or fid.startswith('ad_astra:'):
                bl = [b for b in o['blocks'] if b in self.w.known_items and not b.startswith('minecraft:air')]
                if bl:
                    feats.append(f'<li><b>{esc(fid.split(":")[1].replace("_", " "))}</b>: '
                                 + ''.join(self.chip(b) for b in bl[:6]) + '</li>')
        if feats:
            out.append('<p class="small"><b>Surface features</b> (from the worldgen files):</p><ul class="feat">'
                       + ''.join(feats) + '</ul>')
        if p['mobs']:
            rows = []
            for mob in p['mobs']:
                drops = self.k.loot.drops_of_entity(mob)
                dr = ', '.join(f'{self.chip(d["item"])} <span class="small">{fmt_pct(d["chance"])}</span>' for d in drops[:6]) \
                    or '<span class="small">no loot table in the files</span>'
                rows.append(f'<tr><td><b>{esc(self.w.name(mob))}</b></td><td>{dr}</td></tr>')
            out.append('<table class="ptab"><tr><th>Mob (natural spawns)</th><th>Drops per kill</th></tr>' + ''.join(rows) + '</table>')
        if p['structures']:
            rows = []
            for s in p['structures']:
                info = self.k.structures.get(s['id'], {})
                mobs = sorted(set(s.get('spawns', [])) | set(info.get('mobs', [])))
                mob_txt = ', '.join(esc(self.w.name(m)) for m in mobs) or '–'
                loot = info.get('loot', [])
                notable = self.notable_loot(loot)
                rows.append(f'<tr><td><b>{esc(self.w.name(s["id"]))}</b><br/><span class="small">'
                            f'{esc(", ".join(self.w.name(b) for b in s["biomes"]))}</span></td>'
                            f'<td>{mob_txt}</td><td>{notable}</td></tr>')
            out.append('<table class="ptab"><tr><th>Structure (biomes)</th><th>Mobs inside</th><th>Chest loot highlights</th></tr>'
                       + ''.join(rows) + '</table>')
        out.append('</div>')
        return ''.join(out)

    def notable_loot(self, tables):
        agg = {}
        for t in tables:
            for d in self.k.loot.summary(t):
                if d['item']:
                    agg[d['item']] = max(agg.get(d['item'], 0), d['chance'])
        if not agg:
            return '–'
        prio = set(self.item_steps)
        items = sorted(agg.items(), key=lambda kv: (kv[0] not in prio, -kv[1]))[:8]
        return ' '.join(f'{self.chip(i)}<span class="small">{fmt_pct(c)}</span>' for i, c in items)

    # ------------------------------------------------------------ chapters
    def chapter_html(self, idx, ch):
        c = ch['cfg']
        color = c.get('color', '#355')
        title = c.get('title', c['group'])
        qs = ch['quests']
        nums = f'#{self.step_no[qs[0].id]}–#{self.step_no[qs[-1].id]}' if qs else ''
        out = [f'<div class="chapter" id="ch{idx}" style="--acc:{color}">']
        out.append(f'<div class="chhead">{self.icon(c.get("icon"), "xl")}<div><div class="chgroup">{esc(c["group"])} · steps {nums}</div>'
                   f'<h2 class="chtitle">{esc(title)}</h2>{"<div class=chsub>" + esc(c["subtitle"]) + "</div>" if c.get("subtitle") else ""}</div></div>')
        if c.get('intro'):
            out.append(f'<div class="intro">{self.md(c["intro"])}</div>')
        if c.get('tips'):
            out.append('<div class="tips"><b>Tips</b><ul>' + ''.join(f'<li>{self.md(t)[3:-4]}</li>' for t in c['tips']) + '</ul></div>')
        for pk in (c.get('planets') or ([c['planet']] if c.get('planet') else [])):
            out.append(self.planet_box(pk))
        bosses = [b for b in self.cfg['bosses'] if b.get('quest') in {q.id for q in qs}]
        if bosses:
            rows = []
            for b in bosses:
                q = self.quests[b['quest']]
                st = [d for d in q.deps if d in self.quests and any(t.get('type') == 'heracles:structure' for t in self.quests[d].tasks)]
                where = ', '.join(esc(self.w.name(self.quests[d].tasks[0].get('structures', ''))) for d in st) or '–'
                opt = ' (optional)' if 'optional' in (q.subtitle or '').lower() else ''
                rows.append(f'<tr><td><b>{esc(self.w.name(b["entity"]))}</b>{opt}</td><td>{where}</td>'
                            f'<td>{self.step_ref(self.step_no[q.id])}</td></tr>')
            out.append('<table class="ptab bosses"><tr><th>Boss</th><th>Found in</th><th>Step</th></tr>' + ''.join(rows) + '</table>')
        out.append('<div class="steps">')
        for q in qs:
            out.append(self.step_html(q, ch))
        out.append('</div></div>')
        return ''.join(out)

    # ------------------------------------------------------------ front matter
    def cover_html(self):
        m = self.cfg.get('meta', {})
        icon = ''
        ip = os.path.join(self.args.instance, 'icon.png')
        if os.path.exists(ip):
            im = Image.open(ip).convert('RGBA')
            if im.size[0] < 256:
                im = im.resize((256, 256), Image.NEAREST)
            im.save(os.path.join(self.icons.out_dir, '_pack_icon.png'))
            icon = '<img class="packicon" src="icons/_pack_icon.png"/>'
        strip = ''.join(self.icon(i, 'l') for i in m.get('cover_items', []))
        return (f'<div class="cover">{icon}<h1>{esc(m.get("title", "Quicreate Skyblock"))}</h1>'
                f'<div class="ver">{esc(m.get("subtitle", ""))}</div><div class="strip">{strip}</div>'
                f'<div class="coverbl">{self.md(m.get("cover_text", ""))}</div>'
                f'<div class="built">Built {datetime.date.today().isoformat()} from the pack files · '
                f'{len(self.steps)} quest steps · {len(self.chapters)} chapters</div></div>')

    def howto_html(self):
        m = self.cfg.get('how_to_use', '')
        legend = (f'<div class="legend"><div class="recipe">'
                  f'<div class="rhead">{self.icon("minecraft:crafting_table", "xs")}<b>Machine</b> <span class="tagx">conditions</span><span class="rsrc">who adds it</span></div>'
                  f'<div class="rbody"><div class="ins">{self.slot(Ing(["create:andesite_alloy"], count=2))}{self.slot(Ing(["minecraft:sand"], chance=0.5))}{self.slot(Ing(self.w.tag_items("minecraft:logs"), tag="minecraft:logs"))}'
                  f'{self.slot(Ing([], fluid="minecraft:water", amount=250))}</div><span class="arrow">→</span>'
                  f'<div class="outs">{self.slot(Ing(["create:andesite_casing"]))}</div></div></div>'
                  f'<ul class="small"><li>Small number: how many. <i>%</i>: chance. <i>#</i>: any item of that tag. '
                  f'Blue number: millibuckets of fluid.</li><li><b>#12</b> links point to the step where that item is made.</li></ul></div>')
        return f'<div class="howto"><h2>How to use this guide</h2>{self.md(m)}{legend}</div>'

    def route_html(self):
        rows = []
        for i, ch in enumerate(self.chapters):
            c = ch['cfg']
            if c.get('route') is False:
                continue
            qs = ch['quests']
            items = ''.join(self.icon(x, 's') for x in (c.get('route_items') or []))
            rows.append(f'<div class="rt" style="--acc:{c.get("color", "#355")}">{self.icon(c.get("icon"), "l")}'
                        f'<div class="rtx"><a href="#ch{i}"><b>{esc(c.get("title", c["group"]))}</b></a>'
                        f'<span class="small"> · {esc(c["group"])} · {len(qs)} steps</span>'
                        f'<div class="small">{self.md(c.get("summary", ""))[3:-4]}</div><div class="rti">{items}</div></div>'
                        f'<a class="pg" href="#ch{i}"></a></div>')
        return f'<div class="route"><h2>The route</h2><div class="small">{self.md(self.cfg.get("route_text", ""))}</div>{"".join(rows)}</div>'

    # ------------------------------------------------------------ appendices
    MESH_ORDER = ['createsifter:string_mesh', 'createsifter:andesite_mesh', 'createsifter:zinc_mesh',
                  'createsifter:brass_mesh', 'createsifter:advanced_brass_mesh']

    def appendix_sifting(self):
        by_in = collections.defaultdict(list)
        for r in self.w.recipes:
            if r.type == 'createsifter:sifting' and r.inputs:
                by_in[self.ing_display_item(r.inputs[0])].append(r)
        blocks = []
        order = self.cfg.get('sifting_order', [])
        keys = sorted(by_in, key=lambda k: (order.index(k) if k in order else 99, self.w.name(k)))
        for k in keys:
            rows = []
            for r in sorted(by_in[k], key=lambda r: (r.extra.get('waterlogged', False),
                                                      self.MESH_ORDER.index(r.extra.get('mesh')) if r.extra.get('mesh') in self.MESH_ORDER else 9)):
                outs = ' '.join(f'<span class="so">{self.icon(o.items[0], "xs")}{esc(self.w.name(o.items[0]))} <b>{fmt_pct(o.chance)}</b>'
                                + (f' ×{o.count}' if o.count > 1 else '') + '</span>' for o in r.outputs if o.items)
                rows.append(f'<tr><td>{self.icon(r.extra.get("mesh"), "s")}</td><td class="mesh">{esc(self.w.name(r.extra.get("mesh") or "?"))}'
                            f'{"<br/><span class=water>waterlogged</span>" if r.extra.get("waterlogged") else ""}</td><td>{outs}</td></tr>')
            blocks.append(f'<div class="siftblock"><h4>{self.icon(k, "m")} {esc(self.w.name(k))}</h4>'
                          f'<table class="sift">{"".join(rows)}</table></div>')
        return ('<div class="appendix" id="app-sift"><h2>Appendix A · Sifting tables</h2>'
                f'<div class="small">{self.md(self.cfg.get("appendix_text", {}).get("sifting", ""))}</div>' + ''.join(blocks) + '</div>')

    def appendix_extruder(self):
        rows = []
        for r in sorted([r for r in self.w.recipes if r.type == 'create_mechanical_extruder:extruding'],
                        key=lambda r: self.w.name(r.output_items()[0] if r.output_items() else '')):
            cat = r.extra.get('catalyst')
            fl = ' + '.join(esc(self.ing_name(g)) for g in r.inputs if g.fluid)
            items = ' + '.join(self.ing_chip(g) for g in r.inputs if not g.fluid)
            out = r.output_items()[0] if r.output_items() else None
            rows.append(f'<tr><td>{self.chip(out) if out else "?"}</td><td>{self.chip(cat) if cat else "<i>nothing</i>"}</td>'
                        f'<td>{fl}{(" + " + items) if items else ""}</td><td class="small">{esc(self.origin_label(r))}</td></tr>')
        return ('<div class="appendix" id="app-extr"><h2>Appendix B · Mechanical Extruder</h2>'
                f'<div class="small">{self.md(self.cfg.get("appendix_text", {}).get("extruder", ""))}</div>'
                '<table class="ptab"><tr><th>Makes</th><th>Block below (kept)</th><th>Needs next to it</th><th>Added by</th></tr>'
                + ''.join(rows) + '</table></div>')

    def appendix_fishing(self):
        if not self.k.fishing:
            return ''
        rows = []
        for t in self.k.fishing:
            tt = t['t']
            cells = []
            for w in ('light', 'medium', 'heavy'):
                cells.append(f'<td class="num">{fmt_pct(tt.get(w, 0)) if tt.get(f"{w}_item") else "–"}</td>')
            ex = ', '.join(f'{self.chip(e["item"])} {fmt_pct(e["chance"])}' for e in tt.get('extras', [])) or '–'
            rows.append(f'<tr><td><b>{esc(t["rod"])}</b></td>{"".join(cells)}<td>{ex}</td></tr>')
        balls = []
        for ball, table in (('quicreate:light_kelpy_ball', 'quicreate:kelpy_ball_light'),
                            ('quicreate:medium_kelpy_ball', 'quicreate:kelpy_ball_medium'),
                            ('quicreate:heavy_kelpy_ball', 'quicreate:kelpy_ball_heavy')):
            j = self.k.loot.table(table)
            if not j:
                continue
            pool = j['pools'][0]
            rmin, rmax, _ = _num(pool.get('rolls'))
            total = sum(e.get('weight', 1) for e in pool['entries'])
            cells = []
            for e in pool['entries']:
                names = [rl(e['name'])] if e.get('type', '').endswith('item') else self.w.tag_items(e['name'])
                cnt = ''
                for f in e.get('functions', []):
                    if f.get('function', '').endswith('set_count'):
                        a, b, _ = _num(f.get('count'))
                        cnt = f' {int(a)}–{int(b)}' if a != b else (f' {int(a)}' if a != 1 else '')
                label = self.w.name(names[0]) if len(names) == 1 else f'a music disc ({len(names)} kinds)'
                cells.append(f'<span class="so">{self.icon(names[0] if names else None, "xs")}{esc(label)}{esc(cnt)} '
                             f'<b>{fmt_pct(e.get("weight", 1) / total)}</b></span>')
            balls.append(f'<div class="siftblock"><h4>{self.icon(ball, "m")} {esc(self.w.name(ball))} '
                         f'<span class="small">({int(rmin)}–{int(rmax)} rolls; % is per roll)</span></h4>'
                         f'<div>{" ".join(cells)}</div></div>')
        return ('<div class="appendix" id="app-fish"><h2>Appendix C · Fishing and kelpy balls</h2>'
                f'<div class="small">{self.md(self.cfg.get("appendix_text", {}).get("fishing", ""))}</div>'
                '<table class="ptab"><tr><th>Rod</th><th>Light ball</th><th>Medium ball</th><th>Heavy ball</th><th>Rare extras</th></tr>'
                + ''.join(rows) + '</table>' + ''.join(balls) + '</div>')

    def appendix_cards(self):
        packs = [p for p in self.w.tag_items('cards:card_packs')] or []
        pack_rows = []
        for p in packs:
            src = []
            for r in self.w.by_output.get(p, []):
                if r.type == 'createsifter:sifting':
                    o = next(o for o in r.outputs if o.items and o.items[0] == p)
                    src.append(f'sift {esc(self.ing_name(r.inputs[0]))} + {esc(self.w.name(r.extra.get("mesh")))}'
                               + (' (waterlogged)' if r.extra.get('waterlogged') else '') + f' {fmt_pct(o.chance)}')
                elif r.type in ('minecraft:smelting', 'minecraft:blasting', 'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'):
                    src.append(f'{esc(MACHINES[r.type][0])}: ' + ' + '.join(self.ing_chip(g) for g in self.collapse(r.inputs)))
            for d in self.k.natural_sources(p):
                src.append(esc(d['text']))
            pack_rows.append(f'<tr><td>{self.chip(p)}</td><td class="small">{"<br/>".join(src) or "<span class=warn>no source found</span>"}</td></tr>')
        # card -> egg
        eggs = collections.defaultdict(list)
        for r in self.w.recipes:
            if r.origin.startswith('CraftTweaker') and any(o.items and o.items[0].endswith('_spawn_egg') for o in r.outputs):
                for g in r.inputs:
                    if g.items:
                        eggs[r.output_items()[0]].append(g.items[0])
        # card -> packs
        card_packs = collections.defaultdict(set)
        for r in self.w.recipes:
            if r.type in ('cards:pack_contents',) or (r.type == 'create:deploying' and r.origin and 'quicreate' in r.origin
                                                       and any((g.tag or '').startswith('cards:') for g in r.inputs)):
                for o in r.output_items():
                    for g in r.inputs:
                        if g.tag and g.tag.startswith('cards:'):
                            card_packs[o].add(g.tag)
        egg_rows = []
        for egg in sorted(eggs, key=lambda e: self.w.name(e)):
            cards = sorted(set(eggs[egg]), key=lambda c: self.w.name(c))
            cell = []
            for c in cards:
                tags = card_packs.get(c, set())
                pk = sorted({self.w.name(x) for t in tags for x in self.w.tag_items(t) if x.endswith('_pack') or x.endswith('_box')})
                cell.append(f'{self.chip(c)}<span class="small">{esc(", ".join(pk)) if pk else "not in any pack list in the files"}</span>')
            egg_rows.append(f'<tr><td>{self.chip(egg)}</td><td>{"<br/>".join(cell)}</td></tr>')
        return ('<div class="appendix" id="app-cards"><h2>Appendix D · Card packs, cards and spawn eggs</h2>'
                f'<div class="small">{self.md(self.cfg.get("appendix_text", {}).get("cards", ""))}</div>'
                '<h3>Where card packs come from</h3><table class="ptab"><tr><th>Pack</th><th>Sources</th></tr>'
                + ''.join(pack_rows) + '</table><h3>Spawn eggs from cards</h3>'
                '<table class="ptab eggs"><tr><th>Spawn egg</th><th>Card(s) that craft into it, and the packs that contain them</th></tr>'
                + ''.join(egg_rows) + '</table></div>')

    def appendix_bosses(self):
        rows = []
        for b in self.cfg['bosses']:
            drops = self.k.loot.drops_of_entity(b['entity'])
            dr = ' '.join(f'<span class="so">{self.icon(d["item"], "xs")}{esc(self.w.name(d["item"]))} {self.count_range(d)} '
                          f'<b>{fmt_pct(d["chance"])}</b></span>' for d in drops) or '<span class="small">no loot table in the files (drops handled by game code)</span>'
            rows.append(f'<tr><td><b>{esc(self.w.name(b["entity"]))}</b><br/><span class="small">'
                        f'{esc(self.k.planet_name(b.get("planet") or ""))} · {self.step_ref(self.step_no[b["quest"]])}</span></td><td>{dr}</td></tr>')
        return ('<div class="appendix" id="app-boss"><h2>Appendix E · Bosses and their drops</h2>'
                f'<div class="small">{self.md(self.cfg.get("appendix_text", {}).get("bosses", ""))}</div>'
                '<table class="ptab"><tr><th>Boss</th><th>Drops (loot table)</th></tr>' + ''.join(rows) + '</table></div>')

    def appendix_nosource(self):
        rows = []
        for it, where in sorted(self.no_source.items(), key=lambda kv: self.w.name(kv[0])):
            rows.append(f'<tr><td>{self.chip(it)}</td><td class="small">{esc(", ".join(sorted(where)))}</td></tr>')
        txt = self.cfg.get('appendix_text', {}).get('nosource', '')
        body = ('<table class="ptab"><tr><th>Item</th><th>Needed in</th></tr>' + ''.join(rows) + '</table>') if rows else \
            '<p>Every quest item and ingredient traced in this guide has at least one recipe or natural source in the pack files.</p>'
        audit = []
        for it in self.cfg.get('audit_items') or []:
            it = rl(it)
            lines = self.source_lines(it, None, limit=6)
            ok = self.has_any_source(it)
            self.audit[it] = ok
            audit.append(f'<tr><td>{self.chip(it)}</td><td class="small">{"<br/>".join(lines) if ok else "<span class=warn>no source found in the files</span>"}</td></tr>')
        if audit:
            body += ('<h3>Hard-to-get items checked</h3><div class="small">' + self.md(self.cfg.get('appendix_text', {}).get('audit', '')) +
                     '</div><table class="ptab"><tr><th>Item</th><th>Sources found in the files</th></tr>' + ''.join(audit) + '</table>')
        notes = self.cfg.get('progression_notes') or []
        if notes:
            body += '<h3>Progression notes</h3><ul>' + ''.join(f'<li>{self.md(n)[3:-4]}</li>' for n in notes) + '</ul>'
        return f'<div class="appendix" id="app-nosrc"><h2>Appendix F · Items with no source, and progression notes</h2><div class="small">{self.md(txt)}</div>{body}</div>'

    def appendix_notes(self, notes):
        return ('<div class="appendix notes" id="app-notes"><h2>Appendix G · Build notes</h2>'
                + ''.join(f'<h4>{esc(k)}</h4>{v}' for k, v in notes) + '</div>')

    # ------------------------------------------------------------ whole document
    def document(self, notes):
        toc = []
        parts = [self.cover_html(), self.howto_html(), self.route_html()]
        for i, ch in enumerate(self.chapters):
            parts.append(self.chapter_html(i, ch))
        apps = [self.appendix_sifting(), self.appendix_extruder(), self.appendix_fishing(), self.appendix_cards(),
                self.appendix_bosses(), self.appendix_nosource()]
        parts.extend(apps)
        parts.append(self.appendix_notes(notes))
        css = open(os.path.join(HERE, 'guide.css'), encoding='utf-8').read() if os.path.exists(
            os.path.join(HERE, 'guide.css')) else ''
        title = esc(self.cfg.get('meta', {}).get('title', 'Quicreate Skyblock'))
        return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title><style>{css}</style></head>'
                f'<body>{"".join(parts)}</body></html>')


# =====================================================================================
# 12. Main
# =====================================================================================

def default_paths():
    """Sensible defaults: run from <repo>/guide on Jake's PC, or the staged copy in a Claude session."""
    repo = os.path.dirname(HERE)
    win_inst = os.path.expanduser(r'~\AppData\Roaming\PrismLauncher\instances\Quicreate Skyblock RFA  0.9.0\minecraft')
    staged_inst = '/mnt/user-data/uploads/Quicreate Skyblock RFA  0.9.0/minecraft'
    inst = win_inst if os.path.isdir(win_inst) else staged_inst
    win_vanilla = os.path.expanduser(r'~\AppData\Roaming\PrismLauncher\libraries\com\mojang\minecraft\1.20.1\minecraft-1.20.1-client.jar')
    vanilla = [win_vanilla] if os.path.exists(win_vanilla) else []
    # Forge's own tags (forge:ingots/iron ...) live in the Forge universal jar
    forge = sorted(glob.glob(os.path.expanduser(
        r'~\AppData\Roaming\PrismLauncher\libraries\net\minecraftforge\forge\1.20.1-*\forge-1.20.1-*-universal.jar')))
    vanilla += forge[-1:]
    if not os.path.isdir(os.path.join(repo, 'src', 'main', 'resources')) and os.path.isdir('/mnt/user-data/uploads/Quicreate/src'):
        repo = '/mnt/user-data/uploads/Quicreate'
    return inst, repo, vanilla


def main(argv=None):
    inst, repo, vanilla = default_paths()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--instance', default=inst, help='the instance "minecraft" folder (has mods/, config/, scripts/)')
    ap.add_argument('--repo', default=repo, help='the Quicreate repo (src/main/resources is read as the newest datapack)')
    ap.add_argument('--vanilla', action='append', default=None,
                    help='vanilla 1.20.1 client jar, or extracted folders with assets/ and data/ (repeatable)')
    ap.add_argument('--yaml', default=os.path.join(HERE, 'guide.yaml'))
    ap.add_argument('--out', default=os.path.join(HERE, 'build'), help='output folder for HTML, icons and the PDF')
    ap.add_argument('--pdf', default=None, help='PDF path (default: <out>/Quicreate-Skyblock-Guide.pdf)')
    ap.add_argument('--quicreate-jar-fallback', action='store_true',
                    help='also read quicreate-*.jar from mods/ under the repo files (for a partial copy of the repo)')
    ap.add_argument('--extra-mods', nargs='*', default=[], help='mod ids to treat as loaded for recipe conditions')
    ap.add_argument('--no-pdf', action='store_true', help='only write the HTML')
    args = ap.parse_args(argv)
    args.vanilla = args.vanilla or vanilla
    if not args.vanilla:
        log('! No vanilla data given (--vanilla). Vanilla recipes, names and textures will be missing.')
    cfg = yaml.safe_load(open(args.yaml, encoding='utf-8'))
    os.makedirs(args.out, exist_ok=True)

    log('Reading the cleanup script and CraftTweaker scripts...')
    cleanup_path = None
    for c in sorted(glob.glob(os.path.join(args.repo or '', 'quicreate_cleanup_*.ps1'))):
        cleanup_path = c
    cleanup = parse_cleanup_ps1(cleanup_path)
    ct_dir = os.path.join(args.instance, 'scripts')
    ct_removals, ct_recipes, ct_unparsed = parse_ct_scripts(ct_dir, cleanup['scripts'])
    scripts_present = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ct_dir, '*.zs')))

    log('Loading resources...')
    pool, loaded, jars = build_pool(args, cleanup)
    world = World(pool, loaded, cleanup['data'])
    world.load_lang()
    world.load_tags()
    world.load_recipes(ct_removals, ct_recipes)
    log(f'  {len(pool.sources)} sources, {len(world.recipes)} recipes, {len(world.ct_removed)} removed by scripts')
    loot = Loot(world)
    wg = Worldgen(world, loot)
    scan = StructureScan(world)
    know = Knowledge(world, loot, wg, scan, cfg, args)
    groups, quests = load_quests(os.path.join(args.instance, 'config', 'heracles'))
    log(f'  {len(quests)} quests in {len(groups)} groups')
    icons = Icons(world, os.path.join(args.out, 'icons'), cfg.get('icon_overrides'))
    guide = Guide(world, know, icons, groups, quests, cfg, args).plan()
    know.build(quests)

    # quest items without any recipe or source (checked for every quest, not just shown ones)
    for q in guide.steps:
        for t in q.items():
            it = t.get('item', '')
            if it.startswith('#'):
                if not world.tag_items(it[1:]):
                    guide.problems.append(f'Quest "{q.id}" asks for tag {it}, which has no items.')
                continue
            if it not in world.known_items:
                guide.problems.append(f'Quest "{q.id}" asks for {it}, which no loaded mod seems to register.')

    log('Writing HTML...')
    notes = build_notes(args, cfg, pool, jars, cleanup, scripts_present, ct_removals, ct_recipes, ct_unparsed, world, icons, guide)
    html_doc = guide.document(notes)
    # notes are rendered before icon rendering finishes for appendix F etc., so render twice to pick up late data
    notes = build_notes(args, cfg, pool, jars, cleanup, scripts_present, ct_removals, ct_recipes, ct_unparsed, world, icons, guide)
    guide.no_source_snapshot = dict(guide.no_source)
    html_doc = guide.document(notes)
    hp = os.path.join(args.out, 'guide.html')
    open(hp, 'w', encoding='utf-8').write(html_doc)
    report = {
        'missing_icons': icons.missing,
        'no_source': {k: sorted(v) for k, v in guide.no_source.items()},
        'problems': guide.problems,
        'ct_unparsed': ct_unparsed,
        'steps': len(guide.steps),
        'audit': guide.audit,
    }
    json.dump(report, open(os.path.join(args.out, 'build_report.json'), 'w'), indent=1)
    log(f'  HTML: {hp}  ({len(icons.cache)} icons, {len(icons.missing)} missing)')
    if args.no_pdf:
        return 0
    pdf = args.pdf or os.path.join(args.out, 'Quicreate-Skyblock-Guide.pdf')
    log('Rendering PDF with WeasyPrint (takes a minute)...')
    import weasyprint
    weasyprint.HTML(filename=hp, base_url=args.out).write_pdf(pdf)
    log(f'  PDF: {pdf}')
    return 0


def build_notes(args, cfg, pool, jars, cleanup, scripts_present, ct_removals, ct_recipes, ct_unparsed, world, icons, guide):
    notes = []
    src_lines = []
    for s in pool.sources:
        n_data = sum(1 for r in s.files if r.startswith('data/'))
        n_assets = sum(1 for r in s.files if r.startswith('assets/'))
        src_lines.append((s.name, n_data, n_assets))
    vanilla = [s for s in src_lines if s[0].startswith('vanilla')]
    qc = [s for s in src_lines if 'quicreate' in s[0]]
    notes.append(('Files this guide was built from', (
        f'<p>Quest book: <code>config/heracles</code> ({len(guide.quests)} quests). '
        f'CraftTweaker: <code>scripts/</code> ({len(scripts_present)} scripts: {len(ct_removals)} removals, '
        f'{len(ct_recipes)} added recipes). Mods: {len(jars)} jars in <code>mods/</code>. '
        f'Quicreate datapack: ' + ', '.join(esc(f'{n} ({d} data files)') for n, d, a in qc) + '. '
        f'Vanilla data: ' + (', '.join(esc(n) for n, d, a in vanilla) or '<b>none</b>') + '.</p>'
        + (f'<p>{guide.md(cfg.get("build_notes", {}).get("vanilla", ""))}</p>' if cfg.get('build_notes', {}).get('vanilla') else '')
        + f'<p>Load order (later wins for recipes, loot tables and worldgen; tags merge): vanilla, then mod jars '
          f'alphabetically, then the Quicreate jar (only with <code>--quicreate-jar-fallback</code>), then the Quicreate '
          f'source folder.</p>')))
    present_data = sorted(r for r in cleanup['data'] if any(r in s.files for s in pool.sources if 'quicreate' in s.name)
                          or os.path.exists(os.path.join(args.repo or '', 'src', 'main', 'resources', r)))
    present_scripts = sorted(set(cleanup['scripts']) & set(scripts_present))
    if cleanup.get('path'):
        txt = (f'<p><code>{esc(os.path.basename(cleanup["path"]))}</code> lists {len(cleanup["moves"])} recipe files to rename, '
               f'{len(cleanup["data"]) - len(cleanup["moves"])} data files and {len(cleanup["scripts"])} scripts to delete. '
               f'The guide treats every listed file (and the old name of every renamed file) as already removed. ')
        if not present_data and not present_scripts:
            txt += 'At build time none of those files existed any more, so the cleanup appears to have been applied already.</p>'
        else:
            txt += (f'Still present and ignored: {len(present_data)} data files, {len(present_scripts)} scripts '
                    f'({esc(", ".join(present_scripts[:10]))}).</p>')
        notes.append(('Quicreate cleanup script', txt))
    rem = collections.Counter(s for _, s in world.ct_removed)
    notes.append(('Recipes removed by CraftTweaker', '<p class="small">' + ', '.join(
        f'{esc(world.name(r.output_items()[0]))} ({esc(r.id)})' for r, s in world.ct_removed if r.output_items()) + '</p>'))
    if ct_unparsed:
        notes.append(('CraftTweaker lines the builder could not read', '<ul>' + ''.join(
            f'<li><code>{esc(n)}</code>: {esc(s[:120])}</li>' for n, s in ct_unparsed) + '</ul>'))
    if icons.missing:
        notes.append(('Items drawn without a texture', '<p class="small">These items have no plain texture in the files '
                      '(they are drawn by code, e.g. rockets and globes) and show a placeholder: ' + ', '.join(
                          f'{esc(world.name(k))} <code>{esc(k)}</code>' for k in sorted(icons.missing)) + '</p>'))
    if guide.problems:
        notes.append(('Quest book checks', '<ul>' + ''.join(f'<li>{esc(p)}</li>' for p in guide.problems) + '</ul>'))
    for k, v in (cfg.get('build_notes') or {}).items():
        if k != 'vanilla':
            notes.append((k.replace('_', ' ').capitalize(), guide.md(v)))
    return notes


if __name__ == '__main__':
    sys.exit(main())
