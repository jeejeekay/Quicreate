"""Hand-written text for the Quicreate guide book (Modonomicon). Markdown as Modonomicon reads it.

Item links are written [[namespace:item]] and quest links [[#quest_id]]; build_book.py turns them into
Modonomicon item:// and entry:// links. Keep sentences short: a book page holds about 11 lines of 22 characters.
"""

BOOK_NAME = 'Quicreate Skyblock Guide'
BOOK_TOOLTIP = 'Your guide, quest log and field journal'

# ------------------------------------------------------------------ Field Guide: welcome
WELCOME = [
    ('Welcome!', "This book is your quest log and your guide in one. Every tab is a chapter. Every icon is a "
                 "step: open it to see what to get and how to get it."),
    ('Reading the map', "**Lit icons** are ready to do. **Grey icons** are locked: hover them to see what unlocks "
                        "them. A blue dot means something new to read."),
    ('Shapes', "[#](3b3b3b)**Square**[#]() steps are the main route.  \n"
               "[#](a07800)**Gold star**[#]() steps are milestones.  \n"
               "**Round** icons are optional or just for reading."),
    ('Finishing a step', "Steps finish on their own the moment you have the items, kill the boss or reach the "
                         "place. A toast pops up and the step gets a **Completed** page with links to what's next."),
    ('Side Paths', "The **Side Paths** tab holds optional goals: building sets, exploring, hunting, automation, "
                   "food and cards. Each one gives a reward picked to help the main route."),
    ('Lost your book?', "Craft a new one from a [[minecraft:book]] and a [[minecraft:cobblestone]]. Your progress "
                        "is saved with you, not the book."),
]

ISLAND_TIPS = [
    ('Island tips', "- Vein mine a whole tree with the **~** key.\n- Sneak next to a sapling to grow it faster.\n"
                    "- Your inventory is kept when you die.\n\n"),
    ('The lava bucket', "The chest holds one [[minecraft:lava_bucket]]. Lava flowing into water makes "
                        "cobblestone forever. Don't lose it!"),
]

# Reading-only entries for the Field Guide. Each: id, title, icon, column, row, gate (quest id or None), pages
# A page is (title, text) or ('@multiblock', id, name, text) or ('@image', texture, title, text)
# or ('@entity', entity id, text) or ('@spotlight', item, title, text).
FIELD = [
    # ---------------- column 0: the island
    dict(id='welcome', title='How to use this book', icon='minecraft:book', col=0, row=0, gate=None,
         star=True, pages='WELCOME'),
    dict(id='island_tips', title='Island survival', icon='minecraft:oak_sapling', col=0, row=1, gate=None,
         pages='ISLAND_TIPS'),
    dict(id='cobble_gen', title='Cobblestone generator', icon='minecraft:cobblestone', col=0, row=2, gate=None, pages=[
        ('Infinite stone', "Lava flowing next to water makes cobblestone. Mine it, and it comes back."),
        ('@multiblock', 'quicreate:cobblestone_generator', 'Cobblestone generator',
         "Water on one side, lava on the other, mine the middle."),
        ('Later on', "The [[create_mechanical_extruder:mechanical_extruder]] does this automatically, and the "
                     "block under it picks the stone. See [[#mechnanical_extruder]]."),
    ]),
    # quests that were only 'read this' in the old quest book: filled in from the quest text
    dict(id='about_this_modpack', quest='about_this_modpack', col=0, row=3, gate=None),
    dict(id='ad_astra', quest='ad_astra', col=1, row=3, gate=None, after='about_this_modpack'),
    dict(id='create_new_age', quest='create_new_age', col=1, row=4, gate=None, after='about_this_modpack'),
    dict(id='cataclysm', quest='cataclysm', col=1, row=5, gate=None, after='about_this_modpack'),
    dict(id='quicreate3', quest='quicreate3', col=0, row=4, gate=None, after='about_this_modpack'),
    dict(id='quicreate', quest='quicreate', col=0, row=5, gate=None, after='about_this_modpack'),
    dict(id='create_cataclysm', quest='create_cataclysm', col=0, row=6, gate=None, after='about_this_modpack'),
    # ---------------- column 2: early tech
    dict(id='sifting', title='Sifting', icon='createsifter:sifter', col=2, row=0, gate='mill', pages='@SIFTING'),
    dict(id='meshes', title='Mesh ladder', icon='createsifter:brass_mesh', col=2, row=1, gate='mesh', pages='@MESHES'),
    dict(id='extruder', title='Mechanical Extruder', icon='create_mechanical_extruder:mechanical_extruder', col=2, row=2,
         gate='mill', pages='@EXTRUDER'),
    dict(id='heat', title='Heat', icon='create_new_age:heater', col=3, row=0, gate='copper', pages=[
        ('No blaze burners', "Blaze burners are out of reach in this pack. Heat comes from **Create: New Age**."),
        ('Solar heat', "[[create_new_age:basic_solar_heating_plate]] plates collect heat in daylight. A "
                       "[[create_new_age:heater]] under a basin turns it into **heated** or **superheated** mixing."),
        ('Moving heat', "[[create_new_age:heat_pipe]] and [[create_new_age:heat_pump]] carry heat from the plates. "
                        "A [[create_new_age:stirling_engine]] turns spare heat into rotation."),
        ('At night', "Solar heat stops at night. Nuclear heat ([[#nuclear_fuel]]) is the answer later on."),
    ]),
    dict(id='electricity', title='Electricity', icon='create_new_age:generator_coil', col=3, row=1, gate='magnetite',
         pages=[
        ('Making power', "A [[create_new_age:generator_coil]] makes power while it spins and touches "
                         "[[create_new_age:magnetite_block]]. Up to 12 magnets per coil."),
        ('Better magnets', "Stronger magnets give more power for the same rotation: redstone, layered, then "
                           "fluxuated magnetite."),
        ('Taking power out', "[[create_new_age:carbon_brushes]] on the end of the coil collect the power. "
                             "[[create_new_age:electrical_connector]] carry it with wire."),
        ('@multiblock', 'quicreate:mechanical_crafter_grid', '21 mechanical crafters',
         "The coil is a 5x5 recipe: build this grid."),
    ]),
    dict(id='assembly', title='Circuits', icon='create_new_age:copper_circuit', col=3, row=2, gate='deployer', pages=[
        ('Sequenced assembly', "Circuits are made on a belt with deployers, a press and a saw, in loops. Each tier "
                               "is built from the one below it."),
        ('The ladder', "1. [[create_new_age:blank_circuit]]\n2. [[create_new_age:copper_circuit]]\n"
                       "3. [[quicreate:emerald_circuit]]\n4. [[quicreate:amethyst_circuit]]\n"
                       "5. [[quicreate:ancient_metal_circuit]]\n\n"),
        ('Plan ahead', "Costs multiply as you climb. One ancient metal circuit is about **288 redstone** and "
                       "**144 quartz**. Leave each line running."),
    ]),
    dict(id='nuclear', title='Nuclear heat', icon='create_new_age:reactor_rod', col=3, row=3, gate='nuclear_fuel', pages=[
        ('Heat at night', "Reactor rods make heat day and night. Every side of a rod must touch a reactor part."),
        ('@multiblock', 'quicreate:reactor', 'A small reactor', "Rods in a casing, with a fuel acceptor, a heat vent and heat pipes."),
        ('Careful', "[[create_new_age:reactor_heat_vent]] vents must take the heat away, or it builds up."),
    ]),
    dict(id='cards', title='Card packs', icon='cards:common_card_pack', col=2, row=3, gate='sifter', pages='@CARDS'),
    dict(id='fishing', title='Fishing', icon='quicreate:brass_fishing_rod', col=2, row=4, gate='sifter', pages='@FISHING'),
    # ---------------- column 4: space
    dict(id='spaceflight', title='Going to space', icon='ad_astra:tier_1_rocket', col=4, row=0, gate='steel_plates', pages=[
        ('Checklist', "- Full space suit\n- Oxygen in the suit\n- Rocket on a launch pad\n- Fuel, and fuel "
                      "for the trip home\n\n"),
        ('Oxygen', "The [[ad_astra:oxygen_loader]] fills tanks and suits from water. Carry a "
                   "[[ad_astra:large_gas_tank]] to top up."),
        ('Fuel', "Oil comes from [[cards:rubber_ball]] in a superheated mixer. The [[ad_astra:fuel_refinery]] turns "
                 "it into rocket fuel."),
    ]),
    dict(id='planet_moon', planet='moon', col=4, row=1, gate='moon_landing'),
    dict(id='planet_mars', planet='mars', col=4, row=2, gate='mars_landing'),
    dict(id='planet_venus', planet='venus', col=5, row=1, gate='venus_landing'),
    dict(id='planet_mercury', planet='mercury', col=5, row=2, gate='mercury_landing'),
    dict(id='planet_glacio', planet='glacio', col=5, row=3, gate='glacio_landing'),
    dict(id='bosses', title='Boss guide', icon='cataclysm:ignitium_ingot', col=4, row=3, gate='moon_landing', pages='@BOSSES'),
    dict(id='endgame', title='The creative ending', icon='quicreate:creative_alloy', col=5, row=4, gate='glacio_landing',
         pages=[
        ('The true ending', "Craft the creative casing, creative motor and creative blaze cake, and kill the "
                            "dragon. That finishes the pack."),
        ('Boss materials', "Cursium, ignitium, witherite and the essence of the storm make "
                           "[[quicreate:creative_alloy]]. Each alloy needs one essence: you need at least three."),
        ('Double up', "The [[ad_astra:etrionic_blast_furnace]] can alloy boss ingots, doubling them. Build it "
                      "before spending boss drops."),
    ]),
]

FIELD_COLUMNS = ['The Island', 'The Island', 'Workshop Age', 'Workshop Age', 'Space', 'Outer Planets']

# ------------------------------------------------------------------ chapter tab settings
# group -> (category id, short name, icon, background, star layers?)
CHAPTERS = [
    ('Chapter 1: The Sky', 'sky', 'The Sky', 'minecraft:oak_sapling', 'sky', False, 'island'),
    ('1.1: Sifting', 'sifting', 'Sifting', 'createsifter:sifter', 'sifting', False, 'sifting'),
    ('1.2: New Age', 'new_age', 'Heat', 'create_new_age:heater', 'new_age', False, 'newage'),
    ('1.2b: Electricity', 'electricity', 'Electricity', 'create_new_age:generator_coil', 'electricity', False, 'electricity'),
    ('1.3: Improvements', 'improvements', 'Improvements', 'create_new_age:copper_circuit', 'improvements', False, 'improve'),
    ('1.4: Space', 'space', 'Space', 'ad_astra:tier_1_rocket', 'space', True, 'space'),
    ('Chapter 2: The Moon', 'moon', 'The Moon', 'ad_astra:moon_globe', 'moon', True, 'moon'),
    ('Chapter 3: Mars', 'mars', 'Mars', 'ad_astra:mars_globe', 'mars', True, 'mars'),
    ('Chapter 4: Venus & Mercury', 'venus_mercury', 'Venus & Mercury', 'ad_astra:venus_globe', 'venus', True, 'venus'),
    ('Chapter 5: Glacio', 'glacio', 'Glacio', 'ad_astra:glacio_globe', 'glacio', True, 'glacio'),
    ('Endgame: Creative', 'creative', 'The Creative Ending', 'quicreate:creative_alloy', 'creative', True, 'creative'),
]
SIDE_CARDS_GROUP = 'Side: Cards & Mobs'
# 3D build previews on quest steps (Modonomicon multiblock pages: drag to turn, "Visualize" ghosts it in the world).
# The cna_* builds are the setups from Create: New Age's own ponder scenes (BSD-3-Clause), floors left out.
QUEST_MULTIBLOCKS = {
    'cobblestone': ('cobblestone_generator', 'Cobblestone generator', "Water and lava meeting make cobblestone."),
    'mechnanical_extruder': ('extruder_setup', 'Extruder setup', "Lava one side, water the other."),
    'heater': ('cna_heater', 'Heater', "Heat pipe in, heated basin on top."),
    'stirling_engine': ('cna_heating', 'Heat to rotation', "Solar heat, piped to Stirling engines, becomes rotation."),
    'generator_coil': ('cna_generation', 'Generator', "Spinning magnetite inside the coils makes power."),
    'wires': ('cna_wires', 'Wiring', "Wire between connectors carries the power."),
    'energizer': ('cna_energiser', 'Energiser line', "Energisers charge items passing under them."),
    'motors': ('cna_motor', 'Motor', "Power in through connectors, rotation out."),
    'reactor_rod': ('reactor', 'A small reactor', "Rods in a casing, with a fuel acceptor, a heat vent and heat pipes."),
}

# intro text for tabs that have no chapter in the walkthrough
CHAPTER_INTRO = {'electricity': [
    "Electricity runs on rotation, and rotation comes from heat: a [[create_new_age:stirling_engine]] turns the "
    "heat tab's solar heat into spin.",
    "A generator coil turns that spin into power. Carry it with wire and connectors, and use it to energise "
    "iron and gold."]}
# steps shown in a different chapter than the old quest book had them: the world where they can be built
GROUP_OVERRIDE = {'maptera_razor_sword': 'Chapter 2: The Moon', 'ancient_gilded_sword': 'Chapter 3: Mars',
                  'platinum_master_sword': 'Chapter 4: Venus & Mercury',
                  # its recipe and both parents are Moon tech; the quest file had it under Mars
                  'reinforced_motor': 'Chapter 2: The Moon',
                  # electricity has its own tab after heat: generators need rotation, which heat provides
                  **{q: '1.2b: Electricity' for q in ('electricity', 'magnetite', 'carbon_brush', 'wires', 'connector',
                                                       'energizer', 'overcharged_iron', 'overcharged_gold', 'blaze_powder',
                                                       'generator_coil')}}
# when a chapter tab appears (quest id); chapters not listed open once one of their steps can be started
CHAPTER_GATES = {'electricity': 'stirling_engine', 'moon': 'rocket', 'mars': 'tier_2_rocket', 'venus_mercury': 'tier_3_rocket',
                 'glacio': 'tier_4_rocket', 'creative': 'tier_3_rocket', 'improvements': 'magnetite'}

# quests that are milestones (gold star) and quests that are optional (round)
MILESTONES = {'andesitealloy', 'sifter', 'brass', 'mechnanical_extruder', 'generator_coil', 'steel', 'copper_circuit',
              'rocket', 'moon_landing', 'ender_dragon', 'tier_2_rocket', 'mars_landing', 'ancient_metal_circuit',
              'tier_3_rocket', 'venus_landing', 'mercury_landing', 'tier_4_rocket', 'glacio_landing',
              'creative_alloy', 'quicreate_complete', 'flight_anchor', 'emerald_circuit', 'amethyst_circuit'}
OPTIONAL = {'chunk_loader', 'smart_crafter', 'brass_chunk_loader', 'mechanical_spawner', 'soul_catcher',
            'ender_guardian', 'umvuthi', 'leviathan', 'sunken_city', 'wroughtnaut', 'ancient_gilded_sword',
            'maptera_razor_sword', 'platinum_master_sword', 'blaze_burner'}
MOVED_TO_FIELD_GUIDE = {'about_this_modpack', 'ad_astra', 'create_new_age', 'cataclysm', 'quicreate3', 'quicreate',
                        'create_cataclysm'}
READING = {'heat_generation', 'electricity', 'moon_stuff'}
HIDDEN_UNTIL_DONE = set()      # e.g. {'blaze_burner'}: entry stays invisible until done
HIDDEN_UNTIL_UNLOCKED = set()  # e.g. {'mars_secret'}: invisible until the steps it needs are done (then shown normally)
# every chapter tab shows from the start (locked steps are greyed); False brings back the unlock-as-you-go tabs
ALL_TABS_VISIBLE = True
# parents for quests the old book drew without arrows
EXTRA_PARENTS = {
    'wires': ['sheets', 'saw'], 'carbon_brush': ['sheets'], 'crushing_wheels': ['mechnanical_extruder'],
    'mechnanical_extruder': ['press', 'brass_casing'], 'mechanical_crafters': ['electron_tube', 'brass_casing'],
    'space_suit': ['steel_plates'], 'space_pants': ['steel_plates'], 'space_boots': ['steel_plates'],
    'electricity': ['magnetite'],
}
# items that do not stack: count 1 in the tracker, the text still says how many to bring
UNSTACKABLE_SUFFIX = ('_bucket',)
UNSTACKABLE = {'ad_astra:gas_tank', 'ad_astra:large_gas_tank'}

# ------------------------------------------------------------------ side paths
# Each path: id, name, icon, background, description. Each goal: id, name, icon, stage (0..5), row,
# kind: items (collect one of each) | count (hold N of an item) | kills | biomes | structures | link (main quest),
# and text. Rewards come from rewards.yaml.
STAGES = [('island', 'The Island', 'minecraft:grass_block', None),
          ('tech', 'Workshop Age', 'create:cogwheel', 'sifter'),
          ('moon', 'The Moon', 'ad_astra:moon_globe', 'moon_landing'),
          ('mars', 'Mars', 'ad_astra:mars_globe', 'mars_landing'),
          ('venus', 'Venus & Mercury', 'ad_astra:venus_globe', ['venus_landing', 'mercury_landing']),
          ('glacio', 'Glacio', 'ad_astra:glacio_globe', 'glacio_landing')]

SIDE_PATHS = [
    ('builders', "Builder's Book", 'minecraft:bricks', 'builders',
     "Collect every kind of stone and wood. Builders get blocks, and blocks make bases worth looking at."),
    ('explorer', 'Explorer', 'minecraft:compass', 'explorer',
     "Visit every biome and find every landmark on each world."),
    ('bestiary', 'Bestiary', 'minecraft:skeleton_skull', 'bestiary',
     "Hunt the creatures of each world, and read up on every boss."),
    ('workshop', 'Workshop', 'create:brass_casing', 'workshop',
     "Automation goals. Build lines that run while you're away."),
    ('kitchen', 'Kitchen & Farm', 'minecraft:bread', 'kitchen',
     "Grow, cook and bake. Good food keeps you fighting."),
    ('cards', 'Cards & Mobs', 'cards:common_card_pack', 'cards',
     "Card packs, spawn eggs, the Wither and the Flight Anchor."),
]

SIDE_GOALS = {
    'builders': [
        dict(id='woodworker', name='Woodworker', icon='minecraft:oak_log', stage=0, row=0, kind='items',
             items=['minecraft:oak_log', 'minecraft:birch_log', 'minecraft:spruce_log', 'minecraft:jungle_log',
                    'minecraft:acacia_log', 'minecraft:dark_oak_log', 'minecraft:cherry_log', 'minecraft:bamboo_block'],
             text="Saplings from a waterlogged sifter grow every tree. Collect a log of each."),
        dict(id='stonemason', name='Stonemason', icon='minecraft:stone', stage=0, row=1, kind='items',
             items=['minecraft:stone', 'minecraft:cobblestone', 'minecraft:andesite', 'minecraft:diorite',
                    'minecraft:granite', 'minecraft:smooth_stone', 'minecraft:stone_bricks'],
             text="The basic stones. Andesite and diorite come from the extruder too."),
        dict(id='extruded', name='Extruded stones', icon='quicreate:andesite_extruder', stage=0, row=2, kind='items',
             items=['minecraft:tuff', 'minecraft:calcite', 'minecraft:cobbled_deepslate', 'create:limestone',
                    'create:scoria'],
             text="The Andesite Extruder rolls these now and then. Keep one of each."),
        dict(id='create_stones', name='Create stones', icon='create:limestone', stage=1, row=0, kind='items',
             items=['create:limestone', 'create:scoria', 'create:scorchia', 'create:crimsite', 'create:veridium',
                    'create:asurine', 'create:ochrum'],
             text="Create's stones come from the extruder: limestone and scoria from fluids, the ore stones from "
                  "metal blocks below it."),
        dict(id='cut_and_polished', name='Cut & polished', icon='create:cut_limestone', stage=1, row=1, kind='items',
             items=['create:cut_limestone', 'create:polished_cut_limestone', 'create:cut_scoria',
                    'create:cut_andesite', 'create:cut_diorite', 'create:cut_granite'],
             text="Put a stone on a stonecutter or a mechanical saw for cut and polished blocks."),
        dict(id='glass_works', name='Glass works', icon='create:framed_glass', stage=1, row=2, kind='items',
             items=['minecraft:glass', 'create:framed_glass', 'create:tiled_glass', 'create:vertical_framed_glass',
                    'create:horizontal_framed_glass'],
             text="Smelt sand into glass, then craft Create's framed panes."),
        dict(id='moon_stones', name='Lunar masonry', icon='ad_astra:moon_stone_bricks', stage=2, row=0, kind='items',
             items=['ad_astra:moon_stone', 'ad_astra:moon_cobblestone', 'ad_astra:moon_sand', 'ad_astra:moon_deepslate',
                    'ad_astra:moon_stone_bricks', 'ad_astra:moon_pillar'],
             text="Bring the Moon home: moon stone, sand, deepslate, bricks and pillars."),
        dict(id='mars_stones', name='Martian masonry', icon='ad_astra:mars_stone_bricks', stage=3, row=0, kind='items',
             items=['ad_astra:mars_stone', 'ad_astra:mars_cobblestone', 'ad_astra:mars_sand', 'ad_astra:conglomerate',
                    'ad_astra:mars_stone_bricks', 'ad_astra:mars_pillar'],
             text="Red stone for red builds. Conglomerate hides ancient debris."),
        dict(id='venus_stones', name='Venusian masonry', icon='ad_astra:venus_sandstone_bricks', stage=4, row=0,
             kind='items',
             items=['ad_astra:venus_stone', 'ad_astra:venus_cobblestone', 'ad_astra:venus_sand',
                    'ad_astra:venus_sandstone', 'ad_astra:venus_sandstone_bricks', 'ad_astra:venus_stone_bricks'],
             text="Golden sandstone from the acid world."),
        dict(id='mercury_stones', name='Mercurian masonry', icon='ad_astra:mercury_stone_bricks', stage=4, row=1,
             kind='items',
             items=['ad_astra:mercury_stone', 'ad_astra:mercury_cobblestone', 'ad_astra:mercury_stone_bricks',
                    'ad_astra:mercury_pillar'],
             text="Dark stone from the planet closest to the sun."),
        dict(id='alien_woods', name='Alien woods', icon='ad_astra:aeronos_stem', stage=4, row=2, kind='items',
             items=['ad_astra:aeronos_stem', 'ad_astra:aeronos_cap', 'ad_astra:strophar_stem', 'ad_astra:strophar_cap',
                    'ad_astra:aeronos_planks', 'ad_astra:strophar_planks'],
             text="Venus grows tall aeronos mushrooms; the Moon's deep pits grow strophar. Their stems make planks."),
        dict(id='glacio_stones', name='Glacian masonry', icon='ad_astra:glacio_stone_bricks', stage=5, row=0,
             kind='items',
             items=['ad_astra:glacio_stone', 'ad_astra:glacio_cobblestone', 'ad_astra:glacio_stone_bricks',
                    'ad_astra:glacio_pillar', 'ad_astra:permafrost', 'ad_astra:glacian_log', 'ad_astra:glacian_planks'],
             text="Icy stone and glacian wood from the frozen world."),
    ],
    'workshop': [
        dict(id='mill_row', name='Mill row', icon='create:millstone', stage=0, row=0, kind='count',
             item='create:millstone', count=4,
             text="One millstone is slow. Four in a row, fed by a belt, keeps the sifters busy."),
        dict(id='sifter_line', name='Sifter line', icon='createsifter:sifter', stage=1, row=0, kind='count',
             item='createsifter:sifter', count=4,
             text="Four sifters on a belt: one for each block you sift."),
        dict(id='belt_it', name='Belt it', icon='create:belt_connector', stage=1, row=1, kind='count',
             item='create:belt_connector', count=32,
             text="Belts move everything. Build a long line from the mills to the sifters."),
        dict(id='ore_line', name='Ore line', icon='create:crushing_wheel', stage=1, row=2, kind='items',
             items=['create:crushing_wheel', 'create:encased_fan', 'create:crushed_raw_iron'],
             text="Extruder, crushing wheels and a washing fan: endless ore."),
        dict(id='storage', name='Storage room', icon='create:item_vault', stage=1, row=3, kind='count',
             item='create:item_vault', count=8,
             text="Item vaults join into one big store. Hook them to a storage terminal later."),
        dict(id='circuit_line', name='Circuit line', icon='create:deployer', stage=1, row=4, kind='count',
             item='create:deployer', count=4,
             text="Four deployers on a belt run a circuit recipe on their own."),
        dict(id='smart_crafter', link='smart_crafter', stage=2, row=0),
        dict(id='chunk_loader', link='chunk_loader', stage=2, row=1),
        dict(id='mechanical_arms', name='Robot arms', icon='create:mechanical_arm', stage=2, row=2, kind='count',
             item='create:mechanical_arm', count=4,
             text="Mechanical arms sort and feed machines without belts."),
        dict(id='brass_chunk_loader', link='brass_chunk_loader', stage=3, row=0),
        dict(id='mechanical_spawner', link='mechanical_spawner', stage=3, row=1),
        dict(id='soul_catcher', link='soul_catcher', stage=3, row=2),
        dict(id='blast_furnace', link='etrionic_blast_furnace', stage=4, row=0),
        dict(id='flight_anchor', link='flight_anchor', stage=5, row=0),
    ],
    'kitchen': [
        dict(id='first_harvest', name='First harvest', icon='minecraft:wheat', stage=0, row=0, kind='items',
             items=['minecraft:wheat', 'minecraft:potato', 'minecraft:carrot', 'minecraft:beetroot',
                    'minecraft:pumpkin', 'minecraft:sugar_cane'],
             text="Seeds and crops come from sifting dirt. Plant one of each."),
        dict(id='baker', name='Baker', icon='minecraft:bread', stage=0, row=1, kind='items',
             items=['minecraft:bread', 'minecraft:cookie', 'minecraft:pumpkin_pie', 'minecraft:cake'],
             text="Bread, cookies, pie and cake."),
        dict(id='farm_animals', link='farm_animals', stage=1, row=0),
        dict(id='butcher', name='Hearty meals', icon='minecraft:cooked_beef', stage=1, row=1, kind='items',
             items=['minecraft:cooked_beef', 'minecraft:cooked_porkchop', 'minecraft:cooked_chicken',
                    'minecraft:cooked_mutton', 'minecraft:baked_potato'],
             text="Animals from card packs give real food. Cook one of each."),
        dict(id='create_treats', name='Create treats', icon='create:sweet_roll', stage=1, row=2, kind='items',
             items=['create:sweet_roll', 'create:honeyed_apple', 'create:chocolate_glazed_berries',
                    'create:bar_of_chocolate', 'create:builders_tea'],
             text="Spouts and mixers make Create's sweets. Builder's tea gives haste."),
        dict(id='angler', name='Angler', icon='minecraft:cod', stage=1, row=3, kind='items',
             items=['minecraft:cod', 'minecraft:salmon', 'minecraft:tropical_fish', 'minecraft:pufferfish'],
             text="Fish in the ocean around your island."),
        dict(id='moon_cheese', name='Moon cheese', icon='ad_astra:cheese', stage=2, row=0, kind='count',
             item='ad_astra:cheese', count=16,
             text="The Moon really is made of cheese. Mine cheese ore."),
        dict(id='golden_food', name='Golden food', icon='minecraft:golden_carrot', stage=3, row=0, kind='items',
             items=['minecraft:golden_carrot', 'minecraft:golden_apple', 'minecraft:glistering_melon_slice'],
             text="Gold from the brass mesh makes the best food for boss fights."),
        dict(id='stews', name='Stew pot', icon='minecraft:rabbit_stew', stage=4, row=0, kind='items',
             items=['minecraft:mushroom_stew', 'minecraft:beetroot_soup', 'minecraft:rabbit_stew',
                    'minecraft:suspicious_stew'],
             text="Every stew in a bowl."),
    ],
}
# steps that are new in the book (not in the old quest book). Same shape as knowledge.json quests.
EXTRA_QUESTS = [
    {'id': 'andesite_extruder', 'group': '1.1: Sifting', 'step': 1000, 'title': 'Andesite Extruder',
     'subtitle': 'Random stone, forever', 'pos': [-60, -30], 'deps': ['mill'], 'soft_deps': [], 'icon': 'quicreate:andesite_extruder',
     'desc': ['Lava on one side, water on the other, like a cobblestone generator. Each cycle it makes a random '
              'natural stone.',
              'The block **underneath** picks the stones: nothing special gives overworld stones, limestone gives '
              "Create's decorative stones, and stone from another planet gives that planet's stones. "
              'See the Field Guide page on extruders.'],
     'tasks': [{'type': 'heracles:item', 'item': 'quicreate:andesite_extruder', 'amount': 1}], 'tag_items': {}},
]
EXTRA_KNOWN = {'quicreate:andesite_extruder': 'Andesite Extruder'}
ANDESITE_EXTRUDER_TABLES = [
    ('Nothing special', 'stone, cobblestone, andesite, diorite, granite, limestone, scoria, tuff, calcite, deepslate'),
    ('Limestone', 'limestone, scoria, scorchia, dripstone'),
    ('Moon stone', 'moon stone, cobblestone, sand, deepslate'),
    ('Mars stone', 'Mars stone, cobblestone, sand'),
    ('Venus stone', 'Venus stone, cobblestone, sand, sandstone'),
    ('Mercury stone', 'Mercury stone and cobblestone'),
    ('Glacio stone', 'Glacio stone, cobblestone, permafrost'),
    ('Netherrack', 'netherrack, basalt, blackstone, soul soil'),
    ('End stone', 'end stone'),
]

# explorer and bestiary goals are generated from the planet data in build_book.py
EXPLORER_EXTRA = [
    dict(id='the_end_city', name='City in the End', icon='minecraft:purpur_block', stage=2, row=3, kind='structures',
         structures=['minecraft:end_city'], text="After the dragon, end gateways lead to the end cities."),
]
