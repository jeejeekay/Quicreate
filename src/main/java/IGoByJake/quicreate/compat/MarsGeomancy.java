package IGoByJake.quicreate.compat;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Makes Mowzie's geomancy rocks look like Mars.
 * <ul>
 *   <li>The Sculptor's boulder platforms and pillars become Mars stone.</li>
 *   <li>The crumbling platforms become Mars sand.</li>
 *   <li>Any other geomancy rock that would show plain stone shows Mars stone.</li>
 * </ul>
 * The rocks draw whatever block state they carry, so swapping that state on the server when the entity joins
 * changes the texture for everyone. Reflection only, so Quicreate does not need Mowzie's Mobs to build.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID)
public final class MarsGeomancy {

    private static final String MZ = "mowziesmobs";
    private static boolean lookedUp;
    private static Method getBlock;
    private static Method setBlock;
    private static Field storedBlock;

    private MarsGeomancy() {
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide()) {
            return;
        }
        Entity entity = event.getEntity();
        ResourceLocation id = ForgeRegistries.ENTITY_TYPES.getKey(entity.getType());
        if (id == null || !MZ.equals(id.getNamespace())) {
            return;
        }
        String path = id.getPath();
        if (!(path.startsWith("boulder") || path.startsWith("pillar") || path.startsWith("fissure")
                || path.equals("earth_spike") || path.equals("rock_sling"))) {
            return;
        }
        Block marsStone = block("ad_astra", "mars_stone");
        Block marsSand = block("ad_astra", "mars_sand");
        if (marsStone == null || marsSand == null || !lookUp(entity)) {
            return;
        }
        try {
            BlockState current = (BlockState) getBlock.invoke(entity);
            BlockState next;
            if (path.equals("boulder_platform_crumbling")) {
                next = marsSand.defaultBlockState();
            } else if (path.equals("boulder_platform") || path.equals("pillar_sculptor")) {
                next = marsStone.defaultBlockState();
            } else if (current != null && current.is(Blocks.STONE)) {
                next = marsStone.defaultBlockState();
            } else {
                return;
            }
            setBlock.invoke(entity, next);
            if (storedBlock != null && storedBlock.getDeclaringClass().isInstance(entity)) {
                storedBlock.set(entity, next);
            }
        } catch (ReflectiveOperationException | ClassCastException ignored) {
            // Mowzie's changed its classes; leave the rock as it is
        }
    }

    private static Block block(String ns, String path) {
        ResourceLocation id = new ResourceLocation(ns, path);
        return ForgeRegistries.BLOCKS.containsKey(id) ? ForgeRegistries.BLOCKS.getValue(id) : null;
    }

    private static boolean lookUp(Entity entity) {
        if (!lookedUp) {
            lookedUp = true;
            try {
                ClassLoader loader = entity.getClass().getClassLoader();
                Class<?> base = Class.forName("com.bobmowzie.mowziesmobs.server.entity.effects.geomancy.EntityGeomancyBase", false, loader);
                getBlock = base.getMethod("getBlock");
                setBlock = base.getMethod("setBlock", BlockState.class);
                Class<?> boulder = Class.forName("com.bobmowzie.mowziesmobs.server.entity.effects.geomancy.EntityBoulderBase", false, loader);
                storedBlock = boulder.getField("storedBlock");
            } catch (ReflectiveOperationException e) {
                Quicreate.LOGGER.warn("Quicreate: could not find Mowzie's geomancy classes, Sculptor rocks keep their look", e);
            }
        }
        return getBlock != null && setBlock != null && getBlock.getDeclaringClass().isInstance(entity);
    }
}
