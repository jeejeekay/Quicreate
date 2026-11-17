package IGoByJake.quicreate.entity;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.common.ForgeMod;
import net.minecraftforge.event.entity.EntityAttributeModificationEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.Map;

/**
 * Lets some mobs walk up full blocks instead of hopping. Mobs jump whenever the next block is higher
 * than their step height (0.6 by default); adding 0.5 makes it 1.1, so one-block rises are walked.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class StepHeights {

    /** Mob id to extra step height (blocks). */
    private static final Map<String, Double> EXTRA = Map.of(
            "ad_astra:star_crawler", 0.5
    );

    private StepHeights() {
    }

    @SubscribeEvent
    @SuppressWarnings("unchecked")
    public static void onAttributes(EntityAttributeModificationEvent event) {
        for (Map.Entry<String, Double> entry : EXTRA.entrySet()) {
            ResourceLocation id = new ResourceLocation(entry.getKey());
            if (!ForgeRegistries.ENTITY_TYPES.containsKey(id)) {
                continue; // that mod isn't installed (an unknown id would give the default, pigs)
            }
            EntityType<?> type = ForgeRegistries.ENTITY_TYPES.getValue(id);
            if (type == null || !event.getTypes().contains(type)) {
                continue; // the mob has no attributes
            }
            event.add((EntityType<? extends LivingEntity>) type, ForgeMod.STEP_HEIGHT_ADDITION.get(), entry.getValue());
        }
    }
}
