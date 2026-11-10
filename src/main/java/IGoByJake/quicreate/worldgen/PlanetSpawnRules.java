package IGoByJake.quicreate.worldgen;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Monster;
import net.minecraftforge.event.entity.living.MobSpawnEvent;
import net.minecraftforge.eventbus.api.Event;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * Natural spawn rules for Ad Astra's Venus mobs (biome spawn lists set where and how many):
 * <ul>
 *   <li>Pygros spawn in any light, so groups of them wander the surface by day too. Ad Astra gave
 *       them monster rules, which only allow darkness.</li>
 *   <li>Moglers spawn only in the dark: in caves and on the surface at night. Ad Astra let them
 *       spawn in any light.</li>
 * </ul>
 * Spawners, spawn eggs and structures are untouched.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID)
public final class PlanetSpawnRules {

    private static final ResourceLocation PYGRO = new ResourceLocation("ad_astra", "pygro");
    private static final ResourceLocation MOGLER = new ResourceLocation("ad_astra", "mogler");

    private PlanetSpawnRules() {
    }

    private static boolean is(EntityType<?> type, ResourceLocation id) {
        return id.equals(ForgeRegistries.ENTITY_TYPES.getKey(type));
    }

    private static boolean natural(MobSpawnType spawnType) {
        return spawnType == MobSpawnType.NATURAL || spawnType == MobSpawnType.CHUNK_GENERATION;
    }

    @SubscribeEvent
    public static void onSpawnPlacement(MobSpawnEvent.SpawnPlacementCheck event) {
        if (!natural(event.getSpawnType())) {
            return;
        }
        EntityType<?> type = event.getEntityType();
        boolean mogler = is(type, MOGLER);
        if (!mogler && !is(type, PYGRO)) {
            return;
        }
        BlockPos below = event.getPos().below();
        boolean ok = event.getLevel().getBlockState(below).isValidSpawn(event.getLevel(), below, type);
        if (mogler) {
            ok = ok && event.getLevel().getDifficulty() != Difficulty.PEACEFUL
                    && Monster.isDarkEnoughToSpawn(event.getLevel(), event.getPos(), event.getRandom());
        }
        event.setResult(ok ? Event.Result.ALLOW : Event.Result.DENY);
    }

    /** Pygros are monsters, and monsters normally refuse lit spots; let them spawn wherever they fit. */
    @SubscribeEvent
    public static void onPositionCheck(MobSpawnEvent.PositionCheck event) {
        if (natural(event.getSpawnType()) && is(event.getEntity().getType(), PYGRO)) {
            event.setResult(event.getEntity().checkSpawnObstruction(event.getLevel()) ? Event.Result.ALLOW : Event.Result.DENY);
        }
    }
}
