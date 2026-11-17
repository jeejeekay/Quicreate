package IGoByJake.quicreate.spawn;

import IGoByJake.quicreate.Quicreate;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimpleJsonResourceReloadListener;
import net.minecraft.util.GsonHelper;
import net.minecraft.util.profiling.ProfilerFiller;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Drowned;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.AddReloadListenerEvent;
import net.minecraftforge.event.entity.living.MobSpawnEvent;
import net.minecraftforge.eventbus.api.Event;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Data-driven caps on natural mob spawns, replacing Hard Mob Limits.
 *
 * <p>Each file in {@code data/<namespace>/mob_limits/*.json} is one limit:
 * <pre>{"entity": "minecraft:drowned", "max": 3, "radius": 128, "dimensions": ["minecraft:overworld"]}</pre>
 * {@code radius} defaults to 128 and {@code dimensions} to every dimension. A natural (or world generation) spawn
 * of that mob is refused when {@code max} or more of it are already within {@code radius} blocks of the spot. The
 * check runs in {@link MobSpawnEvent.SpawnPlacementCheck}, before the mob is created, so a refused spawn never
 * makes anything (no stray jockey chickens). Spawn eggs, spawners, structures and commands are not limited.
 *
 * <p>Drowned also never roll a chicken jockey: see {@link #onFinalizeSpawn}. Babies keep their vanilla chance.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class MobLimits extends SimpleJsonResourceReloadListener {
    private static final Gson GSON = new GsonBuilder().create();
    private static final MobLimits INSTANCE = new MobLimits();

    private record Limit(int max, int radius, Set<ResourceLocation> dimensions) {
    }

    private volatile Map<EntityType<?>, List<Limit>> limits = Map.of();

    private MobLimits() {
        super(GSON, "mob_limits");
    }

    @Override
    protected void apply(Map<ResourceLocation, JsonElement> files, ResourceManager manager, ProfilerFiller profiler) {
        Map<EntityType<?>, List<Limit>> out = new HashMap<>();
        files.forEach((id, element) -> {
            try {
                JsonObject json = GsonHelper.convertToJsonObject(element, "mob limit");
                ResourceLocation entityId = new ResourceLocation(GsonHelper.getAsString(json, "entity"));
                EntityType<?> type = ForgeRegistries.ENTITY_TYPES.getValue(entityId);
                if (type == null || !ForgeRegistries.ENTITY_TYPES.containsKey(entityId)) {
                    Quicreate.LOGGER.debug("[mob_limits] {}: entity {} is not loaded, skipped", id, entityId);
                    return;
                }
                Set<ResourceLocation> dims = new HashSet<>();
                if (json.has("dimensions")) {
                    for (JsonElement d : GsonHelper.getAsJsonArray(json, "dimensions")) {
                        dims.add(new ResourceLocation(d.getAsString()));
                    }
                }
                Limit limit = new Limit(Math.max(0, GsonHelper.getAsInt(json, "max")),
                        Math.max(8, GsonHelper.getAsInt(json, "radius", 128)), dims);
                out.computeIfAbsent(type, t -> new ArrayList<>()).add(limit);
            } catch (Exception e) {
                Quicreate.LOGGER.error("[mob_limits] could not read {}: {}", id, e.getMessage());
            }
        });
        limits = out;
        Quicreate.LOGGER.info("[mob_limits] {} limits loaded", out.values().stream().mapToInt(List::size).sum());
    }

    @SubscribeEvent
    public static void onAddReloadListeners(AddReloadListenerEvent event) {
        event.addListener(INSTANCE);
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void onSpawnPlacement(MobSpawnEvent.SpawnPlacementCheck event) {
        MobSpawnType reason = event.getSpawnType();
        if (reason != MobSpawnType.NATURAL && reason != MobSpawnType.CHUNK_GENERATION) {
            return;
        }
        List<Limit> list = INSTANCE.limits.get(event.getEntityType());
        if (list == null) {
            return;
        }
        ServerLevel level = event.getLevel().getLevel();
        ResourceLocation dim = level.dimension().location();
        for (Limit limit : list) {
            if (!limit.dimensions().isEmpty() && !limit.dimensions().contains(dim)) {
                continue;
            }
            if (limit.max() == 0) {
                event.setResult(Event.Result.DENY);
                return;
            }
            AABB box = new AABB(event.getPos()).inflate(limit.radius());
            int count = level.getEntities(event.getEntityType(), box, e -> e.isAlive()).size();
            if (count >= limit.max()) {
                event.setResult(Event.Result.DENY);
                return;
            }
        }
    }

    /**
     * Vanilla Zombie#finalizeSpawn (drowned inherit it) gives a baby a 5% chance to spawn a chicken and ride it.
     * Over the ocean that chicken appears underwater and drowns, hundreds of times a minute. Handing drowned
     * group data with jockeys switched off stops that, while babies keep their usual chance. Other zombies are
     * untouched. FinalizeSpawn fires before finalizeSpawn runs, so this is the value vanilla uses.
     */
    @SubscribeEvent
    public static void onFinalizeSpawn(MobSpawnEvent.FinalizeSpawn event) {
        if (event.getEntity() instanceof Drowned drowned && event.getSpawnData() == null) {
            event.setSpawnData(new Zombie.ZombieGroupData(Zombie.getSpawnAsBabyOdds(drowned.getRandom()), false));
        }
    }
}
