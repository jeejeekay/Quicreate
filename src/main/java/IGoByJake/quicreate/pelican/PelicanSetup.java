package IGoByJake.quicreate.pelican;

import IGoByJake.quicreate.Quicreate;
import IGoByJake.quicreate.QuicreateContent;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = Quicreate.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class PelicanSetup {
    private PelicanSetup() {}

    @SubscribeEvent
    public static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(QuicreateContent.PELICAN.get(), Pelican.attributes().build());
    }
}
