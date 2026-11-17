"""Build the Quicreate Skyblock guide book (Modonomicon 1.20.1) and its progress advancements.

    python guide/book/build_book.py --resources src/main/resources

Reads guide/book/knowledge.json (from dump_knowledge.py), book_text.py, walkthrough_content.py and rewards.yaml.
Writes, all under the given resources folder:
  data/quicreate/modonomicon/books/skyblock/...      the book, its tabs and entries
  data/quicreate/modonomicon/multiblocks/*.json      multiblock previews
  data/quicreate/advancements/skyblock/*.json         one per main quest (progress + toasts)
  data/quicreate/advancements/side/...                one per side-path goal (+ reward)
  data/quicreate/advancements/book/*.json             gives the book on first join
  data/quicreate/functions/...                        book and reward functions
  data/quicreate/recipes/guide_book.json              craft a replacement book
  assets/quicreate/lang/en_us.json                    every text in the book (merged into the existing file)
  assets/quicreate/textures/gui/book/...              backgrounds and planet pictures (textures.py)
Old generated files are removed first, so a rebuild never leaves stale entries behind.
"""
import argparse, collections, html, importlib.util, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_text as T  # noqa: E402
import textures  # noqa: E402

NS = 'quicreate'
BOOK = 'skyblock'
BOOK_ID = f'{NS}:{BOOK}'
LANG_PREFIX = f'book.{NS}.{BOOK}'
WARN = []

# entry background (u = row, v = column) in modonomicon:textures/gui/entry_textures.png
BG_REQUIRED = (1, 0)     # grey square
BG_MILESTONE = (0, 1)    # gold star
BG_OPTIONAL = (1, 2)     # grey round
BG_READING = (0, 2)      # gold round
BG_LINK = (0, 0)         # gold square

COL_MACHINE = '1f4e8c'
COL_GOOD = '1e6b2a'
COL_WARN = '9b2a1a'
COL_DIM = '555555'


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ============================================================ text helpers
CHAR_W = {' ': 4, 'i': 2, 'l': 3, 't': 4, 'I': 4, 'f': 5, 'k': 5, '.': 2, ',': 2, ':': 2, ';': 2, "'": 2, '!': 2,
          '|': 2, '(': 5, ')': 5, '[': 4, ']': 4, '*': 5, '<': 5, '>': 5, '"': 5, '`': 3, '{': 5, '}': 5}
PAGE_W = 122           # a little under Modonomicon's 124 px so rounding never pushes a word over
LINES_TITLED = 10
LINES_PLAIN = 13
LINES_SPOTLIGHT = 6
LINES_ENTITY = 3
LINES_IMAGE = 3
LINES_MULTIBLOCK = 3
LINES_RECIPE = 3


def visible(md):
    """Text as rendered: link targets, colour codes and emphasis markers removed."""
    s = re.sub(r'\[#\]\([0-9a-fA-F]*\)', '', md)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    return s.replace('**', '').replace('++', '').replace('~~', '')


def text_width(s, bold=False):
    return sum(CHAR_W.get(c, 6) + (1 if bold else 0) for c in s)


def count_lines(md):
    """Lines a markdown block takes on a page (paragraphs separated by a blank line)."""
    total = 0
    paras = [p for p in md.split('\n\n')]
    for pi, para in enumerate(paras):
        if not para.strip():
            continue
        for raw in para.split('\n'):
            line = visible(raw.rstrip())
            indent = 0
            if re.match(r'^\s*([-*]|\d+\.)\s', line):
                indent = 10
                line = re.sub(r'^\s*([-*]|\d+\.)\s', '', line)
            words = line.split(' ')
            cur, n = 0, 1
            for w in words:
                ww = text_width(w) + (4 if cur else 0)
                if cur + ww > PAGE_W - indent and cur:
                    n += 1
                    cur = text_width(w)
                else:
                    cur += ww
            total += n
        if pi < len(paras) - 1:
            total += 1
    return total


def split_long(block, cap):
    """Split one paragraph that is longer than a page at sentence boundaries."""
    if count_lines(block) <= cap:
        return [block]
    if '\n' in block.strip():
        # a list or several lines: split between lines, keep the heading line with the first part
        lines = [l for l in block.split('\n') if l.strip()]
        out, cur = [], []
        for l in lines:
            cand = '\n'.join(cur + [l]) + '\n\n'
            if cur and count_lines(cand) > cap:
                out.append('\n'.join(cur) + '\n\n')
                cur = [l]
            else:
                cur.append(l)
        if cur:
            out.append('\n'.join(cur) + '\n\n')
        return out
    parts = re.split(r'(?<=[.!?])\s+', block)
    out, cur = [], ''
    for p in parts:
        cand = (cur + ' ' + p).strip()
        if cur and count_lines(cand) > cap:
            out.append(cur)
            cur = p
        else:
            cur = cand
    if cur:
        out.append(cur)
    return out


def paginate(blocks, first_cap=LINES_TITLED, cap=LINES_PLAIN):
    """Greedily pack paragraphs onto pages. Returns a list of page texts."""
    pages, cur, used = [], [], 0
    limit = first_cap
    flat = []
    for b in blocks:
        if b and b.strip():
            flat += split_long(b.strip(), min(first_cap, cap))
    for b in flat:
        need = count_lines(b) + (1 if cur else 0)
        if cur and used + need > limit:
            pages.append('\n\n'.join(cur))
            cur, used, limit = [], 0, cap
            need = count_lines(b)
        cur.append(b)
        used += need
    if cur:
        pages.append('\n\n'.join(cur))
    return pages


def html_to_md(s):
    s = re.sub(r'</?b>', '**', s)
    s = re.sub(r'</?i>', '*', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s)


def pct(p):
    if p is None:
        return ''
    p *= 100
    if p >= 99.95:
        return '100%'
    if p >= 10:
        return f'{p:.0f}%'
    if p >= 1:
        return f'{p:.1f}'.rstrip('0').rstrip('.') + '%'
    return f'{p:.2f}'.rstrip('0').rstrip('.') + '%'


# ============================================================ the builder
class Builder:
    def __init__(self, res, knowledge, walk, rewards):
        self.res = res
        self.k = knowledge
        self.walk = walk
        self.rewards = rewards
        self.lang = {}
        self.files = {}           # relative path -> json/text
        self.Q = {q['id']: q for q in knowledge['quests']}
        self.names = knowledge['names']
        self.known = set(knowledge['known_items'])
        self.obtainable = set(knowledge['obtainable'])
        self.entities = set(knowledge['entities'])
        self.qcat = {}            # quest id -> category id
        self.entry_of = {}        # quest id -> entry id
        self.children = collections.defaultdict(list)
        self.how = {}             # step number -> curated "how to get it"
        for ch in walk.CHAPTERS:
            for _sec, _paras, rows in ch['sections']:
                for (n, _name, _ask, how) in rows:
                    self.how[n] = how
        self.step_q = {q['step']: q['id'] for q in knowledge['quests']}
        self.notes = {}

    # ---------------------------------------------------- basics
    def tr(self, key, text):
        k = f'{LANG_PREFIX}.{key}'
        self.lang[k] = text
        return k

    def name(self, ident):
        if ident in self.names:
            return self.names[ident]
        return ident.split(':')[-1].replace('_', ' ').title()

    def item_ok(self, it, where):
        if it in self.known:
            return True
        WARN.append(f'unknown item {it} ({where})')
        return False

    def put(self, rel, data):
        self.files[rel] = data

    def entry_link(self, qid, label=None):
        eid = self.entry_of.get(qid)
        title = label or (self.Q[qid]['title'] if qid in self.Q else qid)
        if not eid:
            return f'**{title}**'
        return f'[{title}](entry://{BOOK_ID}/{eid.split(":", 1)[1]})'

    def md(self, text):
        """Book markdown: [[ns:item]] and [[#quest]] links, html from the walkthrough, quest numbers to links."""
        text = html_to_md(text)

        def item(m):
            it = m.group(1)
            self.item_ok(it, 'text link')
            return f'[{self.name(it)}](item://{it})'
        text = re.sub(r'\[\[([a-z0-9_]+:[a-z0-9_/.]+)\]\]', item, text)
        text = re.sub(r'\[\[#([a-z0-9_]+)\]\]', lambda m: self.entry_link(m.group(1)), text)

        def num(m):
            n = int(m.group(1))
            q = self.step_q.get(n)
            return f' ({self.entry_link(q)})' if q else ''
        text = re.sub(r'Quest #(\d+) \(([^)]+)\)', lambda m: self.entry_link(self.step_q.get(int(m.group(1)), ''), m.group(2))
                      if self.step_q.get(int(m.group(1))) else m.group(2), text)
        text = re.sub(r' \(#(\d+)\)', num, text)
        text = re.sub(r'#(\d+)–#(\d+)', '', text)
        text = text.replace('the Reference PDF', 'the Field Guide').replace('Reference PDF', 'Field Guide')
        text = text.replace('in the quest book', 'in this book').replace('the quest book', 'this book')
        return text

    def ilink(self, it, count=None):
        nm = self.name(it)
        c = f'{count}x ' if count and count > 1 else ''
        return f'{c}[{nm}](item://{it})'

    # ---------------------------------------------------- pages
    def text_pages(self, key, title, blocks, cond=None, anchor=None):
        out = []
        for i, t in enumerate(paginate(blocks)):
            p = {'type': 'modonomicon:text', 'text': self.tr(f'{key}.p{i}', t)}
            if i == 0 and title:
                p['title'] = self.tr(f'{key}.title', title)
            if cond:
                p['condition'] = cond
            if anchor and i == 0:
                p['anchor'] = anchor
            out.append(p)
        return out

    def page_spotlight(self, key, item, title, text, cond=None, tag=None):
        ing = {'tag': tag} if tag else {'item': item}
        p = {'type': 'modonomicon:spotlight', 'item': ing, 'title': self.tr(f'{key}.title', title),
             'text': self.tr(f'{key}.text', text)}
        if cond:
            p['condition'] = cond
        return p

    def custom_pages(self, key, spec):
        """Pages from the hand-written forms in book_text.py."""
        out = []
        for i, pg in enumerate(spec):
            k = f'{key}.c{i}'
            if pg[0] == '@multiblock':
                _, mid, nm, txt = pg
                out.append({'type': 'modonomicon:multiblock', 'multiblock_id': mid,
                            'multiblock_name': self.tr(f'{k}.name', nm), 'text': self.tr(f'{k}.text', self.md(txt)),
                            'show_visualize_button': True})
            elif pg[0] == '@image':
                _, tex, ttl, txt = pg
                out.append({'type': 'modonomicon:image', 'images': [tex], 'title': self.tr(f'{k}.title', ttl),
                            'text': self.tr(f'{k}.text', self.md(txt)), 'border': True})
            elif pg[0] == '@entity':
                _, eid, txt = pg
                out.append({'type': 'modonomicon:entity', 'entity_id': eid, 'text': self.tr(f'{k}.text', self.md(txt))})
            elif pg[0] == '@spotlight':
                _, it, ttl, txt = pg
                out.append(self.page_spotlight(k, it, ttl, self.md(txt)))
            else:
                ttl, txt = pg
                out += self.text_pages(k, ttl, [self.md(t) for t in txt.split('\n\n')] if '\n- ' not in txt and '\n1.' not in txt
                                       else [self.md(txt)])
        return out

    # ---------------------------------------------------- conditions
    def adv_cond(self, adv_id, tooltip):
        return {'type': 'modonomicon:advancement', 'advancement_id': adv_id, 'tooltip': tooltip}

    def all_of(self, conds):
        conds = [c for c in conds if c]
        if not conds:
            return None
        if len(conds) == 1:
            return conds[0]
        return {'type': 'modonomicon:and', 'children': conds}

    def any_of(self, conds):
        conds = [c for c in conds if c]
        if len(conds) == 1:
            return conds[0]
        return {'type': 'modonomicon:or', 'children': conds}

    def quest_adv(self, qid):
        return f'{NS}:skyblock/{qid}'

    def quest_cond(self, qid, key):
        q = self.Q[qid]
        if self.is_reading(qid):
            return None       # reading pages never lock anything (entry_read fails server-side in 1.79.3)
        return self.adv_cond(self.quest_adv(qid), self.tr(f'tooltip.{qid}', f'Finish: {q["title"]}'))

    def is_reading(self, qid):
        q = self.Q[qid]
        return all(t['type'] == 'heracles:check' for t in q['tasks']) and qid != 'quicreate_complete'

    # ---------------------------------------------------- advancements
    def criterion_for_task(self, t):
        typ = t['type']
        if typ == 'heracles:item':
            it = t['item']
            n = int(t.get('amount', 1))
            cond = {'count': n}
            if it.startswith('#'):
                cond['tag'] = it[1:]
            else:
                cond['item'] = it
                self.item_ok(it, 'quest task')
            return {'trigger': f'{NS}:has_items', 'conditions': cond}
        if typ == 'heracles:kill_entity':
            return {'trigger': 'minecraft:player_killed_entity',
                    'conditions': {'entity': {'type': t['entity']['type']}}}
        if typ == 'heracles:structure':
            return {'trigger': 'minecraft:location', 'conditions': {'player': {'location': {'structure': t['structures']}}}}
        if typ == 'heracles:changed_dimension':
            return {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': t['to']}}
        return None

    def display(self, icon, title, desc, frame='task', toast=True, chat=False, hidden=True, background=None):
        d = {'icon': {'item': icon}, 'title': {'text': title}, 'description': {'text': desc}, 'frame': frame,
             'show_toast': toast, 'announce_to_chat': chat, 'hidden': hidden}
        if background:
            d['background'] = background
        return d

    def task_text(self, t, plain=False):
        typ = t['type']
        if typ == 'heracles:item':
            it = t['item']
            n = int(t.get('amount', 1))
            if it.startswith('#'):
                q_tags = t.get('_tag_items') or []
                nm = t.get('title') or ('any ' + it[1:].split(':')[-1].replace('_', ' ').rstrip('s'))
                return f'{n} {nm}' if plain else f'**{n}** {nm}'
            return f'{n} {self.name(it)}' if plain else f'**{n}** {self.ilink(it)}'
        if typ == 'heracles:kill_entity':
            e = t['entity']['type']
            return f'Defeat {self.name(e)}' if plain else f'Defeat **{self.name(e)}**'
        if typ == 'heracles:structure':
            s = t['structures']
            return f'Find the {self.name(s)}' if plain else f'Find the **{self.name(s)}**'
        if typ == 'heracles:changed_dimension':
            return f'Travel to {self.name(t["to"])}' if plain else f'Travel to **{self.name(t["to"])}**'
        return t.get('title') or 'Read this'

    def write_quest_adv(self, q, parent_adv):
        crit = {}
        for i, t in enumerate(q['tasks']):
            c = self.criterion_for_task(t)
            if c:
                crit[f'task{i}'] = c
        if q['id'] == 'quicreate_complete':
            crit = {'casing': {'trigger': f'{NS}:has_items', 'conditions': {'item': 'quicreate:creative_casing', 'count': 1}},
                    'motor': {'trigger': f'{NS}:has_items', 'conditions': {'item': 'create:creative_motor', 'count': 1}},
                    'cake': {'trigger': f'{NS}:has_items', 'conditions': {'item': 'create:creative_blaze_cake', 'count': 1}},
                    'dragon': {'trigger': 'minecraft:player_killed_entity',
                               'conditions': {'entity': {'type': 'minecraft:ender_dragon'}}}}
        if not crit:
            return None
        ms = q['id'] in T.MILESTONES
        frame = 'challenge' if q['id'] in ('quicreate_complete', 'ender_dragon') else ('goal' if ms else 'task')
        icon = q.get('icon') or 'minecraft:book'
        desc = q.get('subtitle') or ', '.join(self.task_text(t, True) for t in q['tasks'])
        adv = {'parent': parent_adv, 'display': self.display(icon, q['title'], desc, frame, True, ms),
               'criteria': crit, 'requirements': [[k] for k in crit]}
        self.put(f'data/{NS}/advancements/skyblock/{q["id"]}.json', adv)
        return self.quest_adv(q['id'])

    # ---------------------------------------------------- main chapters
    # ------------------------------------------------ layout
    # Modonomicon draws a parent -> child line as: horizontal along the parent's row to the child's column, then
    # vertical into the child; "line_reversed" goes vertical first. Straight when they share a row or column.
    FIT_W = 26          # grid cells: a tab should fit on one screen when zoomed out (Moon was ~33 x 16)
    FIT_H = 12

    @staticmethod
    def reverse_broken(p, c):
        """Modonomicon 1.79.3 puts the corner arc of a reversed line in the wrong place when the child is two or more
        cells left of AND below its parent (renderLargeCurvesReversed draws it next to the parent). Never use it."""
        return c[0] <= p[0] - 2 and c[1] >= p[1] + 2

    @staticmethod
    def path_cells(p, c, reverse):
        (px, py), (cx, cy) = p, c
        sx = 1 if cx > px else -1
        sy = 1 if cy > py else -1
        cells = []
        if not reverse:
            cells += [(x, py) for x in range(px + sx, cx + sx, sx)] if cx != px else []
            cells += [(cx, y) for y in range(py + sy, cy, sy)] if cy != py else []
        else:
            cells += [(px, y) for y in range(py + sy, cy + sy, sy)] if cy != py else []
            cells += [(x, cy) for x in range(px + sx, cx, sx)] if cx != px else []
        return [c2 for c2 in cells if c2 != c]

    def ancestors(self, qid, memo):
        """Ancestors reachable through steps in the same tab (what the drawn lines can show)."""
        if qid in memo:
            return memo[qid]
        memo[qid] = set()
        out = set()
        for p in self.parents_of(qid):
            if self.qcat.get(p) != self.qcat.get(qid):
                continue
            out.add(p)
            out |= self.ancestors(p, memo)
        memo[qid] = out
        return out

    def line_parents(self, qid, memo):
        """Parents worth a line: drop a parent that another parent already depends on (it is implied)."""
        ps = self.parents_of(qid)
        keep = []
        for p in ps:
            if any(p in self.ancestors(o, memo) for o in ps if o != p):
                continue
            keep.append(p)
        return keep

    def layout(self, quests, cat):
        moved_in = [q for q in quests if q['id'] in T.GROUP_OVERRIDE]
        quests = [q for q in quests if q['id'] not in T.GROUP_OVERRIDE]
        if not quests:   # a tab made only of moved steps (Electricity): lay them out from their old positions
            quests, moved_in = moved_in, []
        xs = [q['pos'][0] for q in quests]
        ys = [q['pos'][1] for q in quests]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        dx = max(12.0, (max(xs) - min(xs)) / self.FIT_W)
        dy = max(12.0, (max(ys) - min(ys)) / self.FIT_H)
        pos, used = {}, set()
        for q in sorted(quests, key=lambda q: q['step']):
            p = (round((q['pos'][0] - cx) / dx), round((q['pos'][1] - cy) / dy))
            k = 0
            while p in used:
                k += 1
                p = (p[0] + (k % 2), p[1] + (1 - k % 2))
            used.add(p)
            pos[q['id']] = p
        for q in moved_in:
            near = [pos[p] for p in self.parents_of(q['id']) if p in pos]
            bx = max(p[0] for p in near) if near else max(p[0] for p in pos.values())
            by = max(p[1] for p in near) if near else max(p[1] for p in pos.values())
            cand = (bx, by + 1)
            for k in range(60):
                if cand not in pos.values():
                    break
                cand = (bx + (k % 4), by + 1 + k // 4)
            pos[q['id']] = cand
        quests = quests + moved_in
        memo = {}
        ids = {q['id'] for q in quests}
        edges = [(p, q['id']) for q in quests for p in self.line_parents(q['id'], memo)
                 if p in ids and self.qcat.get(p) == cat]
        rev = {}
        x_lo, x_hi = min(p[0] for p in pos.values()) - 1, max(p[0] for p in pos.values()) + 1
        y_lo, y_hi = min(p[1] for p in pos.values()) - 1, max(p[1] for p in pos.values()) + 1
        moves = collections.Counter()

        def occupied(cell, skip):
            return any(v == cell for k2, v in pos.items() if k2 not in skip)

        def blocked(e, r):
            return any(occupied(c2, set(e)) for c2 in self.path_cells(pos[e[0]], pos[e[1]], r))

        for _round in range(40):
            # cells used by the lines so far, to keep parallel lines apart
            moved = False
            line_use = collections.Counter()
            for e in edges:
                choices = (False,) if self.reverse_broken(pos[e[0]], pos[e[1]]) else (False, True)
                opts = sorted(choices, key=lambda r: (blocked(e, r), sum(line_use[c2] for c2 in
                              self.path_cells(pos[e[0]], pos[e[1]], r))))
                r = opts[0]
                rev[e] = r
                for c2 in self.path_cells(pos[e[0]], pos[e[1]], r):
                    line_use[c2] += 1
            for e in edges:
                if blocked(e, rev[e]) and moves[e[1]] < 3:
                    # move the child one cell (sideways first) to a free spot that clears its lines
                    child = e[1]
                    x0, y0 = pos[child]
                    best = None
                    for ddx, ddy in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (2, 0)):
                        cand = (x0 + ddx, y0 + ddy)
                        if cand in pos.values() or not (x_lo <= cand[0] <= x_hi and y_lo <= cand[1] <= y_hi):
                            continue
                        pos[child] = cand
                        bad = sum(1 for f in edges if child in f and blocked(f, False) and blocked(f, True))
                        bad += sum(1 for f in edges if child not in f and any(c2 == cand for c2 in
                                   self.path_cells(pos[f[0]], pos[f[1]], rev.get(f, False))))
                        if best is None or bad < best[0]:
                            best = (bad, cand)
                        pos[child] = (x0, y0)
                    if best and best[0] < 1 + sum(1 for f in edges if child in f and blocked(f, rev[f])):
                        pos[child] = best[1]
                        moves[child] += 1
                        moved = True
            if not moved:
                break
        self.line_info = getattr(self, 'line_info', {})
        for e in edges:
            self.line_info[e] = rev.get(e, False)
        self.line_edges = getattr(self, 'line_edges', set()) | set(edges)
        return pos, set(pos.values())

    def parents_of(self, qid):
        q = self.Q[qid]
        ps = list(q['deps']) + [p for p in T.EXTRA_PARENTS.get(qid, []) if p not in q['deps']]
        return [p for p in ps if p in self.Q and p not in T.MOVED_TO_FIELD_GUIDE]

    def plan_main(self):
        groups = {c[0]: c for c in T.CHAPTERS}
        groups[T.SIDE_CARDS_GROUP] = (T.SIDE_CARDS_GROUP, 'cards', 'Cards & Mobs', 'cards:common_card_pack', 'cards', False,
                                      'cards')
        for q in self.k['quests']:
            if q['id'] in T.MOVED_TO_FIELD_GUIDE:
                self.qcat[q['id']] = 'field_guide'
                self.entry_of[q['id']] = f'{NS}:field_guide/{q["id"]}'
                continue
            cat = groups[T.GROUP_OVERRIDE.get(q['id'], q['group'])][1]
            self.qcat[q['id']] = cat
            self.entry_of[q['id']] = f'{NS}:{cat}/{q["id"]}'
        for q in self.k['quests']:
            for p in self.parents_of(q['id']):
                self.children[p].append(q['id'])

    def chapter_gate(self, cat, quests):
        """The quest after which something in this chapter can be started (earliest by step order)."""
        best = None
        for q in quests:
            ext = [p for p in self.parents_of(q['id']) if self.qcat.get(p) != cat]
            loc = [p for p in self.parents_of(q['id']) if self.qcat.get(p) == cat]
            if loc:
                continue
            if not ext:
                continue
            cand = max(ext, key=lambda p: self.Q[p]['step'])
            if best is None or self.Q[cand]['step'] < self.Q[best]['step']:
                best = cand
        return best

    def build_chapter(self, group, cat, short, icon, bgname, starry, walk_key, sort):
        quests = [q for q in self.k['quests'] if T.GROUP_OVERRIDE.get(q['id'], q['group']) == group
                  and q['id'] not in T.MOVED_TO_FIELD_GUIDE]
        pos, used = self.layout(quests, cat)
        gate = T.CHAPTER_GATES.get(cat) or (self.chapter_gate(cat, quests) if sort > 1 else None)
        cat_json = {'name': self.tr(f'cat.{cat}', short), 'icon': icon, 'sort_number': sort}
        self.background(cat_json, bgname, starry)
        if gate and not T.ALL_TABS_VISIBLE:
            cat_json['condition'] = self.adv_cond(self.quest_adv(gate),
                                                  self.tr(f'cat.{cat}.gate', f'Unlocks after: {self.Q[gate]["title"]}'))
        if cat == 'cards':
            cat_json['show_category_button'] = False
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/categories/{cat}.json', cat_json)
        self.cat_gate = getattr(self, 'cat_gate', {})
        self.cat_gate[cat] = gate

        # chapter intro: top-left corner
        minx = min(p[0] for p in used)
        miny = min(p[1] for p in used)
        ip = (minx - 1, miny - 1)
        while ip in used or any(ip in self.path_cells(pos[a], pos[b], r) for (a, b), r in self.line_info.items()
                                if a in pos and b in pos):
            ip = (ip[0], ip[1] + 1)
        self.chapter_intro(cat, short, icon, walk_key, ip, quests)

        for q in quests:
            self.quest_entry(q, cat, pos[q['id']])

    def chapter_intro(self, cat, short, icon, walk_key, xy, quests):
        ch = next((c for c in self.walk.CHAPTERS if c['key'] == walk_key), None)
        key = f'{cat}.intro'
        pages = []
        if ch:
            label = re.sub(r'\s*·\s*steps.*$', '', ch['label'])
            blocks = [f'*{label}*'] + [self.md(p) for p in ch['intro']]
            pages += self.text_pages(f'{key}.overview', ch['title'], blocks)
            if ch.get('tips'):
                tips = [self.md(t) for t in ch['tips'] if 'no arrows' not in t]
                pages += self.text_pages(f'{key}.tips', 'Tips', ['\n'.join(f'- {t}' for t in tips) + '\n\n'])
            mat = self.materials.get(cat)
            if mat:
                pages += self.text_pages(f'{key}.mat', 'Materials', [
                    'Roughly what this chapter costs, in raw materials:', mat,
                    f'[#]({COL_DIM})Each step counted on its own, so treat it as an upper bound.[#]()'])
            for si, (sec, paras, rows) in enumerate(ch['sections']):
                links = []
                for (n, _nm, _ask, _how) in rows:
                    qid = self.step_q.get(n)
                    if qid and qid not in T.MOVED_TO_FIELD_GUIDE and qid not in T.HIDDEN_UNTIL_DONE:
                        links.append(f'- {self.entry_link(qid)}')
                blocks = [self.md(p) for p in paras]
                if links:
                    blocks.append('\n'.join(links) + '\n\n')
                pages += self.text_pages(f'{key}.s{si}', sec, blocks)
        else:
            pages += self.text_pages(f'{key}.overview', short,
                                     [self.md(t) for t in T.CHAPTER_INTRO.get(cat, ['The steps of this chapter.'])])
        e = {'category': f'{NS}:{cat}', 'name': self.tr(f'{key}.name', f'{short}: start here'),
             'description': self.tr(f'{key}.desc', 'Overview, tips and materials'), 'icon': 'minecraft:writable_book',
             'x': xy[0], 'y': xy[1], 'background_u_index': BG_MILESTONE[0], 'background_v_index': BG_MILESTONE[1],
             'pages': pages}
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{cat}/intro.json', e)

    def quest_entry(self, q, cat, xy):
        qid = q['id']
        key = f'{cat}.{qid}'
        reading = self.is_reading(qid)
        parents = self.parents_of(qid)
        local_parents = [p for p in parents if self.qcat.get(p) == cat]
        conds = [self.quest_cond(p, key) for p in parents]
        cond = self.all_of(conds)

        # tracker advancement
        adv_parent = None
        for p in parents:
            if not self.is_reading(p):
                adv_parent = self.quest_adv(p)
                break
        my_adv = None if reading else self.write_quest_adv(q, adv_parent or f'{NS}:skyblock/root')

        if qid in T.HIDDEN_UNTIL_DONE:
            bg = BG_OPTIONAL
        elif reading:
            bg = BG_READING
        elif qid in T.MILESTONES:
            bg = BG_MILESTONE
        elif qid in T.OPTIONAL:
            bg = BG_OPTIONAL
        else:
            bg = BG_REQUIRED

        pages = self.quest_pages(q, key, my_adv)
        icon = q.get('icon') or 'minecraft:book'
        if not self.item_ok(icon, f'icon of {qid}'):
            icon = 'minecraft:book'
        desc = q.get('subtitle') or ', '.join(self.task_text(t, True) for t in q['tasks'])
        if qid in T.OPTIONAL:
            desc = ('Optional. ' + desc) if not desc.lower().startswith('optional') else desc
        e = {'category': f'{NS}:{cat}', 'name': self.tr(f'{key}.name', q['title']),
             'description': self.tr(f'{key}.desc', desc), 'icon': icon, 'x': xy[0], 'y': xy[1],
             'background_u_index': bg[0], 'background_v_index': bg[1], 'pages': pages}
        if local_parents:
            e['parents'] = []
            for p in local_parents:
                par = {'entry': self.entry_of[p]}
                if (p, qid) not in self.line_edges:
                    par['line_enabled'] = False          # implied by another parent: no line, still a parent
                elif self.line_info.get((p, qid)):
                    par['line_reversed'] = True
                e['parents'].append(par)
        if qid in T.HIDDEN_UNTIL_DONE:
            e['condition'] = self.adv_cond(my_adv, self.tr(f'{key}.secret', '???'))
            e['hide_while_locked'] = True
        elif cond:
            e['condition'] = cond
        if qid in T.HIDDEN_UNTIL_UNLOCKED and cond:
            e['hide_while_locked'] = True
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{cat}/{qid}.json', e)

    def quest_pages(self, q, key, my_adv):
        qid = q['id']
        pages = []
        sub = q.get('subtitle') or ''
        desc = [self.md(x) for x in q.get('desc') or [] if x and x.strip()]
        how = self.how.get(q['step'])
        if self.is_reading(qid):
            blocks = ([f'*{self.md(sub)}*'] if sub else []) + desc
            if not desc and how:
                blocks.append(self.md(how))
            return self.text_pages(f'{key}.read', q['title'], blocks or ['(Nothing to do here: just read.)'])

        goal_lines = [self.task_text(t) for t in q['tasks']]
        first = q['tasks'][0]
        goal = ('\n'.join(f'- {g}' for g in goal_lines) + '\n\n') if len(goal_lines) > 1 else goal_lines[0]
        spot = (f'*{self.md(sub)}*\n\n' if sub else '') + f'**Goal:** {goal}' if len(goal_lines) == 1 else \
            (f'*{self.md(sub)}*\n\n' if sub else '') + '**Goal:**\n' + goal
        overflow = []
        if count_lines(spot) > LINES_SPOTLIGHT:
            short_sub = f'*{self.md(sub)}*\n\n' if sub and count_lines(f'*{self.md(sub)}*') <= 2 else ''
            if count_lines(short_sub + f'**Goal:**\n{goal}') <= LINES_SPOTLIGHT:
                spot = short_sub + f'**Goal:**\n{goal}'
            else:
                spot = short_sub + f'**Goal:** {len(goal_lines)} things, listed on the next page.'
                overflow.append('**Goal:**\n' + goal)
            if sub and not short_sub:
                overflow.insert(0, f'*{self.md(sub)}*')
        t0 = first['type']
        if t0 == 'heracles:kill_entity':
            eid = first['entity']['type']
            txt = spot if count_lines(spot) <= LINES_ENTITY else f'**Goal:** Defeat {self.name(eid)}'
            if txt != spot:
                overflow.insert(0, spot)
            pages.append({'type': 'modonomicon:entity', 'entity_id': eid, 'name': self.tr(f'{key}.ename', q['title']),
                          'text': self.tr(f'{key}.etext', txt), 'scale': 0.8})
        elif t0 == 'heracles:changed_dimension':
            dim = first['to'].split(':')[-1]
            img = {'moon': 'moon', 'mars': 'mars', 'venus': 'venus', 'mercury': 'mercury', 'glacio': 'glacio'}.get(dim)
            if img:
                txt = spot if count_lines(spot) <= LINES_IMAGE else f'**Goal:** Travel to {self.name(first["to"])}'
                if txt != spot:
                    overflow.insert(0, spot)
                pages.append({'type': 'modonomicon:image', 'images': [f'{NS}:textures/gui/book/planet/{img}.png'],
                              'title': self.tr(f'{key}.ititle', q['title']), 'text': self.tr(f'{key}.itext', txt),
                              'border': True})
            else:
                pages.append(self.page_spotlight(f'{key}.spot', q.get('icon') or 'minecraft:ender_eye', q['title'], spot))
        else:
            item = q.get('icon')
            tag = None
            if t0 == 'heracles:item':
                if first['item'].startswith('#'):
                    tag = first['item'][1:]
                else:
                    item = first['item']
            if not item or (not tag and not self.item_ok(item, f'spotlight {qid}')):
                item = 'minecraft:book'
            pages.append(self.page_spotlight(f'{key}.spot', item, q['title'], spot, tag=tag))

        # how to get it
        blocks = list(overflow)
        if how:
            blocks.append(f'[#]({COL_GOOD})**How:**[#]() ' + self.md(how) + '.')
        blocks += desc
        note = self.notes.get(qid)
        if note:
            blocks.append(self.md(note))
        for t in q['tasks']:
            if t['type'] != 'heracles:item' or t['item'].startswith('#'):
                continue
            info = self.k['items'].get(t['item'])
            if info:
                blocks += self.source_blocks(t['item'], info, show_name=len(q['tasks']) > 1)
        for t in q['tasks']:
            if t['type'] == 'heracles:kill_entity':
                blocks += self.boss_blocks(t['entity']['type'])
            if t['type'] == 'heracles:structure':
                blocks += self.structure_blocks(t['structures'])
        if blocks:
            pages += self.text_pages(f'{key}.how', 'How to get it', blocks)

        # a real crafting / smelting grid when there is one
        if t0 == 'heracles:item' and not first['item'].startswith('#'):
            rp = self.recipe_page(first['item'], key)
            if rp:
                pages.append(rp)

        # a 3D build preview
        mb = T.QUEST_MULTIBLOCKS.get(qid)
        if mb:
            pages.append({'type': 'modonomicon:multiblock', 'multiblock_id': f'{NS}:{mb[0]}',
                          'multiblock_name': self.tr(f'{key}.mbname', mb[1]), 'text': self.tr(f'{key}.mbtext', self.md(mb[2])),
                          'show_visualize_button': True})

        # completed page, only shown once the step is done
        if my_adv:
            nxt = [c for c in self.children.get(qid, []) if c not in T.MOVED_TO_FIELD_GUIDE]
            lines = [f'[#]({COL_GOOD})**Completed!**[#]()']
            if nxt:
                lines.append('This opened up:')
                lines.append('\n'.join(f'- {self.entry_link(c)}' for c in nxt[:8]) + '\n\n')
            elif qid not in T.OPTIONAL:
                lines.append('Nothing new depends on this one, but the chapter needs it.')
            done = self.adv_cond(my_adv, self.tr(f'{key}.donetip', 'Done'))
            pages += self.text_pages(f'{key}.done', 'Done', lines, cond=done)
        return pages

    def recipe_page(self, item, key):
        recs = self.k['page_recipes'].get(item) or []
        types = {'minecraft:crafting_shaped': 'modonomicon:crafting_recipe',
                 'minecraft:crafting_shapeless': 'modonomicon:crafting_recipe',
                 'minecraft:smelting': 'modonomicon:smelting_recipe', 'minecraft:blasting': 'modonomicon:blasting_recipe',
                 'minecraft:smithing_transform': 'modonomicon:smithing_recipe'}
        info = self.k['items'].get(item) or {}
        best = [r['id'] for r in info.get('recipes', [])]
        recs = sorted(recs, key=lambda r: (0 if r['id'] in best else 1, r['id']))
        for r in recs:
            if r['type'] in types:
                p = {'type': types[r['type']], 'recipe_id_1': r['id'],
                     'text': self.tr(f'{key}.rtext', f'[#]({COL_DIM})Also in JEI: press U on any item.[#]()')}
                same = [x for x in recs if x['type'] == r['type'] and x['id'] != r['id']]
                if same:
                    p['recipe_id_2'] = same[0]['id']
                return p
        return None

    def ing_text(self, g):
        if g.get('fluid'):
            amt = g.get('amount', 0)
            a = f'{amt // 1000} B' if amt >= 1000 and amt % 1000 == 0 else f'{amt} mB'
            return f'{a} {g["name"]}'
        c = g.get('count', 1)
        if g.get('tag'):
            return f'{c}x {g["name"]}' if c > 1 else g['name']
        it = g.get('item')
        if it:
            return self.ilink(it, c)
        return g.get('name', '?')

    def recipe_text(self, r):
        mach = f'[#]({COL_MACHINE})**{r["machine"]}**[#]()'
        extra = f' ({", ".join(r["extra"])})' if r.get('extra') else ''
        ins = ', '.join(self.ing_text(g) for g in r['inputs'][:6])
        out = r['outputs'][0] if r['outputs'] else None
        oc = f' gives {out["count"]}' if out and out.get('count', 1) > 1 else ''
        s = f'{mach}{extra}: {ins}{oc}.'
        if r['type'] == 'create:sequenced_assembly' and r.get('steps'):
            steps = ' > '.join(st['machine'].split(' (')[0].replace('Mechanical ', '') for st in r['steps'])
            s += f' Steps: {steps}, {r.get("loops", 1)} loop{"s" if r.get("loops", 1) != 1 else ""}.'
        return s

    def source_blocks(self, item, info, show_name=False):
        out = []
        head = f'**{self.name(item)}**: ' if show_name else ''
        g = info.get('gather') or []
        if g:
            lines = []
            for x in g[:4]:
                if x['kind'] == 'sift':
                    wl = ' (waterlogged)' if x['waterlogged'] else ''
                    lines.append(f'- Sift {x["input"]}, {x["mesh_name"]}{wl}: [#]({COL_GOOD})**{pct(x["chance"])}**[#]()')
                else:
                    cat = x.get('catalyst_name')
                    lines.append(f'- Extruder' + (f', {cat} below' if cat else ''))
            out.append(head + 'Gather it:\n' + '\n'.join(lines) + '\n\n')
            head = ''
        nat = info.get('natural') or []
        if nat:
            out.append(head + 'Found:\n' + '\n'.join(f'- {self.md(n)}' for n in nat[:3]) + '\n\n')
            head = ''
        recs = info.get('recipes') or []
        if recs:
            out.append(head + ('Make it: ' if g or nat else '') + self.recipe_text(recs[0]))
            if info.get('more_recipes') or len(recs) > 1:
                out.append(f'[#]({COL_DIM})More recipes in JEI.[#]()')
        if not (g or nat or recs) and not info.get('has_source'):
            out.append(f'[#]({COL_WARN})No source found in the pack files.[#]()')
        return out

    def boss_blocks(self, eid):
        b = next((x for x in self.k['bosses'] if x['entity'] == eid), None)
        if not b or not b['drops']:
            return []
        drops = '\n'.join(f'- {self.ilink(d["item"])} {pct(d["chance"])}' for d in b['drops'][:5]
                          if d['item'] in self.known)
        return ['Drops:\n' + drops + '\n\n'] if drops else []

    def structure_blocks(self, sid):
        for key, p in self.k['planets'].items():
            for s in p['structures']:
                if s['id'] == sid:
                    biomes = ', '.join(self.name(b) for b in s['biomes'][:4])
                    out = [f'On **{p["name"]}**, in: {biomes}.']
                    mobs = [m for m in s['mobs'] if m in self.entities][:5]
                    if mobs:
                        out.append('Inside: ' + ', '.join(self.name(m) for m in mobs) + '.')
                    return out
        return []

    # ---------------------------------------------------- backgrounds
    # tabs drawn from block textures at runtime by the mod (client/BookBackgrounds.java)
    TILED = {'sky': 'water', 'sifting': 'sand', 'new_age': 'iron_block', 'electricity': 'copper_block', 'improvements': 'steel_block',
             'moon': 'moon_stone', 'mars': 'mars_stone', 'venus': 'venus_stone', 'glacio': 'glacio_stone',
             'side_paths': 'dark_oak_planks', 'builders': 'stone_bricks', 'explorer': 'moss_block',
             'bestiary': 'mud_bricks', 'workshop': 'andesite_casing', 'kitchen': 'hay_block', 'cards': 'green_wool'}

    def background(self, cat_json, bgname, starry):
        if bgname == 'field':
            cat_json['background'] = 'modonomicon:textures/gui/dark_slate_seamless.png'
            return
        if bgname in self.TILED:
            cat_json['background'] = f'{NS}:textures/gui/book/tiled/{self.TILED[bgname]}.png'
            return
        base = f'{NS}:textures/gui/book/background/{bgname}.png'
        if starry:
            cat_json['background_parallax_layers'] = [
                {'background': base, 'speed': 0.7, 'vanish': -1},
                {'background': f'{NS}:textures/gui/book/background/stars_far.png', 'speed': 1.0, 'vanish': -1},
                {'background': f'{NS}:textures/gui/book/background/stars_near.png', 'speed': 1.3, 'vanish': 0.6}]
        else:
            cat_json['background'] = base

    # ---------------------------------------------------- field guide
    def build_field_guide(self):
        cat = 'field_guide'
        cj = {'name': self.tr('cat.field_guide', 'Field Guide'), 'icon': 'minecraft:writable_book', 'sort_number': 0}
        self.background(cj, 'field', False)
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/categories/{cat}.json', cj)
        for f in T.FIELD:
            x = f['col'] * 3 - 7
            y = f['row'] * 2 - 5
            key = f'field.{f["id"]}'
            if f.get('quest'):
                q = self.Q[f['quest']]
                title, icon = q['title'], q.get('icon') or 'minecraft:book'
                blocks = ([f'*{self.md(q["subtitle"])}*'] if q.get('subtitle') else []) + \
                         [self.md(x2) for x2 in q.get('desc') or [] if x2 and x2.strip()]
                pages = self.text_pages(f'{key}.read', title, blocks or [title])
            elif f.get('planet'):
                title, icon, pages = self.planet_profile(f['planet'], key)
            else:
                title, icon = f['title'], f['icon']
                spec = f['pages']
                if spec == 'WELCOME':
                    pages = self.custom_pages(key, [(a, b) for a, b in T.WELCOME])
                elif spec == 'ISLAND_TIPS':
                    pages = self.custom_pages(key, [(a, b) for a, b in T.ISLAND_TIPS])
                elif isinstance(spec, str) and spec.startswith('@'):
                    pages = getattr(self, 'gen_' + spec[1:].lower())(key)
                else:
                    pages = self.custom_pages(key, spec)
            self.item_ok(icon, f'field guide {f["id"]}')
            bg = BG_MILESTONE if f.get('star') else BG_READING
            e = {'category': f'{NS}:{cat}', 'name': self.tr(f'{key}.name', title), 'icon': icon, 'x': x, 'y': y,
                 'background_u_index': bg[0], 'background_v_index': bg[1], 'pages': pages}
            gate = f.get('gate')
            if gate:
                if f.get('read_gate'):
                    e['condition'] = {'type': 'modonomicon:entry_read', 'entry_id': f'{NS}:field_guide/{gate}',
                                      'tooltip': self.tr(f'{key}.gate', 'Read "About This Modpack" first')}
                    e['parents'] = [{'entry': f'{NS}:field_guide/{gate}'}]
                else:
                    e['condition'] = self.adv_cond(self.quest_adv(gate),
                                                   self.tr(f'{key}.gate', f'Unlocks after: {self.Q[gate]["title"]}'))
            if f.get('after'):
                e['parents'] = [{'entry': f'{NS}:field_guide/{f["after"]}'}]
            self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{cat}/{f["id"]}.json', e)

    def planet_profile(self, pk, key):
        p = self.k['planets'][pk]
        title = p['name']
        icon = f'ad_astra:{pk}_globe'
        pages = [{'type': 'modonomicon:image', 'images': [f'{NS}:textures/gui/book/planet/{pk}.png'],
                  'title': self.tr(f'{key}.ititle', title),
                  'text': self.tr(f'{key}.itext', f'{len(p["biomes"])} biomes, {len(p["structures"])} landmarks.'),
                  'border': True}]
        blocks = ['**Biomes**\n' + '\n'.join(f'- {b["name"]}' for b in p['biomes']) + '\n\n']
        ores = []
        for o in p['ores']:
            for b in o['blocks'][:1]:
                if b in self.known:
                    h = f' (Y {o["height"]})' if o.get('height') else ''
                    ores.append(f'- {self.ilink(b)}{h}')
        if ores:
            blocks.append('**Ores**\n' + '\n'.join(dict.fromkeys(ores)) + '\n\n')
        mobs = []
        for m in p['mobs']:
            dr = ', '.join(self.name(d['item']) for d in m.get('drops', [])[:2])
            mobs.append(f'- {m["name"]}' + (f': {dr}' if dr else ''))
        if mobs:
            blocks.append('**Creatures**\n' + '\n'.join(mobs) + '\n\n')
        st = [f'- {s["name"]}' for s in p['structures']]
        if st:
            blocks.append('**Landmarks**\n' + '\n'.join(st) + '\n\n')
        pages += self.text_pages(f'{key}.info', f'{title} at a glance', blocks)
        return title, icon, pages

    def gen_sifting(self, key):
        blocks = ["A [[create:millstone]] grinds cobblestone into gravel, gravel into sand, and sand into dust.",
                  "Put those in a [[createsifter:sifter]] with a mesh inside. Every block and every mesh gives "
                  "different drops.",
                  "A **waterlogged** sifter has its own drops: saplings from dirt, rubber and clay from sand."]
        pages = self.text_pages(f'{key}.a', 'Sifting', [self.md(b) for b in blocks])
        pages.append(self.page_spotlight(f'{key}.dust', 'createsifter:dust', 'Dust',
                                         self.md('Mill sand to get [[createsifter:dust]]. Dust gives redstone, gunpowder '
                                                 'and powdered obsidian.')))
        return pages

    def gen_meshes(self, key):
        order = ['createsifter:string_mesh', 'createsifter:andesite_mesh', 'createsifter:zinc_mesh',
                 'createsifter:brass_mesh', 'createsifter:advanced_brass_mesh']
        pages = self.text_pages(f'{key}.a', 'The mesh ladder', [
            'Each mesh is made from the one before it. Better meshes find better things.',
            '\n'.join(f'{i + 1}. {self.ilink(m)}' for i, m in enumerate(order)) + '\n\n'])
        inputs = ['minecraft:dirt', 'minecraft:gravel', 'minecraft:sand', 'createsifter:dust', 'minecraft:soul_sand',
                  'ad_astra:moon_sand', 'ad_astra:mars_sand']
        for mi, mesh in enumerate(order):
            blocks = []
            for inp in inputs:
                for s in self.k['sifting']:
                    if s['mesh'] == mesh and s['input'] == inp and not s['waterlogged']:
                        best = {}
                        for o in s['outputs']:
                            if o['item'] in self.known and 'card' not in o['item']:
                                best[o['item']] = max(best.get(o['item'], 0), o['chance'] or 0)
                        top = sorted(best.items(), key=lambda kv: -kv[1])[:5]
                        if top:
                            blocks.append(f'**{s["input_name"]}**: ' + ', '.join(
                                f'{self.name(i)} {pct(c)}' for i, c in top))
            if blocks:
                pages += self.text_pages(f'{key}.m{mi}', self.name(mesh), blocks)
        return pages

    def gen_extruder(self, key):
        pages = self.text_pages(f'{key}.a', 'Mechanical Extruder', [
            self.md('The [[create_mechanical_extruder:mechanical_extruder]] makes a block forever from the fluids '
                    'beside it. The **block under it** picks what it makes, and is never used up.')])
        pages.append({'type': 'modonomicon:multiblock', 'multiblock_id': f'{NS}:extruder_setup',
                      'multiblock_name': self.tr(f'{key}.mb', 'Extruder setup'),
                      'text': self.tr(f'{key}.mbt', 'Lava and water beside it, a catalyst block below.'),
                      'show_visualize_button': True})
        rows = []
        for e in sorted(self.k['extruding'], key=lambda e: (e['catalyst'] is None, e['catalyst_name'] or '')):
            out = ', '.join(self.name(o) for o in e['outputs'])
            fl = ' + '.join(self.name(f) for f in e['fluids'])
            if e['catalyst']:
                rows.append(f'- {e["catalyst_name"]}: **{out}**')
            else:
                rows.append(f'- No block, {fl}: **{out}**')
        pages += self.text_pages(f'{key}.b', 'Catalysts', ['\n'.join(rows) + '\n\n'])
        pages += self.text_pages(f'{key}.c', 'Andesite Extruder', [
            self.md('The [[quicreate:andesite_extruder]] is the early version. It makes a **random** natural stone each '
                    'cycle, never the metal stones.'),
            'The block below picks the mix:',
            '\n'.join(f'- **{a}**: {b}' for a, b in T.ANDESITE_EXTRUDER_TABLES) + '\n\n'])
        return pages

    def gen_cards(self, key):
        return self.text_pages(f'{key}.a', 'Card packs', [
            self.md('Most sifting tables drop card packs at small chances. Open a pack for cards.'),
            self.md('Mob cards craft into **spawn eggs**: that is how animals reach the island.'),
            self.md('Common packs hold farm animals. Rare packs hold villagers. Smelt an uncommon pack for a nether '
                    'pack.'),
            self.md('A deployer holding shears opens packs for you.'),
            f'See the {self.entry_link("card_packs", "Cards & Mobs")} side path.'])

    def gen_fishing(self, key):
        blocks = [self.md('Fishing can catch **kelpy balls**: open them for loot. Better rods catch better balls.')]
        for t in self.k.get('fishing') or []:
            d = t['data']
            parts = []
            for w in ('light', 'medium', 'heavy'):
                if d.get(w):
                    parts.append(f'{w} {pct(d[w])}')
            if parts:
                blocks.append(f'**{t["rod"]}**: ' + ', '.join(parts))
        return self.text_pages(f'{key}.a', 'Fishing', blocks)

    def gen_bosses(self, key):
        pages = self.text_pages(f'{key}.a', 'Boss guide', [
            'Each world has bosses. Their drops make the next tier of gear, and the creative ending needs four of them.',
            'Bring food, armour and a way home. The Bestiary side path has a page for every boss.'])
        for b in self.k['bosses']:
            if b['entity'] not in self.entities:
                continue
            where = self.k['planets'].get(b.get('planet') or '', {}).get('name', '?')
            st = self.name(b['structure']) if b.get('structure') else None
            txt = f'{where}' + (f', {st}' if st else '')
            pages.append({'type': 'modonomicon:entity', 'entity_id': b['entity'],
                          'name': self.tr(f'{key}.{b["entity"].replace(":", "_")}.n', b['name']),
                          'text': self.tr(f'{key}.{b["entity"].replace(":", "_")}.t', txt), 'scale': 0.7})
        return pages

    # ---------------------------------------------------- side paths
    def stage_gate(self, i):
        g = T.STAGES[i][3]
        if g is None:
            return None
        if isinstance(g, list):
            return self.any_of([self.adv_cond(self.quest_adv(x), self.tr(f'stage.{i}.{x}', f'Finish: {self.Q[x]["title"]}'))
                                for x in g])
        return self.adv_cond(self.quest_adv(g), self.tr(f'stage.{i}', f'Unlocks after: {self.Q[g]["title"]}'))

    def side_goals(self, path):
        goals = list(T.SIDE_GOALS.get(path, []))
        if path == 'explorer':
            goals += self.gen_explorer()
        if path == 'bestiary':
            goals += self.gen_bestiary()
        return goals

    def gen_explorer(self):
        out = [dict(id='nether', name='Into the Nether', icon='minecraft:netherrack', stage=1, row=0, kind='dimension',
                    dimension='minecraft:the_nether', text='Build a nether portal. The Nether has its own small island.'),
               dict(id='the_end', name='The End', icon='minecraft:end_stone', stage=2, row=2, kind='dimension',
                    dimension='minecraft:the_end', text="The Moon's stronghold holds the only portal to the End.")]
        out += T.EXPLORER_EXTRA
        stage_of = {'moon': 2, 'mars': 3, 'venus': 4, 'mercury': 4, 'glacio': 5}
        rows = collections.Counter()
        for pk, p in self.k['planets'].items():
            st = stage_of[pk]
            out.append(dict(id=f'{pk}_biomes', name=f'Biomes of {p["name"]}', icon=f'ad_astra:{pk}_globe', stage=st,
                            row=rows[st], kind='biomes', biomes=[b['id'] for b in p['biomes']],
                            text=f'Set foot in every biome on {p["name"]}.'))
            rows[st] += 1
            out.append(dict(id=f'{pk}_landmarks', name=f'Landmarks of {p["name"]}', icon='minecraft:map', stage=st,
                            row=rows[st], kind='structures', structures=[s['id'] for s in p['structures']],
                            text=f'Find every landmark on {p["name"]}.'))
            rows[st] += 1
        return out

    def gen_bestiary(self):
        out = [dict(id='night_watch', name='Night watch', icon='minecraft:zombie_head', stage=0, row=0, kind='kills',
                    mobs=['minecraft:zombie', 'minecraft:skeleton', 'minecraft:spider', 'minecraft:creeper',
                          'minecraft:drowned'],
                    text='The dark side of the island spawns monsters. Defeat one of each.')]
        stage_of = {'moon': 2, 'mars': 3, 'venus': 4, 'mercury': 4, 'glacio': 5}
        rows = collections.Counter()
        boss_ids = {b['entity'] for b in self.k['bosses']}
        for pk, p in self.k['planets'].items():
            st = stage_of[pk]
            mobs = [m['id'] for m in p['mobs']]
            for s in p['structures']:
                mobs += s['mobs']
            mobs = [m for m in dict.fromkeys(mobs) if m in self.entities and m not in boss_ids
                    and not m.startswith('minecraft:') or m in ('minecraft:enderman',)]
            mobs = [m for m in mobs if m in self.entities and m not in boss_ids]
            if mobs:
                out.append(dict(id=f'{pk}_hunter', name=f'Hunter: {p["name"]}', icon='minecraft:iron_sword', stage=st,
                                row=rows[st], kind='kills', mobs=mobs[:10],
                                text=f'Defeat one of every creature on {p["name"]}.'))
                rows[st] += 1
        for b in self.k['bosses']:
            if b['entity'] not in self.entities or not b.get('quest'):
                continue
            st = stage_of.get(b.get('planet') or '', 2)
            out.append(dict(id=f'boss_{b["entity"].split(":")[1]}', boss=b, stage=st, row=rows[st]))
            rows[st] += 1
        return out

    def build_side_paths(self):
        hub = 'side_paths'
        cj = {'name': self.tr('cat.side_paths', 'Side Paths'), 'icon': 'minecraft:compass', 'sort_number': 20}
        self.background(cj, 'side_paths', False)
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/categories/{hub}.json', cj)
        intro = self.text_pages('side.hub.intro', 'Side Paths', [
            'Optional goals for each stage of the pack. None of them are needed to finish.',
            'Finished goals give a **reward** picked to help the main route.',
            'Each path is sorted left to right by world: island, workshop, Moon, Mars, Venus and Mercury, Glacio.'])
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{hub}/intro.json', {
            'category': f'{NS}:{hub}', 'name': self.tr('side.hub.name', 'About Side Paths'), 'icon': 'minecraft:compass',
            'x': 0, 'y': -3, 'background_u_index': BG_MILESTONE[0], 'background_v_index': BG_MILESTONE[1],
            'pages': intro})
        spots = [(-4, 0), (0, 0), (4, 0), (-4, 3), (0, 3), (4, 3)]
        for (pid, pname, picon, bg, pdesc), xy in zip(T.SIDE_PATHS, spots):
            self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{hub}/{pid}.json', {
                'category': f'{NS}:{hub}', 'name': self.tr(f'side.hub.{pid}', pname),
                'description': self.tr(f'side.hub.{pid}.desc', pdesc), 'icon': picon, 'x': xy[0], 'y': xy[1],
                'background_u_index': BG_LINK[0], 'background_v_index': BG_LINK[1],
                'category_to_open': f'{NS}:{pid}', 'parents': [{'entry': f'{NS}:{hub}/intro', 'draw_arrow': False}]})
            if pid == 'cards':
                continue      # the Cards & Mobs tab is the old side chapter, built with the main chapters
            sub = {'name': self.tr(f'cat.{pid}', pname), 'icon': picon, 'sort_number': 30,
                   'show_category_button': False}
            self.background(sub, bg, False)
            self.put(f'data/{NS}/modonomicon/books/{BOOK}/categories/{pid}.json', sub)
            self.build_side_tab(pid, pname)
        # back link inside the cards tab
        self.back_link('cards')
        self.write_side_root()

    def back_link(self, cat, xy=None):
        x, y = xy or (-9, -6)
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{cat}/back.json', {
            'category': f'{NS}:{cat}', 'name': self.tr(f'side.back.{cat}', 'Back to Side Paths'),
            'icon': 'minecraft:compass', 'x': x, 'y': y, 'background_u_index': BG_LINK[0],
            'background_v_index': BG_LINK[1], 'category_to_open': f'{NS}:side_paths'})

    def write_side_root(self):
        self.put(f'data/{NS}/advancements/side/root.json', {
            'display': self.display('minecraft:compass', 'Side Paths', 'Optional goals from the guide book', 'task',
                                    False, False, False, 'minecraft:textures/block/dark_oak_planks.png'),
            'criteria': {'tick': {'trigger': 'minecraft:tick'}}})

    def build_side_tab(self, pid, pname):
        goals = self.side_goals(pid)
        self.back_link(pid, (-10, -5))
        # stage headers across the top
        used_stages = sorted({g['stage'] for g in goals})
        for i, (skey, sname, sicon, _g) in enumerate(T.STAGES):
            if i not in used_stages:
                continue
            x = -7 + i * 3
            e = {'category': f'{NS}:{pid}', 'name': self.tr(f'side.{pid}.stage{i}', sname), 'icon': sicon, 'x': x, 'y': -5,
                 'background_u_index': BG_MILESTONE[0], 'background_v_index': BG_MILESTONE[1],
                 'pages': self.text_pages(f'side.{pid}.stage{i}.p', sname, [
                     f'{pname} goals for {sname}.',
                     '\n'.join(f'- {self.goal_name(g)}' for g in goals if g['stage'] == i) + '\n\n'])}
            c = self.stage_gate(i)
            if c:
                e['condition'] = c
            self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{pid}/stage{i}.json', e)
        for g in goals:
            self.side_goal(pid, g)

    def goal_name(self, g):
        if g.get('link'):
            return self.Q[g['link']]['title']
        if g.get('boss'):
            return g['boss']['name']
        return g['name']

    def side_goal(self, pid, g):
        gid = g['id']
        key = f'side.{pid}.{gid}'
        x, y = -7 + g['stage'] * 3, -3 + g['row'] * 2
        adv_id = f'{NS}:side/{pid}/{gid}'
        reward = self.rewards.get(f'{pid}/{gid}') or []
        reward_line = ''
        if reward:
            reward_line = '**Reward:** ' + ', '.join(self.ilink(r['item'], r.get('count', 1)) for r in reward
                                                    if self.item_ok(r['item'], f'reward {gid}'))
        pages = []
        icon = g.get('icon')
        crit = {}
        if g.get('boss'):
            b = g['boss']
            q = self.Q[b['quest']]
            icon = q.get('icon') or 'minecraft:skeleton_skull'
            where = self.k['planets'].get(b.get('planet') or '', {}).get('name', '?')
            st = self.name(b['structure']) if b.get('structure') else None
            pages.append({'type': 'modonomicon:entity', 'entity_id': b['entity'], 'name': self.tr(f'{key}.n', b['name']),
                          'text': self.tr(f'{key}.t', f'{where}' + (f', {st}' if st else '')), 'scale': 0.8})
            blocks = self.boss_blocks(b['entity'])
            blocks.append(f'Main route step: {self.entry_link(b["quest"])}')
            pages += self.text_pages(f'{key}.d', b['name'], blocks)
            crit = {'kill': {'trigger': 'minecraft:player_killed_entity', 'conditions': {'entity': {'type': b['entity']}}}}
            name = b['name']
            desc = 'Boss'
        elif g.get('link'):
            q = self.Q[g['link']]
            icon = q.get('icon') or 'minecraft:book'
            name = q['title']
            desc = q.get('subtitle') or 'Optional'
            for i, t in enumerate(q['tasks']):
                c = self.criterion_for_task(t)
                if c:
                    crit[f'task{i}'] = c
            pages.append(self.page_spotlight(f'{key}.s', icon, name, self.md(
                f'*{desc}*\n\n**Goal:** ' + ', '.join(self.task_text(t) for t in q['tasks']))))
            pages += self.text_pages(f'{key}.l', 'Details', [f'Full steps: {self.entry_link(g["link"])}'] +
                                     ([reward_line] if reward_line else []))
        else:
            name = g['name']
            desc = g['text']
            kind = g['kind']
            if kind == 'items':
                items = [i for i in g['items'] if self.item_ok(i, f'goal {gid}')]
                miss = [i for i in items if i not in self.obtainable and not i.endswith('_log') and 'glacian' not in i
                        and 'bamboo' not in i and i != 'minecraft:beetroot']
                if miss:
                    WARN.append(f'goal {gid}: no source found for {miss}')
                for i in items:
                    crit[i.split(':')[1]] = {'trigger': 'minecraft:inventory_changed',
                                             'conditions': {'items': [{'items': [i]}]}}
                goal = 'Collect one of each:\n' + '\n'.join(f'- {self.ilink(i)}' for i in items) + '\n\n'
            elif kind == 'count':
                self.item_ok(g['item'], f'goal {gid}')
                crit['have'] = {'trigger': f'{NS}:has_items', 'conditions': {'item': g['item'], 'count': g['count']}}
                goal = f'Have **{g["count"]}** {self.ilink(g["item"])} at once.'
            elif kind == 'kills':
                mobs = [m for m in g['mobs'] if m in self.entities]
                for m in mobs:
                    crit[m.split(':')[1]] = {'trigger': 'minecraft:player_killed_entity',
                                             'conditions': {'entity': {'type': m}}}
                goal = 'Defeat one of each:\n' + '\n'.join(f'- {self.name(m)}' for m in mobs) + '\n\n'
            elif kind == 'biomes':
                for b in g['biomes']:
                    crit[b.split(':')[1]] = {'trigger': 'minecraft:location',
                                             'conditions': {'player': {'location': {'biome': b}}}}
                goal = 'Visit:\n' + '\n'.join(f'- {self.name(b)}' for b in g['biomes']) + '\n\n'
            elif kind == 'structures':
                for s in g['structures']:
                    crit[s.split(':')[1]] = {'trigger': 'minecraft:location',
                                             'conditions': {'player': {'location': {'structure': s}}}}
                goal = 'Find:\n' + '\n'.join(f'- {self.name(s)}' for s in g['structures']) + '\n\n'
            elif kind == 'dimension':
                crit['go'] = {'trigger': 'minecraft:changed_dimension', 'conditions': {'to': g['dimension']}}
                goal = f'Travel to **{self.name(g["dimension"])}**.'
            else:
                raise ValueError(kind)
            pages += self.text_pages(f'{key}.p', name, [self.md(g['text']), goal] + ([reward_line] if reward_line else []))
        self.item_ok(icon, f'side goal {gid}')
        adv = {'parent': f'{NS}:side/root',
               'display': self.display(icon, name, desc if len(desc) < 80 else desc[:77] + '...', 'challenge', True,
                                       False, True),
               'criteria': crit, 'requirements': [[k] for k in crit]}
        # every goal runs its reward function; the function is empty until a reward is set in rewards.yaml
        adv['rewards'] = {'function': f'{NS}:rewards/{pid}/{gid}'}
        lines = [f'# Reward for the "{name}" side goal. Generated from guide/book/rewards.yaml: edit that file and',
                 '# rebuild the book (python guide/book/build_book.py --resources src/main/resources).']
        lines += [f'give @s {r["item"]} {r.get("count", 1)}' for r in reward]
        self.put(f'data/{NS}/functions/rewards/{pid}/{gid}.mcfunction', '\n'.join(lines) + '\n')
        self.put(f'data/{NS}/advancements/side/{pid}/{gid}.json', adv)
        done = self.adv_cond(adv_id, self.tr(f'{key}.donetip', 'Done'))
        pages += self.text_pages(f'{key}.done', 'Done', [f'[#]({COL_GOOD})**Completed!**[#]()'] +
                                 ([reward_line.replace('**Reward:**', 'You received:')] if reward_line else []), cond=done)
        e = {'category': f'{NS}:{pid}', 'name': self.tr(f'{key}.name', name), 'description': self.tr(f'{key}.desc', desc),
             'icon': icon, 'x': x, 'y': y, 'background_u_index': BG_OPTIONAL[0], 'background_v_index': BG_OPTIONAL[1],
             'pages': pages, 'parents': [{'entry': f'{NS}:{pid}/stage{g["stage"]}', 'draw_arrow': False}]}
        c = self.stage_gate(g['stage'])
        if c:
            e['condition'] = c
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/entries/{pid}/{gid}.json', e)
        self.reward_slots.append(f'{pid}/{gid}')

    # ---------------------------------------------------- the book, root, starting book
    def build_book_files(self):
        self.put(f'data/{NS}/modonomicon/books/{BOOK}/book.json', {
            'name': self.tr('name', T.BOOK_NAME), 'tooltip': self.tr('tooltip', T.BOOK_TOOLTIP),
            'model': 'modonomicon:modonomicon_blue', 'generate_book_item': True,
            'default_title_color': 0x2B3A55, 'auto_add_read_conditions': False})
        self.put(f'data/{NS}/advancements/skyblock/root.json', {
            'display': self.display('minecraft:oak_sapling', 'Quicreate Skyblock', 'Your progress through the pack',
                                    'task', False, False, False, 'minecraft:textures/block/andesite.png'),
            'criteria': {'tick': {'trigger': 'minecraft:tick'}}})
        self.put(f'data/{NS}/advancements/book/give_book.json', {
            'criteria': {'tick': {'trigger': 'minecraft:tick'}},
            'rewards': {'function': f'{NS}:book/give'}})
        self.put(f'data/{NS}/functions/book/give.mcfunction',
                 'give @s modonomicon:modonomicon{"modonomicon:book_id":"quicreate:skyblock"}\n')
        self.put(f'data/{NS}/recipes/guide_book.json', {
            'type': 'minecraft:crafting_shapeless',
            'ingredients': [{'item': 'minecraft:book'}, {'item': 'minecraft:cobblestone'}],
            'result': {'item': 'modonomicon:modonomicon', 'count': 1, 'nbt': '{"modonomicon:book_id":"quicreate:skyblock"}'}})

    def build_multiblocks(self):
        mb = f'data/{NS}/modonomicon/multiblocks'
        self.put(f'{mb}/cobblestone_generator.json', {
            'type': 'modonomicon:dense',
            'pattern': [['W0L'], ['SSS']],
            'mapping': {'W': {'type': 'modonomicon:display', 'display': 'minecraft:water'},
                        'L': {'type': 'modonomicon:display', 'display': 'minecraft:lava'},
                        '0': {'type': 'modonomicon:block', 'block': 'minecraft:cobblestone'},
                        'S': {'type': 'modonomicon:display', 'display': 'minecraft:stone'}}})
        self.put(f'{mb}/extruder_setup.json', {
            'type': 'modonomicon:dense',
            'pattern': [['L0W'], [' C ']],
            'mapping': {'0': {'type': 'modonomicon:block', 'block': 'create_mechanical_extruder:mechanical_extruder'},
                        'L': {'type': 'modonomicon:display', 'display': 'minecraft:lava'},
                        'W': {'type': 'modonomicon:display', 'display': 'minecraft:water'},
                        'C': {'type': 'modonomicon:block', 'block': 'minecraft:iron_block'}}})
        cna = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'multiblocks_cna.json'), encoding='utf-8'))
        for name, data in cna.items():
            self.put(f'{mb}/{"reactor" if name == "reactor" else "cna_" + name}.json', data)
        self.put(f'{mb}/mechanical_crafter_grid.json', {
            'type': 'modonomicon:dense',
            'pattern': [[' MMM '], ['MMMMM'], ['MM0MM'], ['MMMMM'], [' MMM ']],
            'mapping': {'M': {'type': 'modonomicon:block', 'block': 'create:mechanical_crafter'},
                        '0': {'type': 'modonomicon:block', 'block': 'create:mechanical_crafter'}}})

    # ---------------------------------------------------- run
    def run(self, materials):
        self.materials = materials
        self.reward_slots = []
        for q in T.EXTRA_QUESTS:
            if q['id'] not in self.Q:
                self.k['quests'].append(q)
                self.Q[q['id']] = q
        for it, nm in T.EXTRA_KNOWN.items():
            self.known.add(it)
            self.obtainable.add(it)
            self.names[it] = nm
        self.plan_main()
        self.build_book_files()
        self.build_field_guide()
        for i, (group, cat, short, icon, bg, starry, wk) in enumerate(T.CHAPTERS):
            self.build_chapter(group, cat, short, icon, bg, starry, wk, i + 1)
        self.build_chapter(T.SIDE_CARDS_GROUP, 'cards', 'Cards & Mobs', 'cards:common_card_pack', 'cards', False, 'cards', 31)
        self.build_side_paths()
        self.build_multiblocks()


def load_materials(path):
    """materials.md rows -> category id -> text."""
    m = {}
    if not os.path.exists(path):
        return m
    keymap = {'Island': 'sky', 'Sifting': 'sifting', 'New Age': 'new_age', 'Improvements': 'improvements',
              'Space': 'space', 'Moon': 'moon', 'Mars': 'mars', 'Venus & Mercury': 'venus_mercury', 'Glacio': 'glacio',
              'Creative ending': 'creative', 'Cards & Mobs': 'cards'}
    for line in open(path, encoding='utf-8'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 4 or cells[0].startswith('Section') or cells[0].startswith('---'):
            continue
        sec = re.sub(r'\s*\(#.*\)', '', cells[0])
        cat = keymap.get(sec)
        if not cat:
            continue
        mats = [x.strip() for x in cells[1].split(',')][:8]
        txt = '\n'.join(f'- {x}' for x in mats) + '\n\n'
        extra = []
        if cells[2] and cells[2] not in ('0k', '–'):
            extra.append(f'Energy: {cells[2]} FE')
        if cells[3] and cells[3] != '–':
            extra.append(f'Fluids: {cells[3]}')
        if extra:
            txt += '\n'.join(extra)
        m[cat] = txt
    return m


def load_rewards(path):
    import yaml
    if not os.path.exists(path):
        return {}
    data = yaml.safe_load(open(path, encoding='utf-8')) or {}
    out = {}
    for k, v in (data.get('rewards') or {}).items():
        lst = []
        for r in v or []:
            if isinstance(r, str):
                parts = r.split()
                lst.append({'item': parts[0], 'count': int(parts[1]) if len(parts) > 1 else 1})
            elif isinstance(r, dict):
                lst.append(r)
        out[k] = lst
    return out


def write_rewards_template(path, slots, current):
    lines = ['# Side-path rewards. One line per goal: "path/goal": [item count, item count]',
             '# Leave a goal empty for no reward. Rebuild the book after editing:',
             '#   python guide/book/build_book.py --resources src/main/resources', 'rewards:']
    for s in slots:
        cur = current.get(s) or []
        vals = ', '.join(f'"{r["item"]} {r.get("count", 1)}"' for r in cur)
        lines.append(f'  {s}: [{vals}]')
    open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def show_whole_map(b):
    """Modonomicon hides an entry until its parents unlock, but still draws the lines to it, which leaves lines
    ending in empty space. Give every entry an invisible extra parent that is always unlocked (the tab's intro,
    back link or welcome page) and show it once any parent is unlocked: the whole tab is drawn, locked steps grey."""
    anchors = {}
    for rel, e in b.files.items():
        m = re.match(rf'data/{NS}/modonomicon/books/{BOOK}/entries/([^/]+)/([^/]+)\.json$', rel)
        if m and isinstance(e, dict) and m.group(2) in ('intro', 'back', 'welcome') and 'condition' not in e:
            anchors.setdefault(m.group(1), f'{NS}:{m.group(1)}/{m.group(2)}')
    for rel, e in b.files.items():
        m = re.match(rf'data/{NS}/modonomicon/books/{BOOK}/entries/([^/]+)/([^/]+)\.json$', rel)
        if not m or not isinstance(e, dict) or 'category_to_open' in e or e.get('hide_while_locked'):
            continue
        anchor = anchors.get(m.group(1))
        if not anchor or anchor.endswith('/' + m.group(2)):
            continue
        e.setdefault('parents', []).append({'entry': anchor, 'line_enabled': False, 'draw_arrow': False})
        e['show_when_any_parent_unlocked'] = True


def _fix_lang_keys(e, lang):
    """Point text keys that no longer exist at the same step's key under its current tab."""
    pre = 'book.quicreate.skyblock.'
    cat = str(e.get('category', '')).split(':')[-1]
    def fix(v):
        if isinstance(v, str) and v.startswith(pre) and v not in lang:
            parts = v[len(pre):].split('.')
            if len(parts) >= 3:
                tail = '.' + '.'.join(parts[1:])
                if pre + cat + tail in lang:
                    return pre + cat + tail
                hits = [k for k in lang if k.startswith(pre) and k.endswith(tail) and k.count('.') == v.count('.')]
                if len(hits) == 1:
                    return hits[0]
            return v
        if isinstance(v, dict):
            return {k: fix(x) for k, x in v.items()}
        if isinstance(v, list):
            return [fix(x) for x in v]
        return v
    for k in list(e.keys()):
        e[k] = fix(e[k])


def fix_moved_refs(b, moved, entry_rel):
    """After steps moved tab: parents follow the new id (a line only within one tab, otherwise a plain
    requirement, which the unlock condition already holds), the moved step hangs off its new tab's intro,
    and every entry:// link in the texts points at the new id."""
    cat_of = lambda eid: eid.split(':', 1)[1].split('/')[0]
    for rel, e in b.files.items():
        if '/entries/' not in rel or not isinstance(e, dict):
            continue
        me = f'{NS}:' + rel.split('/entries/', 1)[1][:-5]
        ps = []
        for p in e.get('parents', []):
            tgt = moved.get(p['entry'], p['entry'])
            if cat_of(tgt) != cat_of(me):
                continue   # lines never cross tabs
            ps.append({**p, 'entry': tgt})
        anchors = [f'{NS}:{cat_of(me)}/{n}' for n in ('intro', 'back', 'welcome')]
        if me in moved.values() and not any(p['entry'] in anchors for p in ps):
            for anc in anchors:
                if entry_rel(anc) in b.files and anc != me:
                    ps.append({'entry': anc, 'line_enabled': False, 'draw_arrow': False})
                    break
            e['show_when_any_parent_unlocked'] = True
        if 'parents' in e:
            e['parents'] = ps
    for old, new in moved.items():
        a, z = f'entry://{NS}:{BOOK}/{old.split(":", 1)[1]}', f'entry://{NS}:{BOOK}/{new.split(":", 1)[1]}'
        pat = re.compile(re.escape(a) + r'(?![a-z0-9_/])')
        for k, v in b.lang.items():
            if isinstance(v, str) and a in v:
                b.lang[k] = pat.sub(z, v)


def apply_overrides(b, path):
    """Hand edits from editor.html, applied on top of the generated book.

    New format: {"layout": {id: {x, y, icon, bg, parents}}, "entries": {id: full entry json},
    "advancements": {id: json}, "lang": {key: text}, "deleted": [ids], "deleted_advancements": [ids]}.
    An older file holding only the layout map is still read.
    """
    if not os.path.exists(path):
        return
    ovr = json.load(open(path, encoding='utf-8'))
    if not any(k in ovr for k in ('layout', 'entries', 'advancements', 'lang', 'deleted', 'moved', 'multiblocks')):
        ovr = {'layout': ovr}
    entry_rel = lambda eid: f'data/{NS}/modonomicon/books/{BOOK}/entries/{eid.split(":", 1)[1]}.json'
    adv_rel = lambda aid: f'data/{NS}/advancements/{aid.split(":", 1)[1]}.json'
    moved = ovr.get('moved') or {}
    for old, new in moved.items():   # steps moved to another tab: move the generated file first
        e = b.files.pop(entry_rel(old), None)
        if isinstance(e, dict):
            e['category'] = f'{NS}:{new.split(":", 1)[1].split("/")[0]}'
            b.files[entry_rel(new)] = e
    # A hand-saved step the generator has since put on another tab (GROUP_OVERRIDE) follows it there.
    gen_ids = {f'{NS}:' + rel.split('/entries/', 1)[1][:-5] for rel in b.files if '/entries/' in rel}
    entries = {}
    for eid, e in (ovr.get('entries') or {}).items():
        if eid not in gen_ids and eid not in moved.values():
            name = eid.rsplit('/', 1)[1]
            same = [g for g in gen_ids if g.rsplit('/', 1)[1] == name and g != eid and '/field_guide/' not in g.replace(':', '/')]
            if len(same) == 1 and isinstance(e, dict):
                new = same[0]
                moved = {**moved, eid: new}
                e = {**e, 'category': f'{NS}:{new.split(":", 1)[1].split("/")[0]}'}
                WARN.append(f'{eid}: the generator moved this step to {new}; your saved version moved with it')
                eid = new
        entries[eid] = e
    for eid, e in entries.items():
        gen = b.files.get(entry_rel(eid))
        if isinstance(gen, dict) and isinstance(e, dict):
            # new build previews reach hand-saved steps too: add any the saved version doesn't have yet
            have = {p.get('multiblock_id') for p in e.get('pages', [])}
            new = [p for p in gen.get('pages', []) if p.get('type') == 'modonomicon:multiblock' and p.get('multiblock_id') not in have]
            if new:
                pages = list(e.get('pages', []))
                at = next((i for i, p in enumerate(pages) if p.get('condition')), len(pages))
                e = {**e, 'pages': pages[:at] + new + pages[at:]}
        b.files[entry_rel(eid)] = e
    for aid, a in (ovr.get('advancements') or {}).items():
        b.files[adv_rel(aid)] = a
    for mid, m in (ovr.get('multiblocks') or {}).items():   # builds made or changed in the editor
        b.files[f'data/{NS}/modonomicon/multiblocks/{mid.split(":", 1)[1]}.json'] = m
    for eid in ovr.get('deleted') or []:
        b.files.pop(entry_rel(eid), None)
        # text links to a deleted step become plain text
        dead = re.compile(r'\[([^\]]*)\]\(entry://' + re.escape(f'{NS}:{BOOK}/{eid.split(":", 1)[1]}') + r'(?![a-z0-9_/])[^)]*\)')
        for k, v in b.lang.items():
            if isinstance(v, str) and 'entry://' in v:
                b.lang[k] = dead.sub(r'\1', v)
        for rel, e in b.files.items():   # nothing may point at a deleted step
            if '/entries/' in rel and isinstance(e, dict) and e.get('parents'):
                e['parents'] = [p for p in e['parents'] if p['entry'] != eid]
    gone_advs = set(ovr.get('deleted_advancements') or [])

    def drop_gone(cond):
        # remove requirements on deleted advancements from a condition (None = nothing left)
        if not isinstance(cond, dict):
            return cond
        if cond.get('type') == 'modonomicon:advancement':
            return None if cond.get('advancement_id') in gone_advs else cond
        if cond.get('type') in ('modonomicon:and', 'modonomicon:or'):
            kids = [c for c in (drop_gone(c) for c in cond.get('children', [])) if c is not None]
            if not kids:
                return None
            return kids[0] if len(kids) == 1 else {**cond, 'children': kids}
        return cond
    for aid in ovr.get('deleted_advancements') or []:
        gone = b.files.pop(adv_rel(aid), None)
        for rel, adv in b.files.items():   # children of a deleted advancement move up a level
            if '/advancements/' in rel and isinstance(adv, dict) and adv.get('parent') == aid:
                adv['parent'] = (gone or {}).get('parent', f'{NS}:skyblock/root')
    b.lang.update(ovr.get('lang') or {})
    for rel, e in b.files.items():
        if '/entries/' not in rel or not isinstance(e, dict):
            continue
        if gone_advs and 'condition' in e:
            c = drop_gone(e['condition'])
            if c is None:
                e.pop('condition')
            else:
                e['condition'] = c
        # a hand-saved step can name text keys the generator now writes under another tab (step moved)
        _fix_lang_keys(e, b.lang)
    if moved:
        fix_moved_refs(b, moved, entry_rel)
    for eid, o in (ovr.get('layout') or {}).items():
        e = b.files.get(entry_rel(eid))
        if not isinstance(e, dict):
            WARN.append(f'layout override for {eid}: entry no longer exists')
            continue
        for k in ('x', 'y', 'icon'):
            if k in o:
                e[k] = o[k]
        if 'bg' in o:
            e['background_u_index'], e['background_v_index'] = o['bg']
        for par in e.get('parents', []):
            po = (o.get('parents') or {}).get(par['entry'])
            if not po:
                continue
            for k in ('line_enabled', 'draw_arrow'):
                par.pop(k, None)
                if po.get(k) is False:
                    par[k] = False
            par.pop('line_reversed', None)
            if po.get('line_reversed'):
                pe = b.files.get(entry_rel(par['entry']))
                if pe and Builder.reverse_broken((pe['x'], pe['y']), (e['x'], e['y'])):
                    WARN.append(f'{eid}: reversed line from {par["entry"]} would draw wrong in game, left normal')
                else:
                    par['line_reversed'] = True
    # a hand-edited entry can also carry a reversed line Modonomicon draws wrong
    for rel, e in b.files.items():
        if '/entries/' not in rel or not isinstance(e, dict):
            continue
        for par in e.get('parents', []):
            pe = b.files.get(entry_rel(par['entry']))
            if par.get('line_reversed') and pe and Builder.reverse_broken((pe['x'], pe['y']), (e['x'], e['y'])):
                par.pop('line_reversed')
                WARN.append(f'{rel}: reversed line from {par["entry"]} would draw wrong in game, left normal')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resources', required=True)
    ap.add_argument('--knowledge', default=os.path.join(HERE, 'knowledge.json'))
    ap.add_argument('--materials', default=os.path.join(HERE, 'materials.md'))
    ap.add_argument('--rewards', default=os.path.join(HERE, 'rewards.yaml'))
    ap.add_argument('--guide-yaml', default=os.path.join(os.path.dirname(HERE), 'guide.yaml'))
    a = ap.parse_args()
    k = json.load(open(a.knowledge, encoding='utf-8'))
    walk = load_module(os.path.join(HERE, 'walkthrough_content.py'), 'walkthrough_content')
    rewards = load_rewards(a.rewards)
    b = Builder(a.resources, k, walk, rewards)
    try:
        import yaml
        cfg = yaml.safe_load(open(a.guide_yaml, encoding='utf-8'))
        for qid, sc in (cfg.get('steps') or {}).items():
            if sc and sc.get('note'):
                b.notes[qid] = ' '.join(sc['note'].split()).replace('`', '')
    except Exception as e:  # notes are a nicety
        WARN.append(f'guide.yaml notes not read: {e}')
    b.run(load_materials(a.materials))
    show_whole_map(b)
    apply_overrides(b, os.path.join(HERE, 'layout_overrides.json'))

    # clean old output, then write
    res = a.resources
    for d in (f'data/{NS}/modonomicon', f'data/{NS}/advancements/skyblock', f'data/{NS}/advancements/side',
              f'data/{NS}/advancements/book', f'data/{NS}/functions/book', f'data/{NS}/functions/rewards',
              f'assets/{NS}/textures/gui/book'):
        p = os.path.join(res, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    for rel, data in b.files.items():
        p = os.path.join(res, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            if isinstance(data, str):
                f.write(data)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')
    textures.backgrounds(os.path.join(res, f'assets/{NS}/textures/gui/book'))
    # keep only the generated backgrounds a tab still uses (most tabs are tiled block textures now)
    bgdir = os.path.join(res, f'assets/{NS}/textures/gui/book/background')
    used_bg = json.dumps([v for r, v in b.files.items() if '/categories/' in r])
    for fn in os.listdir(bgdir):
        if f'background/{fn}' not in used_bg:
            os.remove(os.path.join(bgdir, fn))
    textures.planets(os.path.join(res, f'assets/{NS}/textures/gui/book'))
    # lang: keep everything that is not ours, replace our block
    lp = os.path.join(res, f'assets/{NS}/lang/en_us.json')
    lang = json.load(open(lp, encoding='utf-8')) if os.path.exists(lp) else {}
    lang = {kk: v for kk, v in lang.items() if not kk.startswith(LANG_PREFIX)}
    lang.update(dict(sorted(b.lang.items())))
    with open(lp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(lang, f, indent=2, ensure_ascii=False)
        f.write('\n')
    write_rewards_template(a.rewards, b.reward_slots, rewards)
    entries = sum(1 for r in b.files if '/entries/' in r)
    advs = sum(1 for r in b.files if '/advancements/' in r)
    print(f'book: {entries} entries, {advs} advancements, {len(b.lang)} texts')
    for w in sorted(set(WARN)):
        print('  !', w)


if __name__ == '__main__':
    main()
