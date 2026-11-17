# Content for the short Quicreate Skyblock walkthrough.
# Each chapter: intro paragraphs, then sections; each section has prose and a step table.
# Step rows: (quest number, quest name, what the quest asks for, how to get it)

META = {
    "title": "Quicreate Skyblock RFA",
    "subtitle": "Short walkthrough · pack version 0.9.0 · Minecraft 1.20.1 Forge",
    "built": "Condensed 2026-11-11 from the full guide (built 2026-11-10 from the pack files).",
}

HOWTO = [
    "This is the short version of the walkthrough. Instead of one card per quest, each chapter is split into a few "
    "<b>stages</b>. A stage explains what you are building and why, then lists its quests in a table: the quest number "
    "(the same <b>#1–#220</b> numbering as the in-game quest book), what it asks for, and the quickest way to get it.",
    "Drop chances, sifting tables, the Mechanical Extruder list, fishing, card packs, bosses and what lives on each "
    "planet are in the separate <b>Reference</b> PDF. When this book says \"see Reference\", that is where to look. "
    "For full recipe grids, use JEI in game: the recipes in this pack are changed by CraftTweaker and the Quicreate "
    "datapack, so they can differ from the wiki.",
    "Numbers like <b>25%</b> are the chance per block sifted. <b>Superheated</b> and <b>heated</b> mean the heat "
    "level under a basin, which in this pack comes from Create: New Age heaters, not blaze burners.",
]

ROUTE = [
    ("island", "The Island", "Wood, a cobblestone generator, andesite alloy and your first Create parts.", "#1–#17"),
    ("sifting", "Sifting", "Mill cobble down to dust and sift it for every early metal.", "#18–#42"),
    ("newage", "New Age", "Sheets, solar heat, brass, the extruder and electricity.", "#43–#77"),
    ("improve", "Improvements", "Steel, motors, the circuit ladder and nuclear heat.", "#78–#98"),
    ("space", "Space", "Space suit, rocket fuel and the tier 1 rocket.", "#99–#116"),
    ("moon", "The Moon", "Desh, diamonds, the only stronghold and the Ender Dragon (soft ending).", "#117–#145"),
    ("mars", "Mars", "Ostrum, netherite, the Ancient Remnant and the netherite space suit.", "#146–#164"),
    ("venus", "Venus & Mercury", "Calorite, platinum and three bosses for the boss ingots.", "#165–#184"),
    ("glacio", "Glacio", "The last bosses: cursium, essence of the storm, ice crystal.", "#185–#200"),
    ("creative", "The Creative Ending", "Creative alloy, sheet, casing, motor and blaze cake (true ending).", "#201–#213"),
    ("cards", "Side: Cards & Mobs", "Card packs into spawn eggs, the Wither and the Flight Anchor. Any time after the sifter.", "#214–#220"),
]

CHAPTERS = [
# ---------------------------------------------------------------- ISLAND
{
 "key": "island", "title": "The Island", "label": "Chapter 1 · The Sky · steps #1–#17", "color": "#3f7d3a",
 "intro": [
   "You start on a small island in an endless ocean: grass and dirt, one oak tree, and a chest with a single "
   "<b>lava bucket</b>. That lava is the most valuable thing you own. Placed next to water it becomes your first "
   "cobblestone generator, and cobblestone is the raw material for almost everything in the first two chapters.",
   "The goal of this chapter is a steady supply of wood and cobblestone, then <b>andesite alloy</b>, the material "
   "every early Create part is made from. In this pack andesite alloy uses <b>charcoal</b>, so a furnace burning logs "
   "comes early.",
 ],
 "tips": [
   "Your inventory is kept on death (it can be changed in the config).",
   "Vein mining with the <b>~</b> key (Ore Excavation) takes a whole tree and its leaves in one go.",
   "Sneaking next to a sapling makes it grow faster.",
 ],
 "sections": [
  ("Wood and a cobblestone generator",
   ["Chop the tree, replant the saplings and keep a few spare: they become string later (#23). Build the "
    "cobblestone generator straight away (lava flowing next to water), because the next chapter mills a lot of it.",
    "Andesite here is crafted from cobblestone, and charcoal comes from smelting logs."],
   [(1, "Logs", "16 any logs", "Vein mine the starting tree"),
    (2, "Saplings", "4 any saplings", "Leaves; sneak beside saplings to grow them"),
    (3, "Get Crafting Table", "Crafting Table", "Planks"),
    (8, "Cobblestone", "32 cobblestone", "Lava from the starting chest flowing next to water"),
    (9, "furnace", "Furnace", "Cobblestone"),
    (10, "andesite", "8 andesite", "Crafted from cobblestone"),
    (14, "Charcoal", "8 charcoal", "Smelt logs in the furnace")]),
  ("About the pack (reading quests)",
   ["These quests only need to be ticked. They explain the idea of the pack: a skyblock you can finish in about "
    "ten hours the first time. The <b>soft ending</b> is killing the Ender Dragon, but the only stronghold is on the "
    "Moon, so you have to build a rocket to get there. The <b>true ending</b> is crafting the creative factory parts, "
    "which needs a boss from every planet and a solid automated factory.",
    "The three core mods are Ad Astra (space), Create: New Age (electricity and heat) and L_Ender's Cataclysm "
    "(bosses). Quicreate is the pack's own mod that ties them together."],
   [(4, "About This Modpack", "Read", "Tick it in the quest book"),
    (5, "Ad Astra", "Read", "Core mod 1: space"),
    (6, "Create: New Age", "Read", "Core mod 2: electricity"),
    (7, "Cataclysm", "Read", "Core mod 3: boss fights"),
    (11, "Quicreate Items", "Read", "New recipes and items"),
    (12, "Quicreate Weapons and Items", "Read", "Minor boss weapons"),
    (13, "Quicreate Endgame", "Read", "The creative tier")]),
  ("Andesite alloy and the first Create parts",
   ["Andesite alloy is charcoal plus andesite. Put it on a stripped log (axe it first) to make andesite casing. "
    "Shafts carry rotation and cogwheels change its direction and speed; together with casing they are the frame of "
    "every machine in the next chapter."],
   [(15, "Andesite Alloy", "16 andesite alloy", "Charcoal + andesite on a crafting table"),
    (16, "Andesite Casing", "4 andesite casing", "Use alloy on a stripped oak log"),
    (17, "Shafts & Cogwheels", "8 shafts, 4 cogwheels", "Shafts from alloy; cogwheel = shaft + planks")]),
 ]},
# ---------------------------------------------------------------- SIFTING
{
 "key": "sifting", "title": "Sifting", "label": "1.1 · Sifting · steps #18–#42", "color": "#9a7432",
 "intro": [
   "Sifting is how you get almost every raw material on the island. The chain is always the same: "
   "<b>mill</b> cobblestone into gravel, gravel into sand and sand into dust, then put those blocks through a "
   "<b>Sifter</b> holding a <b>mesh</b>. Each block gives different drops, and each better mesh "
   "(string → andesite → zinc → brass → advanced brass) unlocks better ones.",
   "A <b>waterlogged</b> sifter has its own drop tables: saplings and seeds from dirt, rubber, slime and clay from "
   "sand. Every table with its chances is in the Reference PDF.",
 ],
 "tips": [
   "The block you sift is the input; the mesh sits inside the sifter.",
   "This chain feeds the whole early game. Put the millstones and sifters on belts as soon as you can and let them run.",
   "Card packs drop from most sifting tables at low chances; see the Cards & Mobs side chapter.",
 ],
 "sections": [
  ("Rotation",
   ["Everything from here on needs rotation. Start with the hand crank, then a water wheel on flowing water. "
    "A windmill is the big early power source: windmill sail frames need no wool and stick without glue, and every "
    "8 sails adds power and speed."],
   [(18, "Hand Crank", "Hand Crank", "Planks + andesite alloy"),
    (19, "Water Wheel", "Water Wheel", "Planks + shaft"),
    (28, "Windmill Bearing", "Windmill Bearing", "Acacia slab + andesite + shaft"),
    (29, "Sails", "8 windmill sail frames", "Sticks + andesite alloy; no wool needed")]),
  ("The milling chain",
   ["A millstone turns cobblestone into gravel, gravel into sand and sand into dust. Milling saplings gives string, "
    "which you need for the first mesh."],
   [(20, "Mill", "Millstone", "Cogwheel + andesite casing + andesite"),
    (22, "Gravel", "16 gravel", "Mill cobblestone"),
    (27, "Sand", "16 sand", "Mill gravel"),
    (33, "Dust", "16 dust blocks", "Mill sand"),
    (23, "String", "8 string", "Mill saplings")]),
  ("The sifter and the mesh ladder",
   ["Each mesh is made from the one before it, so you climb the ladder in order. The brass mesh needs brass ingots, "
    "which only arrive in the New Age chapter (#63), so plan to come back for it."],
   [(21, "Sifter", "Sifter", "Planks + andesite casing + sticks + cogwheel + andesite"),
    (24, "Mesh", "String Mesh", "String + sticks"),
    (30, "Andesite Mesh", "Andesite Mesh", "Andesite alloy + iron nuggets + string mesh"),
    (35, "Zinc Mesh", "Zinc Mesh", "Zinc ingot + iron ingot + andesite mesh"),
    (38, "Brass Mesh", "Brass Mesh", "Brass ingot (#63) + gold ingot + zinc mesh")]),
  ("What to sift for",
   ["The early metals all come as nuggets, so these quests ask for 27 (three ingots' worth). Iron and zinc come from "
    "sand, copper from gravel, redstone from dust. The rare ones at the end (thorium, emeralds) are needed in "
    "chapter 1.3, so leave a brass-mesh sifter running on gravel and sand."],
   [(25, "Iron", "27 iron nuggets", "Sand: string mesh 25%, andesite mesh 50%"),
    (31, "Zinc", "27 zinc nuggets", "Sand: andesite mesh 25%, zinc mesh 35%"),
    (37, "Copper", "27 copper nuggets", "Gravel: zinc mesh 35%"),
    (36, "Gold", "27 gold nuggets", "Sand: zinc mesh 20%, brass mesh 50%"),
    (34, "Redstone", "16 redstone", "Dust: andesite mesh 20%, zinc mesh 40%"),
    (32, "Rubber", "8 rubber balls", "Waterlogged sifter, sand: andesite mesh 20% (up to 60%)"),
    (26, "New Saplings", "one of each other sapling + bamboo", "Waterlogged sifter, dirt, string mesh: 10% each"),
    (39, "Powdered Obsidian", "8 powdered obsidian", "Dust: brass mesh 20%"),
    (40, "Quartz", "16 nether quartz", "Soul sand: brass mesh 10%; gravel: advanced mesh 20%"),
    (41, "Thorium", "4 thorium", "Gravel: brass mesh 2.5%"),
    (42, "Emeralds", "4 emeralds", "Sand: brass mesh 1%")]),
 ]},
# ---------------------------------------------------------------- NEW AGE
{
 "key": "newage", "title": "New Age", "label": "1.2 · New Age · steps #43–#77", "color": "#b0581e",
 "intro": [
   "Blaze burners are out of reach in this pack, so heat comes from <b>Create: New Age</b>: solar heating plates and "
   "heaters, moved around with heat pipes and pumps. Heated mixing makes <b>brass</b>, which unlocks the brass mesh, "
   "brass casing and the Mechanical Extruder.",
   "The second half of the chapter is <b>electricity</b>: a Generator Coil spun while touching magnetite makes power, "
   "carbon brushes take it out, and an Energiser uses it to make overcharged metals and blaze powder.",
 ],
 "tips": [
   "Solar heat only works in daylight. Nuclear heat in the next chapter is the night-time answer.",
   "Several quests in this chapter have no arrows in the quest book. That is on purpose; the order below works.",
   "Quest #48 (Blaze Burner) only catches a burner made outside the intended route. You don't need one.",
 ],
 "sections": [
  ("The press, sheets and wires",
   ["The mechanical press needs a <b>block of iron</b> (81 iron nuggets), which is the first real grind: keep the "
    "sand sifters running. Pressing ingots on a depot or belt gives sheets, and a mechanical saw cuts copper sheets "
    "into wire."],
   [(43, "Mechanical Press", "Mechanical Press", "Shaft + andesite casing + block of iron"),
    (47, "Sheet Metal", "8 iron, 4 copper, 4 golden sheets", "Press ingots on a depot or belt"),
    (51, "Mechanical Saw", "Mechanical Saw", "Iron sheet + iron ingot + andesite casing"),
    (58, "Wires", "16 copper wire", "Saw copper sheets"),
    (46, "Crushing is The New Sifting", "2 crushing wheels", "Andesite alloy + planks + andesite")]),
  ("Heat",
   ["Solar heating plates collect heat in daylight and a heater turns it into heat for the basin above it. "
    "Heat pipes and pumps move heat from the plates to where you need it, and a Stirling engine turns spare heat "
    "into rotation. Heated mixing makes brass; superheated mixing (more heat) turns cobblestone into lava."],
   [(44, "Heat Generation", "Read", "Solar heat replaces blaze burners"),
    (49, "Solar Plate", "2 basic solar heating plates", "Sheets + zinc + glass"),
    (50, "Heater", "Heater", "Copper sheet + zinc + cauldron + furnace"),
    (54, "Basin", "Basin", "Andesite alloy"),
    (55, "Heat Pipes", "8 heat pipes", "Copper sheet + zinc"),
    (56, "Heat Pumps", "2 heat pumps", "Copper sheet + zinc"),
    (57, "Stirling Engine", "Stirling Engine", "Copper sheet + zinc + shaft"),
    (60, "Mixer", "Mechanical Mixer", "Cogwheel + andesite casing + whisk"),
    (61, "Lava", "1 lava bucket", "Superheated mixing turns cobblestone into lava"),
    (48, "Blaze Burner?", "(not needed)", "Trap quest for off-route burners")]),
  ("Brass",
   ["Copper and zinc in a heated mixer make brass. Now go back and make the <b>brass mesh</b> (#38) and finish the "
    "brass-mesh sifting quests in the Sifting chapter."],
   [(63, "Brass", "16 brass ingots", "Copper + zinc, heated mixer"),
    (64, "Brass Casing", "8 brass casing", "Brass on a stripped log")]),
  ("The Mechanical Extruder and Create ores",
   ["The extruder makes a block forever from lava and water beside it. With nothing special below it makes "
    "stone; the <b>block underneath</b> changes the output and is never used up. Put a block of iron, copper, zinc or "
    "gold under it to get Create's ore stones, then crush those for crushed ores. This is the end of the nugget "
    "grind. The full list of catalysts is in the Reference PDF."],
   [(65, "Mechanical Extruder", "Mechanical Extruder", "Mechanical press + glass + brass casing"),
    (66, "Crimsite", "32 crimsite", "Block of iron below; crush for iron (and redstone)"),
    (67, "Veridium", "32 veridium", "Block of copper below; crush for copper (and clay)"),
    (68, "Asurine", "32 asurine", "Block of zinc below; crush for zinc (and gunpowder)"),
    (69, "Ochrum", "32 ochrum", "Block of gold below; crush for gold (and quartz)")]),
  ("Electricity",
   ["The Generator Coil is a 5×5 mechanical crafting recipe, so you need 21 mechanical crafters, and each crafter "
    "needs an electron tube (polished rose quartz on an iron sheet; rose quartz is quartz + 8 redstone). Spin the coil "
    "while it touches up to 12 magnetite blocks; stronger magnets make more power for the same rotation. Carbon brushes "
    "on the end of the coil take the power out, and connectors carry it to the Energiser."],
   [(45, "Electricity", "Read", "Tools for electricity"),
    (52, "Magnetite", "8 magnetite blocks", "Andesite alloy + iron sheet + redstone"),
    (72, "Electron Tubes", "8 electron tubes", "Polished rose quartz + iron sheet"),
    (73, "Mechanical Crafters", "21 mechanical crafters", "Electron tube + brass casing + crafting table"),
    (74, "Generator Coil", "Generator Coil", "5×5 mechanical crafting: copper wire, iron, zinc block"),
    (53, "Carbon Brush", "Carbon Brushes", "Zinc + copper sheet + coal + shaft"),
    (59, "Connector", "8 electrical connectors", "Zinc + copper sheet"),
    (62, "Energizer", "Basic Energiser", "Andesite casing + lightning rod")]),
  ("Energised materials and assembly",
   ["The Energiser charges items with stored power. Overcharged iron and gold feed the circuits in the next chapter, "
    "and energised gunpowder is the pack's blaze powder. The deployer opens up sequenced assembly, starting with the "
    "precision mechanism."],
   [(70, "Overcharged Iron", "8 overcharged iron", "Energise iron ingots (1000 energy)"),
    (75, "Overcharged Gold", "8 overcharged gold", "Energise gold ingots (2000 energy)"),
    (71, "Blaze Powder", "8 blaze powder", "Energise gunpowder (2000 energy)"),
    (76, "Deployer", "Deployer", "Electron tube + andesite casing + brass hand"),
    (77, "Precision Mechanism", "4 precision mechanisms", "Sequenced assembly on a golden sheet, 5 loops")]),
 ]},
# ---------------------------------------------------------------- IMPROVEMENTS
{
 "key": "improve", "title": "Improvements", "label": "1.3 · Improvements · steps #78–#98", "color": "#2c8466",
 "intro": [
   "This chapter builds the parts every later machine and rocket uses: <b>steel</b>, <b>motors</b> and the "
   "<b>circuit ladder</b>. Circuits are made by sequenced assembly, and each tier is built from the one below it "
   "(blank → copper → emerald, then amethyst and ancient metal on the planets), so the cost multiplies as you go up.",
   "It also adds <b>nuclear heat</b>: a reactor gives heat at night, when the solar plates stop.",
 ],
 "tips": [
   "Build one sequenced assembly line per circuit type and leave it running. You will need far more circuits than the quests ask for.",
   "Thorium (#41) and emeralds (#42) are the slow inputs here; keep a brass-mesh sifter on gravel and sand.",
 ],
 "sections": [
  ("Steel and motors",
   ["Steel is iron and charcoal in a <b>superheated</b> mixer, so it needs a strong heat setup. Motors put rotation "
    "anywhere from electricity; motor extensions multiply their output. Better magnets also make the generator coil "
    "more efficient."],
   [(78, "Steel", "32 steel ingots", "Iron + charcoal, superheated mixer"),
    (79, "Motors", "Basic Motor", "Iron sheet + andesite casing + magnetite + shaft"),
    (81, "Redstone Magnet", "4 redstone magnets", "Magnetite + overcharged iron sheet + redstone"),
    (89, "Layered Magnet", "2 layered magnets", "Redstone magnet + overcharged gold and iron sheets"),
    (86, "Motor Extension", "Basic Motor Extension", "Iron sheet + copper circuit + redstone magnet"),
    (92, "Strong Motor", "Advanced Motor", "Mechanical crafting: emerald circuit, layered magnet, brass casing")]),
  ("The circuit ladder",
   ["<b>Plastic</b> comes from compacting card bits (sawn Allay cards) with blaze powder in a heated basin, or from "
    "mixing oil with blaze powder when superheated. A <b>blank circuit</b> is an overcharged golden sheet with copper "
    "wire and plastic. Copper circuits add overcharged iron wire and quartz over 3 loops; emerald circuits add electron "
    "tubes and copper circuits to an emerald wafer, also over 3 loops."],
   [(83, "Plastic", "8 plastic", "Card bits + blaze powder (heated), or oil + blaze powder (superheated)"),
    (84, "Blank Circuit", "8 blank circuits", "Overcharged golden sheet + copper wire + plastic"),
    (85, "Copper Circuit", "8 copper circuits", "Blank circuit + overcharged iron wire + quartz, 3 loops"),
    (90, "Emerald Wafer", "2 emerald wafers", "Cut an emerald, then energise it"),
    (91, "Emerald Circuit", "4 emerald circuits", "Emerald wafer + electron tubes + copper circuits, 3 loops"),
    (87, "Moon Stuff", "Read", "Copper circuits also feed the space parts")]),
  ("Nuclear heat",
   ["Crushing thorium gives radioactive thorium, which becomes nuclear fuel. The reactor is built from reactor "
    "casing; each rod must be covered on every side by reactor parts, and the heat vents export the heat (or it builds "
    "up). The fuel acceptor and heat vent need steel plates (#99), so finish them after steel."],
   [(80, "Nuclear Heat", "4 radioactive thorium", "Crush thorium"),
    (82, "Nuclear Fuel", "4 nuclear fuel", "Radioactive thorium on an iron plate, 1 loop"),
    (94, "Reactor Case", "16 reactor casing", "Energised bricks + iron sheet, pressed"),
    (95, "Fuel Inserter", "Reactor Fuel Acceptor", "Reactor casing + funnel + steel plate + emerald circuit"),
    (96, "Reactor Rod", "2 reactor rods", "Mechanical crafting: casing, golden sheet, reactor glass, fuel"),
    (97, "Heat Vent", "2 reactor heat vents", "Casing + heat pump + emerald circuit + steel plate")]),
  ("Upgrades",
   ["Better solar plates, an advanced energiser and the storage terminal, which lets you use vaults and chests "
    "like one big inventory."],
   [(88, "Advanced Solar Plate", "2 advanced solar heating plates", "Basic plate + copper circuit + overcharged gold + quartz"),
    (98, "Advanced Energizer", "Advanced Energiser", "Basic energiser + emerald circuit + overcharged gold"),
    (93, "Storage Terminals", "Storage Terminal", "Acacia slab + emerald circuit + list filter")]),
 ]},
# ---------------------------------------------------------------- SPACE
{
 "key": "space", "title": "Space", "label": "1.4 · Space · steps #99–#116", "color": "#3d5f8f",
 "intro": [
   "Everything for the tier 1 rocket. Nearly every part is steel plate, so start by pressing a big batch. The suit "
   "keeps you alive on the Moon, the oxygen loader fills it, and the fuel refinery turns oil into rocket fuel.",
   "The rocket is assembled in the <b>NASA Workbench</b> from a nose cone, fins, steel tanks and a steel engine, "
   "then placed on a launch pad.",
 ],
 "tips": [
   "Bring fuel for the trip home, or plan to make it on the Moon.",
   "Moon villages and towers also have suit parts, tanks and fuel in their chests, but don't count on it.",
 ],
 "sections": [
  ("Steel plates and the suit",
   ["You need the full suit: helmet, suit, pants and boots. Gas tanks hold oxygen; the large gas tank is a spare "
    "to refill the suit. The oxygen loader makes oxygen from water."],
   [(99, "Steel Plates", "32 steel plates", "Press steel ingots"),
    (101, "Space Helmet", "Space Helmet", "Steel plate + glass"),
    (102, "Gas Tanks", "6 gas tanks", "Iron sheets + iron rod"),
    (103, "Space Suit", "Space Suit", "Wool + emerald circuit + gas tank + steel plate"),
    (107, "Space Pants", "Space Pants", "Steel plate + wool"),
    (110, "Space Boots", "Space Boots", "Steel plate + wool"),
    (104, "Large Gas Tank", "Large Gas Tank", "Steel plates + rod + gas tank"),
    (108, "Oxygen Loader", "Oxygen Loader", "Reactor casing + copper circuit + gas tank + nuclear fuel")]),
  ("The rocket",
   ["The rocket fan (steel rocket propeller) goes into the steel engine, which also needs an emerald circuit. "
    "Build the NASA workbench, assemble the rocket in it, and put down a launch pad."],
   [(100, "Nose Cone & Fins", "1 nose cone, 4 fins", "Steel plates + lightning rod; fins from steel rods"),
    (105, "Steel Tanks", "2 steel tanks", "Steel plate + steel rod + gas tank"),
    (106, "Rocket Fan", "2 steel rocket propellers", "Steel around a propeller"),
    (111, "Steel Engine", "Steel Engine", "Steel plate + emerald circuit + engine frame + propeller"),
    (109, "Nasa Workbench", "Rocket Assembly Bench", "Steel plate + copper circuit + mechanical arm + crafting table"),
    (112, "Rocket", "Tier 1 Rocket", "NASA workbench: nose cone, fins, steel tanks, engine"),
    (114, "Launch Pad", "Launch Pad", "Steel plates + steel rod")]),
  ("Rocket fuel",
   ["Oil comes from rubber balls in a superheated mixer (rubber is from the waterlogged sifter, #32). The fuel "
    "refinery turns oil into rocket fuel."],
   [(113, "Oil", "1 oil bucket", "Rubber balls, superheated mixer; fill a bucket"),
    (115, "Fuel Refinery", "Fuel Refinery", "Reactor casing + copper circuit + fluid tank + nuclear fuel"),
    (116, "Rocket Fuel", "3 fuel buckets", "Fuel refinery from oil")]),
 ]},
# ---------------------------------------------------------------- MOON
{
 "key": "moon", "title": "The Moon", "label": "Chapter 2 · The Moon · steps #117–#145", "color": "#5d6280",
 "intro": [
   "The Moon has the only stronghold in the pack, so the soft ending happens here: find it with eyes of ender, go "
   "through the portal and kill the Ender Dragon. It also has <b>desh</b>, the first space metal, and three mobs worth "
   "farming: <b>star crawlers</b> (a diamond every kill), <b>endermen</b> (ender pearls) and <b>amethyst crabs</b>.",
   "Back home, desh plates make the <b>advanced brass mesh</b>, which turns your sifters into a source of diamonds, "
   "emeralds, lapis and the planet metals.",
 ],
 "tips": [
   "Moon ores: desh (Y −80 to 80), ice shards (Y −32 to 32), iron, and cheese. The full Moon page is in the Reference PDF.",
   "Ender golems in the Ruined Citadel always drop a void core. Void cores are needed again later (spawners, enderite).",
 ],
 "sections": [
  ("Landing and the soft ending",
   ["Twelve eyes of ender need twelve pearls and blaze powder. The Ruined Citadel is a fortress on the lunar "
    "wastelands with ender golems (void cores) and the optional Ender Guardian boss."],
   [(117, "One Small Step", "Travel to the Moon", "Rocket + launch pad + suit + fuel"),
    (119, "Ender Pearls", "12 ender pearls", "Endermen on the Moon (100% per kill)"),
    (125, "Eyes of Ender", "12 eyes of ender", "Ender pearl + blaze powder"),
    (128, "The Stronghold", "Find the stronghold", "Lunar wastelands; follow the eyes"),
    (134, "The End", "Travel to the End", "The stronghold's portal"),
    (140, "Free the End", "Defeat the Ender Dragon", "The soft ending"),
    (118, "Ruined Citadel", "Find the Ruined Citadel", "Lunar wastelands"),
    (126, "Void Core", "2 void cores", "Ender golems in the citadel"),
    (127, "Ender Guardian", "Defeat the Ender Guardian", "Optional boss in the citadel")]),
  ("Moon materials",
   ["Moon cobblestone can come from the extruder (moon cobblestone below), and milled into moon sand it can be "
    "sifted with the advanced mesh. Ice shards energised at 10,000 energy become etrium."],
   [(120, "Moon Cobblestone", "32 moon cobblestone", "Mine moon stone, or extruder with moon cobble below"),
    (129, "Moon Sand", "16 moon sand", "Mill moon cobblestone"),
    (121, "Desh", "16 desh ingots", "Smelt raw desh (ore Y −80 to 80)"),
    (130, "Desh Plates", "16 desh plates", "Press desh ingots"),
    (122, "Diamonds", "8 diamonds", "Star crawlers (100% per kill)"),
    (123, "Amethyst", "16 amethyst shards", "Amethyst crabs; moon sand advanced mesh 10%"),
    (124, "Ice Shards", "16 ice shards", "Ice shard ore (Y −32 to 32)"),
    (133, "Etrium", "4 etrium ingots", "Energise ice shards (10,000) into nuggets"),
    (131, "Overcharged Diamond", "4 overcharged diamonds", "Energise diamonds (10,000)"),
    (132, "Amethyst Wafer", "2 amethyst wafers", "Polish, cut and energise amethyst"),
    (135, "Advanced Brass Mesh", "Advanced Brass Mesh", "Desh plates + steel plates + brass mesh")]),
  ("Moon tech and the tier 2 rocket",
   ["Amethyst circuits sit on top of emerald circuits and need overcharged diamond wire. They go into the desh "
    "engine, the chunk loader and the smart crafter. Etrium makes the etrionic capacitor and core, used on Mars and "
    "later."],
   [(136, "Fluxuated Magnetite", "2 fluxuated magnetite", "Layered magnet + overcharged iron sheet + overcharged diamond"),
    (137, "Amethyst Circuit", "4 amethyst circuits", "Emerald circuit + amethyst wafer + diamond wire, 3 loops"),
    (138, "Etrionic Capacitor", "2 etrionic capacitors", "Steel plate + etrium rod + emerald circuit"),
    (139, "Etrionic Core", "Etrionic Core", "Steel plate + etrium rods"),
    (141, "Desh Tanks", "4 desh tanks", "Desh plate + gas tank + steel tank"),
    (142, "Desh Engine", "Desh Engine", "Desh plates + amethyst circuit + desh pipe + frame + propeller"),
    (145, "Tier 2 Rocket", "Tier 2 Rocket", "NASA workbench: desh plates, tanks, engine"),
    (143, "Smart Crafter", "Smart Crafter (optional)", "Mechanical crafting: amethyst circuit + crafter"),
    (144, "Chunk Loader", "Andesite Chunk Loader (optional)", "Mechanical crafting: amethyst circuit + casing")]),
 ]},
# ---------------------------------------------------------------- MARS
{
 "key": "mars", "title": "Mars", "label": "Chapter 3 · Mars · steps #146–#164", "color": "#a23a28",
 "intro": [
   "Mars has <b>ostrum</b> (only here), diamonds as ore, and <b>ancient debris</b> in the Mars rock at Y 90 to 130. "
   "Netherite and ancient metal from the <b>Ancient Remnant</b> (Cursed Pyramid) lead to the ancient metal circuit, "
   "the ostrum engine and the <b>netherite space suit</b>, which Venus and Mercury require.",
   "The netherite suit is the big cost of this chapter: four netherite ingots on full diamond armour, plus four "
   "upgrade templates (eight netherrack around a diamond). Start collecting diamonds and debris early.",
 ],
 "tips": [
   "Cataclysm's cursium armour also counts for the heat-protection quest, but cursium only comes on Glacio.",
   "Koboletons and wadjets in the desert site and desert village drop ancient metal nuggets, another route to ancient metal.",
 ],
 "sections": [
  ("Ostrum and netherite",
   ["Mill Mars cobblestone into Mars sand and sift it with the advanced mesh for ostrum nuggets, iron, ice and the "
    "odd diamond. Ancient debris is mostly mined at Y 90 to 130; sifting conglomerate gives it at only 0.5%."],
   [(146, "The Red Planet", "Travel to Mars", "Tier 2 rocket"),
    (147, "Martian Sifting", "16 Mars sand", "Mill Mars cobblestone"),
    (148, "Ostrum", "16 ostrum ingots", "Smelt raw ostrum (ore Y −80 to 80)"),
    (152, "Ostrum Plates", "16 ostrum plates", "Press ostrum ingots"),
    (149, "Ancient Debris", "4 ancient debris", "Mine at Y 90–130; conglomerate sift 0.5%"),
    (153, "Netherite", "2 netherite ingots", "4 netherite scrap + 4 gold")]),
  ("The Ancient Remnant",
   ["The Cursed Pyramid sits on the Martian wastelands. The Ancient Remnant drops a block of ancient metal, which "
    "becomes ancient metal wafers and then the ancient metal circuit (it also needs etrionic capacitors and amethyst "
    "circuits)."],
   [(150, "Cursed Pyramid", "Find the Cursed Pyramid", "Martian wastelands"),
    (151, "Ancient Remnant", "Defeat the Ancient Remnant", "Boss in the pyramid"),
    (154, "Ancient Metal", "4 ancient metal ingots", "Boss block, or nuggets from koboletons/wadjets"),
    (155, "Ancient Metal Wafer", "2 ancient metal wafers", "Press and energise ancient metal"),
    (156, "Ancient Metal Circuit", "4 ancient metal circuits", "Etrionic capacitor + amethyst circuit + wafer, 3 loops")]),
  ("Heat suit and the tier 3 rocket",
   ["The reinforced motor uses sturdy casing (a sturdy sheet on brass casing). The three optional machines here "
    "automate mobs and chunk loading."],
   [(159, "Netherite Space Suit", "Netherite helmet, suit, pants, boots", "Netherite armour + ostrum plates (+ circuit, tanks)"),
    (160, "Ostrum Tanks", "4 ostrum tanks", "Ostrum plate + gas tank + desh tank"),
    (161, "Ostrum Engine", "Ostrum Engine", "Ostrum plates + ancient metal circuit + pipe + frame + propeller"),
    (164, "Tier 3 Rocket", "Tier 3 Rocket", "NASA workbench: ostrum plates, tanks, engine"),
    (157, "Reinforced Motor", "Reinforced Motor", "Sturdy casing + amethyst circuit + fluxuated magnetite"),
    (158, "Soul Catcher", "Empty Soul Catcher (optional)", "Sturdy casing + shulker shell + circuit + void core"),
    (162, "Brass Chunk Loader", "Brass Chunk Loader (optional)", "Andesite chunk loader + ancient metal circuit"),
    (163, "Mechanical Spawner", "Mechanical Spawner (optional)", "Sturdy casing + ancient metal circuit + void core")]),
 ]},
# ---------------------------------------------------------------- VENUS & MERCURY
{
 "key": "venus", "title": "Venus and Mercury", "label": "Chapter 4 · Venus & Mercury · steps #165–#184", "color": "#b26a14",
 "intro": [
   "Both planets are hot: wear the netherite space suit (or cursium armour) before you land. You need both of them "
   "for the tier 4 rocket.",
   "<b>Venus</b> has calorite, the Ancient Factory (the Harbinger, who drops witherite) and the Fungal Forest. "
   "<b>Mercury</b> is the only source of platinum, and has the Burning Arena (Ignis, ignitium) and the Soul Black "
   "Smith (the Netherite Monstrosity).",
 ],
 "tips": [
   "Umvuthi's grove (Umvuthana Grove) is only in the Venus Fungal Forest biome, even though the quest text says wastelands.",
   "The Etrionic Blast Furnace at the end doubles boss ingots by alloying. Build it before spending boss drops.",
 ],
 "sections": [
  ("Venus",
   ["Calorite ore is between Y −80 and 80. The Harbinger in the Ancient Factory drops a block of witherite; more "
    "witherite comes from netherite + calorite in a superheated mixer."],
   [(165, "Acid Rain", "Travel to Venus", "Tier 3 rocket + netherite space suit"),
    (167, "Calorite", "16 calorite ingots", "Smelt raw calorite (ore Y −80 to 80)"),
    (173, "Calorite Plates", "24 calorite plates", "Press calorite ingots"),
    (168, "Ancient Factory", "Find the Ancient Factory", "Barrens, dunes or Fungal Forest"),
    (169, "The Harbinger", "Defeat the Harbinger", "Boss in the factory"),
    (175, "Witherite", "4 witherite ingots", "Boss block, or netherite + calorite superheated"),
    (174, "Umvuthi", "Defeat Umvuthi (optional)", "Umvuthana Grove, Fungal Forest only")]),
  ("Mercury",
   ["Platinum ore is between Y 0 and 30. Ignited berserkers drop dying embers, which craft into burning ashes; "
    "platinum + burning ashes in a superheated mixer makes ignitium, and Ignis drops three ingots directly."],
   [(166, "Closest to the Sun", "Travel to Mercury", "Tier 3 rocket + netherite space suit"),
    (170, "Platinum", "16 platinum", "Smelt raw platinum (ore Y 0 to 30)"),
    (171, "Burning Arena", "Find the Burning Arena", "Mercury"),
    (177, "Ignis", "Defeat Ignis", "Boss in the arena"),
    (176, "Burning Ashes", "4 burning ashes", "Dying embers from ignited berserkers"),
    (179, "Ignitium", "4 ignitium ingots", "Ignis drop, or platinum + burning ashes superheated"),
    (172, "Soul Black Smith", "Find the Soul Black Smith", "Mercury"),
    (178, "Netherite Monstrosity", "Defeat the Netherite Monstrosity", "Boss in the smithy")]),
  ("Tier 4 rocket and the jet suit",
   ["The calorite engine builds on the ostrum engine and needs ignitium. The jet suit upgrades the netherite suit "
    "(ignitium armour also counts)."],
   [(180, "Calorite Engine", "Calorite Engine", "Calorite plates + ignitium + ostrum engine"),
    (181, "Calorite Tanks", "4 calorite tanks", "Calorite plate + gas tank + ostrum tank"),
    (182, "Jet Suit", "Jet suit helmet, suit, pants, boots", "Netherite space suit + calorite + capacitor"),
    (183, "Tier 4 Rocket", "Tier 4 Rocket", "NASA workbench: calorite plates, tanks, engine"),
    (184, "Etrionic Blast Furnace", "Etrionic Blast Furnace", "Witherite + calorite engine + circuit + core")]),
 ]},
# ---------------------------------------------------------------- GLACIO
{
 "key": "glacio", "title": "Glacio", "label": "Chapter 5 · Glacio · steps #185–#200", "color": "#2a7f9e",
 "intro": [
   "The last world holds the last three required bosses, and each gives one ingredient of the creative parts: "
   "<b>Maledictus</b> (Frosted Prison) gives cursium, <b>Scylla</b> (Acropolis) gives the essence of the storm, and "
   "the <b>Frostmaw</b> gives the ice crystal. The Sunken City (Leviathan) and the Ferrous Wroughtnaut are optional.",
   "Glacio also has ordinary ores (coal, copper, iron, lapis) and permafrost, which the cryo freezer turns into cryo fuel.",
 ],
 "tips": [
   "Plan your creative items before spending essence of the storm: each creative alloy needs one.",
   "Draugr in the abandoned spires and temples drop black steel; the Etrionic Blast Furnace can alloy it too.",
 ],
 "sections": [
  ("The Frosted Prison: cursium",
   ["Black steel from draugr plus ender pearls makes void steel; void steel + platinum makes cursium, and "
    "Maledictus drops 3–4 cursium ingots."],
   [(185, "The Frozen World", "Travel to Glacio", "Tier 4 rocket"),
    (186, "Frosted Prison", "Find the Frosted Prison", "Ice peaks or helix spires"),
    (192, "Black Steel", "4 black steel ingots", "Draugr drops, or alloying"),
    (193, "Maledictus", "Defeat Maledictus", "Boss in the prison"),
    (198, "Void Steel", "4 void steel ingots", "Black steel + ender pearl, superheated"),
    (199, "Cursium", "4 cursium ingots", "Maledictus drop, or void steel + platinum")]),
  ("The Acropolis and the Frostmaw",
   ["Scylla's loot table gives 3–4 essence of the storm and 8–16 lacrima. The Frostmaw gives one ice crystal."],
   [(188, "Acropolis", "Find the Acropolis", "Ice peaks or helix spires"),
    (195, "Scylla", "Defeat Scylla", "Boss in the Acropolis"),
    (200, "Essence of the Storm", "1 essence of the storm", "Scylla drop"),
    (190, "Frostmaw", "Defeat the Frostmaw", "Frostmaw spawn site"),
    (197, "Ice Crystal", "1 ice crystal", "Frostmaw drop")]),
  ("Cryo fuel and the optional bosses",
   ["The cryo freezer makes cryo fuel from ice; the creative sheet uses it in every loop."],
   [(189, "Cryo Freezer", "Cryo Freezer", "Ostrum plate + permafrost + circuit + refinery + core"),
    (196, "Cryo Fuel", "1 cryo fuel bucket", "Cryo freezer"),
    (187, "Sunken City", "Find the Sunken City (optional)", "Snowy barrens or Glacian woods"),
    (194, "The Leviathan", "Defeat the Leviathan (optional)", "Sunken City"),
    (191, "Ferrous Wroughtnaut", "Defeat the Wroughtnaut (optional)", "Wrought chamber")]),
 ]},
# ---------------------------------------------------------------- CREATIVE
{
 "key": "creative", "title": "The Creative Ending", "label": "Endgame · Creative · steps #201–#213", "color": "#7a3c9c",
 "intro": [
   "Everything comes together. Cursium, ignitium, witherite and essence of the storm make the <b>creative alloy</b>. "
   "Sixteen loops of sequenced assembly (cryo fuel, ice crystal, sturdy sheets and pressing) make the <b>creative "
   "sheet</b>, which goes on a block of enderite for the creative casing. The <b>Mechanical Fusion Anvil</b> turns a "
   "rotation speed controller and a blaze cake into the creative motor and the creative blaze cake.",
   "Finishing the casing, motor and cake (and the dragon) completes the pack: the true ending.",
 ],
 "tips": [
   "Each creative alloy uses one essence of the storm; you need at least three alloys (sheet, motor, cake).",
   "The three Quicreate swords are optional and can be made earlier.",
 ],
 "sections": [
  ("Materials",
   ["Sturdy sheets are powdered obsidian and lava in sequenced assembly. Enderite is netherite + void core + void "
    "steel; four ingots compact into the block the casing needs."],
   [(201, "Sturdy Sheets", "16 sturdy sheets", "Powdered obsidian + 500 mB lava, 1 loop"),
    (202, "Enderite", "4 enderite ingots", "Netherite + void core + void steel, superheated"),
    (206, "Block of Enderite", "Block of Enderite", "Compact 4 enderite (superheated)"),
    (203, "Mechanical Fusion Anvil", "Mechanical Fusion Anvil", "Witherite + block of redstone + anvil")]),
  ("The creative parts",
   ["The creative alloy is mixed superheated from the four boss materials plus iron."],
   [(204, "Creative Alloy", "1 creative alloy", "Cursium + ignitium + witherite + essence + 4 iron"),
    (205, "Creative Sheet", "1 creative sheet", "Creative alloy, 16 loops: cryo fuel, ice crystal, sturdy sheet"),
    (207, "Creative Motor", "Creative Motor", "Fusion anvil: speed controller + creative alloy"),
    (208, "Creative Blaze Cake", "Creative Blaze Cake", "Fusion anvil: blaze cake + creative alloy"),
    (209, "Creative Casing", "Creative Casing", "Creative sheet on a block of enderite"),
    (210, "Quicreate Complete", "Claim your victory", "The true ending")]),
  ("Optional weapons",
   [],
   [(211, "Ancient Gilded Sword", "Ancient Gilded Sword", "Ostrum plate + ancient metal wafer + netherite"),
    (212, "Maptera Razor Sword", "Maptera Razor Sword", "Void jaw (Endermaptera) + diamond + void core"),
    (213, "Platinum Master Sword", "Platinum Master Sword", "Platinum + etrium + calorite + netherite")]),
 ]},
# ---------------------------------------------------------------- CARDS
{
 "key": "cards", "title": "Side chapter: Cards and Mobs", "label": "Side · Cards & Mobs · steps #214–#220", "color": "#2a7a78",
 "intro": [
   "There are no natural animals on the island. Instead, most sifting tables drop <b>card packs</b> at small "
   "chances. Open a pack for cards, and craft mob cards into <b>spawn eggs</b>. Common packs hold the farm animals; "
   "rare packs hold villagers and the Allay (whose cards also make plastic). This chapter can be done any time "
   "after you have a sifter.",
   "Smelting an uncommon pack gives a <b>nether pack</b>, the route to wither skeletons and the Wither, whose nether "
   "star powers the Flight Anchor.",
 ],
 "tips": [
   "Which packs drop from which sifting table, and which cards are in each pack, is in the Reference PDF.",
   "A deployer holding shears opens packs automatically.",
 ],
 "sections": [
  ("Cards, animals and the Wither",
   [],
   [(214, "Card Packs", "Any card pack", "Rare sifting drop (most tables)"),
    (215, "Farm Animals", "Sheep and chicken spawn eggs", "Cards from common packs"),
    (216, "Nether Pack", "Nether Card Pack", "Smelt an uncommon pack"),
    (217, "Wither Skeletons", "3 wither skeleton skulls", "Wither skeletons (2.5%); eggs from nether-pack cards"),
    (218, "The Wither", "Defeat the Wither", "Nether star"),
    (219, "Flight Anchor", "Flight Anchor", "Beacon + sturdy casing + overcharged diamond + circuit"),
    (220, "Villagers", "Villager spawn egg", "Card from rare packs")]),
 ]},
]
