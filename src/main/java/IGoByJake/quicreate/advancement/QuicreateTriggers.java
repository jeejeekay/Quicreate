package IGoByJake.quicreate.advancement;

import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;

/** Registers Quicreate's advancement triggers and polls the inventory trigger once a second. */
@Mod.EventBusSubscriber(modid = "quicreate", bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class QuicreateTriggers {
    public static HasItemsTrigger HAS_ITEMS;

    private QuicreateTriggers() {
    }

    /** Called from the mod constructor. The trigger map is not thread-safe, so register on the main thread. */
    public static void init(IEventBus modBus) {
        modBus.addListener((FMLCommonSetupEvent event) ->
                event.enqueueWork(() -> HAS_ITEMS = CriteriaTriggers.register(new HasItemsTrigger())));
    }

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || !(event.player instanceof ServerPlayer player)) {
            return;
        }
        // spread players over the second so a full server doesn't check everyone on the same tick
        if (HAS_ITEMS != null && (player.tickCount + player.getId()) % 20 == 0) {
            HAS_ITEMS.trigger(player);
        }
    }
}
