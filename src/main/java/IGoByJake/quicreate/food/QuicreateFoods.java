package IGoByJake.quicreate.food;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.List;

/**
 * Quicreate's own omelettes, in the Neopian Omelettes style (3 eggs + one ingredient, eaten in three bites).
 * <ul>
 *   <li>Amethyst Crab: the crab meat's own effect, Regeneration I for 5 s, each bite.</li>
 *   <li>Blessed Amethyst Crab: the blessed meat's effects, Regeneration I for 5 s and Blessing of Amethyst for 90 s,
 *       each bite. Blessing makes you immune to darkness, abyssal fear and abyssal burn (the Leviathan fight).</li>
 *   <li>Moon Cheese: Jump Boost I for 30 s each bite, for low gravity.</li>
 * </ul>
 */
public final class QuicreateFoods {

    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, Quicreate.MODID);
    private static final ResourceLocation BLESSING = new ResourceLocation("cataclysm", "blessing_of_amethyst");

    private static final FoodProperties CRAB = new FoodProperties.Builder().nutrition(7).saturationMod(0.6F)
            .effect(() -> new MobEffectInstance(MobEffects.REGENERATION, 100, 0), 1.0F).alwaysEat().build();
    private static final FoodProperties BLESSED_CRAB = new FoodProperties.Builder().nutrition(7).saturationMod(0.8F)
            .effect(() -> new MobEffectInstance(MobEffects.REGENERATION, 100, 0), 1.0F)
            .effect(QuicreateFoods::blessing, 1.0F).alwaysEat().build();
    private static final FoodProperties MOON_CHEESE = new FoodProperties.Builder().nutrition(6).saturationMod(0.6F)
            .effect(() -> new MobEffectInstance(MobEffects.JUMP, 600, 0), 1.0F).build();

    public static final List<RegistryObject<Item>> CRAB_OMELETTE = stages("amethyst_crab_omelette", CRAB, false, null);
    public static final List<RegistryObject<Item>> BLESSED_CRAB_OMELETTE = stages("blessed_amethyst_crab_omelette", BLESSED_CRAB, true,
            "item.cataclysm.blessed_amethyst_crab_meat.desc");
    public static final List<RegistryObject<Item>> MOON_CHEESE_OMELETTE = stages("moon_cheese_omelette", MOON_CHEESE, false, null);

    private QuicreateFoods() {
    }

    private static MobEffectInstance blessing() {
        MobEffect effect = ForgeRegistries.MOB_EFFECTS.getValue(BLESSING);
        // Cataclysm missing: fall back to plain resistance so the food still works
        return effect != null ? new MobEffectInstance(effect, 1800, 0) : new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 1800, 0);
    }

    /** name, name_2, name_3: each bite gives the food and returns the next one. */
    private static List<RegistryObject<Item>> stages(String name, FoodProperties food, boolean foil, String tooltip) {
        RegistryObject<Item> third = ITEMS.register(name + "_3",
                () -> new OmeletteItem(new Item.Properties().food(food), null, foil, tooltip));
        RegistryObject<Item> second = ITEMS.register(name + "_2",
                () -> new OmeletteItem(new Item.Properties().food(food), third, foil, tooltip));
        RegistryObject<Item> first = ITEMS.register(name,
                () -> new OmeletteItem(new Item.Properties().food(food), second, foil, tooltip));
        return List.of(first, second, third);
    }

    public static void register(IEventBus modBus) {
        ITEMS.register(modBus);
    }
}
