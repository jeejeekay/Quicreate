# The guide book (Modonomicon)

The pack's quest log and guide is a Modonomicon book, `quicreate:skyblock`, generated from these files into
`src/main/resources`. Progress is tracked with advancements; the book shows it.

| File | What it is |
|---|---|
| `book_text.py` | Hand-written text: Field Guide pages, tab settings, milestones, side-path goals |
| `walkthrough_content.py` | Chapter intros, tips and stage text (from the short walkthrough PDF) |
| `rewards.yaml` | Side-path rewards, one line per goal. Empty means no reward |
| `knowledge.json` | Recipes, quests, planets and loot, exported by `dump_knowledge.py` |
| `materials.md` | Materials estimate per chapter |
| `build_book.py` | Writes the book, advancements, functions, multiblocks, textures and lang |
| `check_book.py` | Checks every id, link, condition and page length |
| `textures.py` | Procedural tab backgrounds and planet pictures |

## Rebuild

```
pip install pyyaml numpy pillow
python guide/book/build_book.py --resources src/main/resources
python guide/book/check_book.py --resources src/main/resources
```

`build_book.py` deletes and rewrites its own output (`data/quicreate/modonomicon`, `data/quicreate/advancements/{skyblock,side,book}`,
`data/quicreate/functions/{book,rewards}`, `assets/quicreate/textures/gui/book`) and only its own `book.quicreate.skyblock.*`
keys in the lang file. Nothing else is touched.

After recipe, quest or worldgen changes, refresh `knowledge.json` first (needs the instance and vanilla data, see the
script header): `python guide/book/dump_knowledge.py --instance ... --repo . --vanilla ...`

## How progress works

- Each main step has a hidden advancement `quicreate:skyblock/<step>`. Item steps use the `quicreate:has_items`
  trigger (counts the whole inventory, like the old quest book). A toast shows when it's done.
- A book entry unlocks when the advancements of its parents are done. Its last page, **Completed**, only shows once its
  own advancement is done.
- Chapter tabs appear when something in them can be started (or at the gate set in `CHAPTER_GATES`).
- Side-path goals are `quicreate:side/<path>/<goal>`, and each runs `quicreate:rewards/<path>/<goal>` when done.
- The book is given on first join (`quicreate:book/give_book`) and can be crafted from a book and cobblestone.
- In game, `/reload` reloads the book with the datapacks (`/modonomicon reload` also exists).

## Editing the book by hand (editor.html)

Open `guide/book/editor.html` in Chrome or Edge and pick the Quicreate repo folder.

- **Map:** drag steps (or arrow keys), **+ New step** then click an empty cell, **Link** (click parent, then child),
  **Delete step**. Red lines run through a step or bend wrong in game; orange lines share a stretch.
- **Step tab:** name, tooltip line, icon, shape.
- **Pages tab:** edit titles and text with a live preview and a line count; add text, item, creature or crafting pages;
  reorder or delete pages. The "shown when done" page appears once the step is finished.
- **Task tab:** what finishes the step: have items (item or #tag + count), defeat a creature, travel to a
  dimension, find a structure. Each step's task is its hidden advancement (`quicreate:skyblock/...`).
- **Lines tab:** parents, line on/off, reverse bend, arrow. The unlock condition follows the parents.
- **Problems tab:** overlaps, overlong pages, links to steps that no longer exist.

Save (Ctrl+S) writes the book files, advancements, `en_us.json` and `layout_overrides.json`.
`build_book.py` applies `layout_overrides.json` last, so your edits survive a rebuild. A step you edit is saved
whole, so later generator changes to that step's text won't reach it; remove its entry from the
`entries` section of the overrides to hand it back to the generator.
