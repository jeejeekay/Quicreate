package IGoByJake.quicreate.compat;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.level.LevelEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.server.ServerLifecycleHooks;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
/**
 * Fix for landing on a planet in the void.
 * <p>
 * Modonomicon (the guide book's mod) syncs book progress when a player joins a level. It keeps its save data in one
 * shared object and clears it whenever <i>any</i> overworld level unloads, including the client's own copy. In single
 * player the client and server share that object, so when a rocket leaves Earth the client can clear it in the middle
 * of the server's landing. Modonomicon then throws, the exception aborts Ad Astra's teleport half-way, and the player
 * ends up in the new dimension without being registered for chunk loading: nothing loads and you float in the void.
 * The log shows it as "BookStatesSaveData ... because this.saveData is null" from AdAstraTeleporter.placeEntity,
 * followed by "objectset is null" errors on every move.
 * <p>
 * Fix: remember the server's save data, put it back right after a client-side overworld unload clears it, and make
 * sure it is set before Modonomicon's join listener runs.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID)
public final class PlanetArrivalFixes {

    private static boolean lookedUp;
    private static Field unlockData;
    private static Field visualData;
    private static Method unlockGet;
    private static Method visualGet;
    private static volatile Object cachedUnlock;
    private static volatile Object cachedVisual;
    private static volatile MinecraftServer cachedServer;

    private PlanetArrivalFixes() {
    }

    // ---- Modonomicon save data ---------------------------------------------------------------------------

    private static boolean lookUp() {
        if (!lookedUp) {
            lookedUp = true;
            try {
                Class<?> unlock = Class.forName("com.klikli_dev.modonomicon.bookstate.BookUnlockStateManager");
                Class<?> visual = Class.forName("com.klikli_dev.modonomicon.bookstate.BookVisualStateManager");
                unlockGet = unlock.getMethod("get");
                visualGet = visual.getMethod("get");
                unlockData = unlock.getField("saveData");
                visualData = visual.getField("saveData");
            } catch (ReflectiveOperationException | LinkageError e) {
                unlockGet = null; // Modonomicon missing or changed: nothing to fix
            }
        }
        return unlockGet != null;
    }

    /** Remember the server's save data while the server runs. */
    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || event.getServer().getTickCount() % 20 != 0 || !lookUp()) {
            return;
        }
        try {
            Object u = unlockData.get(unlockGet.invoke(null));
            Object v = visualData.get(visualGet.invoke(null));
            cachedServer = event.getServer();
            if (u != null) cachedUnlock = u;
            if (v != null) cachedVisual = v;
        } catch (ReflectiveOperationException ignored) {
        }
    }

    private static void restore() {
        if ((cachedUnlock == null && cachedVisual == null) || !lookUp()) {
            return;
        }
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server == null || server != cachedServer || !server.isRunning()) {
            return;
        }
        try {
            Object um = unlockGet.invoke(null);
            Object vm = visualGet.invoke(null);
            if (unlockData.get(um) == null && cachedUnlock != null) unlockData.set(um, cachedUnlock);
            if (visualData.get(vm) == null && cachedVisual != null) visualData.set(vm, cachedVisual);
        } catch (ReflectiveOperationException ignored) {
        }
    }

    /** The client unloading its overworld copy clears the server's data too: put it straight back. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onUnload(LevelEvent.Unload event) {
        if (event.getLevel().isClientSide()) {
            restore();
        }
    }

    /** Runs before Modonomicon's own join listener. */
    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void onJoin(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide()) {
            return;
        }
        if (event.getEntity() instanceof ServerPlayer) {
            restore();
        }
    }

    @SubscribeEvent
    public static void onServerStopped(ServerStoppedEvent event) {
        cachedUnlock = null;
        cachedVisual = null;
        cachedServer = null;
        // Start the next world with fresh book data, as Modonomicon expects
        if (lookUp()) {
            try {
                unlockData.set(unlockGet.invoke(null), null);
                visualData.set(visualGet.invoke(null), null);
            } catch (ReflectiveOperationException ignored) {
            }
        }
    }
}
