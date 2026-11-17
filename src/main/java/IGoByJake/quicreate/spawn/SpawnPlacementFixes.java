package IGoByJake.quicreate.spawn;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.SpawnPlacements;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * Lets mobs we add to planet biomes actually spawn on land there.
 * <ul>
 *   <li>Cataclysm's amethyst crab is registered to spawn only in water, so on the (waterless) Moon it never spawned
 *       naturally at all.</li>
 *   <li>Mowzie's elokosa follower howler has no spawn rules of its own, which lets it appear anywhere, even
 *       floating in the air.</li>
 * </ul>
 * Both now spawn standing on a solid block, like a normal land mob. How often is set by the biome spawn lists.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class SpawnPlacementFixes {

    private static final ResourceLocation[] ON_LAND = {
            new ResourceLocation("cataclysm", "amethyst_crab"),
            new ResourceLocation("mowziesmobs", "elokosa_follower_howler"),
    };

    private SpawnPlacementFixes() {
    }

    @SubscribeEvent
    @SuppressWarnings("unchecked")
    public static void onRegister(SpawnPlacementRegisterEvent event) {
        for (ResourceLocation id : ON_LAND) {
            if (!ForgeRegistries.ENTITY_TYPES.containsKey(id)) {
                continue;
            }
            EntityType<Mob> type = (EntityType<Mob>) ForgeRegistries.ENTITY_TYPES.getValue(id);
            event.register(type, SpawnPlacements.Type.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                    Mob::checkMobSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        }
    }
}
