"""Export the block-state properties of every modded block into guide/book/block_props.json.

The book editor uses this to catch build-preview blocks whose properties don't exist in the installed
mods (Modonomicon crashes the game on load if a multiblock names a property the block doesn't have).

    python guide/book/dump_block_props.py --mods "<prism instance>/minecraft/mods"

Properties are read from each mod's blockstate files. A few properties never show up there (they don't
change the model), so EXTRA lists ones checked by hand against the mods' code.
"""
import argparse, glob, json, os, re, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BOOL = ['false', 'true']
EXTRA = {
    'create:metal_girder': {'axis': ['x', 'y', 'z'], 'waterlogged': BOOL},
    'quicreate:preview_generator_coil': {'axis': ['x', 'y', 'z']},   # new in this version of Quicreate
    'create:blaze_burner': {'blaze': ['none', 'smouldering', 'fading', 'kindled', 'seething'],
                            'facing': ['north', 'south', 'west', 'east']},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', required=True)
    a = ap.parse_args()
    props = {}
    for jar in sorted(glob.glob(os.path.join(a.mods, '*.jar'))):
        try:
            z = zipfile.ZipFile(jar)
        except zipfile.BadZipFile:
            continue
        for n in z.namelist():
            m = re.match(r'assets/([^/]+)/blockstates/([^/]+)\.json$', n)
            if not m or m[1] == 'minecraft':
                continue
            try:
                j = json.loads(z.read(n))
            except Exception:
                continue
            conds = list((j.get('variants') or {}).keys())
            for part in j.get('multipart') or []:
                w = part.get('when') or {}
                for c in (w.get('OR') or w.get('AND') or [w]):
                    conds.append(','.join(f'{k}={v}' for k, v in c.items()))
            p = {}
            for c in conds:
                for kv in filter(None, c.split(',')):
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        p.setdefault(k, set()).update(str(v).lower().split('|'))
            for k, vs in p.items():          # a multipart file only names the "true" side of a boolean
                if vs <= {'true', 'false'}:
                    vs.update(BOOL)
            props[f'{m[1]}:{m[2]}'] = {k: sorted(v) for k, v in sorted(p.items())}
    for b, extra in EXTRA.items():
        props.setdefault(b, {}).update(extra)
    out = os.path.join(HERE, 'block_props.json')
    json.dump(props, open(out, 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
    print(f'{len(props)} modded blocks -> {out}')


if __name__ == '__main__':
    main()
