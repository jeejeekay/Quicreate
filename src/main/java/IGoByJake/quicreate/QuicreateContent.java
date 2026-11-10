package IGoByJake.quicreate;

import IGoByJake.quicreate.entity.SwordBeamEntity;
import IGoByJake.quicreate.loot.KelpyFishingModifier;
import com.mojang.serialization.Codec;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Entities and loot modifiers (items and blocks stay in ModRegistry). */
public final class QuicreateContent {

    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, Quicreate.MODID);
    public static final DeferredRegister<Codec<? extends IGlobalLootModifier>> LOOT_MODIFIERS =
            DeferredRegister.create(ForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, Quicreate.MODID);

    public static final RegistryObject<EntityType<SwordBeamEntity>> SWORD_BEAM = ENTITIES.register("sword_beam",
            () -> EntityType.Builder.<SwordBeamEntity>of(SwordBeamEntity::new, MobCategory.MISC)
                    .sized(0.5F, 0.5F)
                    .clientTrackingRange(4)
                    .updateInterval(2)
                    .build("sword_beam"));

    public static final RegistryObject<Codec<KelpyFishingModifier>> KELPY_FISHING = LOOT_MODIFIERS.register("fishing_kelpy_balls", KelpyFishingModifier.CODEC);

    private QuicreateContent() {
    }

    public static void register(IEventBus modBus) {
        ENTITIES.register(modBus);
        LOOT_MODIFIERS.register(modBus);
    }
}
