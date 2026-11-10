package IGoByJake.quicreate.client;

import IGoByJake.quicreate.ModRegistry;
import IGoByJake.quicreate.Quicreate;
import IGoByJake.quicreate.QuicreateContent;
import net.minecraft.client.renderer.entity.NoopRenderer;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.FishingRodItem;
import net.minecraft.world.item.Item;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.registries.RegistryObject;

import java.util.List;

@Mod.EventBusSubscriber(modid = Quicreate.MODID, value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class QuicreateClient {

    private QuicreateClient() {
    }

    @SubscribeEvent
    public static void onRegisterRenderers(EntityRenderersEvent.RegisterRenderers event) {
        // The sword beam is drawn entirely with particles.
        event.registerEntityRenderer(QuicreateContent.SWORD_BEAM.get(), NoopRenderer::new);
    }

    @SubscribeEvent
    public static void onClientSetup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            // Same "cast" switch vanilla gives its fishing rod, so the line disappears while fishing.
            for (RegistryObject<Item> rod : List.of(ModRegistry.BRASS_FISHING_ROD, ModRegistry.DESH_FISHING_ROD, ModRegistry.OSTRUM_FISHING_ROD)) {
                ItemProperties.register(rod.get(), new ResourceLocation("cast"), (stack, level, entity, seed) -> {
                    if (!(entity instanceof Player player) || player.fishing == null) {
                        return 0.0F;
                    }
                    boolean main = entity.getMainHandItem() == stack;
                    boolean off = entity.getOffhandItem() == stack && !(entity.getMainHandItem().getItem() instanceof FishingRodItem);
                    return main || off ? 1.0F : 0.0F;
                });
            }
        });
    }
}
