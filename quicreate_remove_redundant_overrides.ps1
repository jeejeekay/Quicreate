# Quicreate: remove redundant data overrides (2026-11-10)
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File .\quicreate_remove_redundant_overrides.ps1
# Commit first so `git` can restore anything.
#
# Part 1: files byte-for-byte or JSON-identical to the original mod/vanilla file, so they override nothing.
# Part 2: worldgen files left unused after the Mars Fungal Lowlands biome was removed.
# Part 3: the Ad Astra: More Structures placeholder (that mod is leaving the pack).

$ErrorActionPreference = "Stop"
$root = Join-Path $PSScriptRoot "src\main\resources\data"
$files = @(
    "ad_astra/dimension/earth_orbit.json",
    "ad_astra/dimension/glacio_orbit.json",
    "ad_astra/dimension/mars.json",
    "ad_astra/dimension/mars_orbit.json",
    "ad_astra/dimension/mercury_orbit.json",
    "ad_astra/dimension/moon_orbit.json",
    "ad_astra/dimension/venus_orbit.json",
    "ad_astra/tags/items/space_suit_items.json",
    "ad_astra/worldgen/noise_settings/mars.json",
    "ad_astra/worldgen/noise_settings/orbit.json",
    "cataclysm/recipes/soul_render.json",
    "cataclysm/recipes/the_annihilator.json",
    "cataclysm/structures/acropolis_1.nbt",
    "cataclysm/structures/ancient_factory2.nbt",
    "cataclysm/structures/ancient_factory3.nbt",
    "cataclysm/structures/ancient_factory4.nbt",
    "cataclysm/structures/ancient_factory6.nbt",
    "cataclysm/structures/ancient_factory_d.nbt",
    "cataclysm/structures/ancient_factory_e.nbt",
    "cataclysm/structures/ancient_factory_q.nbt",
    "cataclysm/structures/frosted_prison_bottom_11.nbt",
    "cataclysm/structures/ruined_citadel2.nbt",
    "cataclysm/structures/ruined_citadel3.nbt",
    "cataclysm/structures/ruined_citadel4.nbt",
    "cataclysm/structures/ruined_citadel6.nbt",
    "cataclysm/structures/ruined_citadel7.nbt",
    "cataclysm/structures/ruined_citadel8.nbt",
    "cataclysm/structures/ruined_citadel9.nbt",
    "cataclysm/structures/sunken_city_entrance1.nbt",
    "cataclysm/structures/sunken_city_entrance3.nbt",
    "cataclysm/structures/sunken_city_entrance4.nbt",
    "cataclysm/structures/sunken_city_lower.nbt",
    "cataclysm/structures/sunken_city_lower_north.nbt",
    "cataclysm/structures/sunken_city_lower_northeast.nbt",
    "cataclysm/structures/sunken_city_lower_northwest.nbt",
    "cataclysm/structures/sunken_city_lower_prison.nbt",
    "cataclysm/structures/sunken_city_lower_south.nbt",
    "cataclysm/structures/sunken_city_lower_southeast.nbt",
    "cataclysm/structures/sunken_city_lower_treasureroom.nbt",
    "cataclysm/structures/sunken_city_mid_north_side.nbt",
    "cataclysm/structures/sunken_city_mid_northeast.nbt",
    "cataclysm/structures/sunken_city_mid_southeast.nbt",
    "create_mechanical_extruder/recipes/extruding/stone.json",
    "minecraft/tags/worldgen/biome/has_structure/ancient_city.json",
    "minecraft/tags/worldgen/biome/has_structure/bastion_remnant.json",
    "minecraft/tags/worldgen/biome/has_structure/buried_treasure.json",
    "minecraft/tags/worldgen/biome/has_structure/desert_pyramid.json",
    "minecraft/tags/worldgen/biome/has_structure/end_city.json",
    "minecraft/tags/worldgen/biome/has_structure/igloo.json",
    "minecraft/tags/worldgen/biome/has_structure/jungle_temple.json",
    "minecraft/tags/worldgen/biome/has_structure/mineshaft.json",
    "minecraft/tags/worldgen/biome/has_structure/mineshaft_mesa.json",
    "minecraft/tags/worldgen/biome/has_structure/nether_fortress.json",
    "minecraft/tags/worldgen/biome/has_structure/nether_fossil.json",
    "minecraft/tags/worldgen/biome/has_structure/ocean_monument.json",
    "minecraft/tags/worldgen/biome/has_structure/ocean_ruin_cold.json",
    "minecraft/tags/worldgen/biome/has_structure/ocean_ruin_warm.json",
    "minecraft/tags/worldgen/biome/has_structure/pillager_outpost.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_desert.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_jungle.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_mountain.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_nether.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_ocean.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_standard.json",
    "minecraft/tags/worldgen/biome/has_structure/ruined_portal_swamp.json",
    "minecraft/tags/worldgen/biome/has_structure/shipwreck.json",
    "minecraft/tags/worldgen/biome/has_structure/shipwreck_beached.json",
    "minecraft/tags/worldgen/biome/has_structure/swamp_hut.json",
    "minecraft/tags/worldgen/biome/has_structure/trail_ruins.json",
    "minecraft/tags/worldgen/biome/has_structure/village_desert.json",
    "minecraft/tags/worldgen/biome/has_structure/village_plains.json",
    "minecraft/tags/worldgen/biome/has_structure/village_savanna.json",
    "minecraft/tags/worldgen/biome/has_structure/village_snowy.json",
    "minecraft/tags/worldgen/biome/has_structure/village_taiga.json",
    "minecraft/tags/worldgen/biome/has_structure/woodland_mansion.json",
    "minecraft/tags/worldgen/biome/required_ocean_monument_surrounding.json",
    "minecraft/worldgen/structure_set/nether_complexes.json",
    "mowziesmobs/tags/worldgen/biome/is_magical.json",
    "quicreate/worldgen/biome/martian_fungal_lowlands.json",
    "quicreate/worldgen/configured_feature/mars_aeronos_mushroom.json",
    "quicreate/worldgen/configured_feature/mars_strophar_mushroom.json",
    "quicreate/worldgen/configured_feature/mars_lone_mushroom.json",
    "quicreate/worldgen/configured_feature/mars_conglomerate_boulder.json",
    "quicreate/worldgen/placed_feature/mars_aeronos_mushroom.json",
    "quicreate/worldgen/placed_feature/mars_strophar_mushroom.json",
    "quicreate/worldgen/placed_feature/mars_lone_mushroom.json",
    "quicreate/worldgen/placed_feature/mars_conglomerate_boulder.json"
)
$removed = 0
foreach ($f in $files) {
    $p = Join-Path $root ($f -replace "/", "\")
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p; $removed++ } else { Write-Host "already gone: $f" }
}
$amsd = Join-Path $root "ad_astra_more_structures"
if (Test-Path -LiteralPath $amsd) { Remove-Item -LiteralPath $amsd -Recurse; Write-Host "removed data\ad_astra_more_structures" }
Write-Host "Removed $removed of $($files.Count) files."
