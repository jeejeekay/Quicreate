# Quicreate Skyblock walkthrough (PDF) — source

`build_guide.py` builds `Quicreate-Skyblock-Guide.pdf` from the pack's own files. Nothing about recipes,
drops, ores or structures is typed in by hand: it is read from the quest book, the CraftTweaker scripts,
this repo's datapack, every mod jar and the vanilla/Forge data. `guide.yaml` holds only the words and layout.

| File | What it is |
|---|---|
| `guide.yaml` | Chapter order, colours, intros, tips, per-quest notes, planets, in-game mechanics text, items to audit. **Edit this.** |
| `build_guide.py` | The builder (Python 3.10+). |
| `guide.css` | Page layout for the PDF. |
| `Quicreate-Skyblock-Guide.pdf` | The last build. |

## Rebuilding

Needs Python with `pyyaml`, `pillow`, `nbtlib` and `weasyprint`:

```
pip install pyyaml pillow nbtlib weasyprint
```

On Jake's PC, from the repo folder:

```
python guide/build_guide.py --out guide/build
```

Defaults: the instance is `~/AppData/Roaming/PrismLauncher/instances/Quicreate Skyblock RFA  0.9.0/minecraft`
(two spaces before 0.9.0), the repo is the folder above `guide/`, and vanilla + Forge data come from
`PrismLauncher/libraries` (`minecraft-1.20.1-client.jar` and the Forge `universal` jar). Override any of them:

```
--instance <minecraft folder>   --repo <Quicreate repo>   --vanilla <jar or folder> (repeat)   --out <folder>
```

The PDF and `build/guide.html` (+ `build/icons/`, `build/build_report.json`) land in `--out`. Copy the PDF
next to this README when you are happy with it.

In a Claude session (no shell on the PC) stage these files first, then run with the staged paths:
- `config/heracles/` (groups.txt and every quest JSON), `config/easy_skyblock_island/islands/*.nbt`,
  `scripts/*.zs`, every jar in `mods/`, `icon.png`
- the repo's `src/main/resources/data/**` and `assets/quicreate/lang`, `quicreate_cleanup_*.ps1`,
  `src/main/java/IGoByJake/quicreate/ModRegistry.java` (fishing rod tiers)
- vanilla 1.20.1 data/assets and Forge's generated data (the libraries folder, or public copies such as
  misode/mcmeta `1.20.1-data` / `1.20.1-assets` and MinecraftForge `1.20.1` `src/generated/resources`).
If only part of the repo is staged, add `--quicreate-jar-fallback` so missing files come from `mods/quicreate-*.jar`.

## When progression changes

- **Quest added, removed or re-linked**: just rebuild. Steps come from the quest book; order inside a chapter
  follows the quest arrows, then the recipe ingredients, then the book layout (top to bottom).
- **Recipe changed** (datapack, CraftTweaker, mod update): just rebuild. CraftTweaker `remove`/`addShaped`/
  `addShapeless`/`furnace.addRecipe` lines are applied on top of the datapacks. The cleanup script
  (`quicreate_cleanup_*.ps1`) is read and every file it deletes or renames is ignored.
- **Worldgen changed** (ores, biomes, structures): just rebuild; the planet boxes are read from the dimension,
  biome, feature and structure files.
- **New quest group**: add it to `chapters:` in `guide.yaml` (the builder appends unknown groups at the end and warns).
- **Better wording, a tip, a warning on a step**: `steps: <quest_id>: note: "..."` in `guide.yaml`.
  Text can use `**bold**`, `[[mod:item]]` (item with icon) and `[[#quest_id]]` (link to that step).
- **Wrong step order in a chapter**: `order: [quest_a, quest_b]` under that chapter puts those first.
- **Too many / too few alternative recipes**: `settings: recipe_score_cutoff`.
- **An item drawn by code (no texture)**: `icon_overrides:` points it at a real texture.
- **A hard-coded game mechanic** (axe stripping, cobble generator...): `mechanics:` (item id pattern → text).

After a build, check `build/build_report.json`: `no_source` (items a quest needs with no source anywhere),
`problems` (quest book references that do not resolve), `missing_icons`, `audit`.
