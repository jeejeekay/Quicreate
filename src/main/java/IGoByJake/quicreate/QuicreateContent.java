package IGoByJake.quicreate;

import IGoByJake.quicreate.book.PreviewItemBlock;
import IGoByJake.quicreate.entity.SwordBeamEntity;
import IGoByJake.quicreate.loot.KelpyFishingModifier;
import com.mojang.serialization.Codec;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Entities, loot modifiers and the Field Guide's preview stand-in blocks (items and real blocks stay in ModRegistry). */
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

    /** The obsidian rod's bobber: floats on lava, doesn't burn (see LavaFishingHook). */
    public static final RegistryObject<EntityType<IGoByJake.quicreate.entity.LavaFishingHook>> LAVA_FISHING_HOOK = ENTITIES.register("lava_fishing_hook",
            () -> EntityType.Builder.<IGoByJake.quicreate.entity.LavaFishingHook>of(IGoByJake.quicreate.entity.LavaFishingHook::new, MobCategory.MISC)
                    .noSave()
                    .noSummon()
                    .fireImmune()
                    .sized(0.25F, 0.25F)
                    .clientTrackingRange(4)
                    .updateInterval(5)
                    .build("lava_fishing_hook"));

    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, Quicreate.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, Quicreate.MODID);

    /** Book-preview stand-in for Create: New Age's generator coil (see PreviewItemBlock). Has no item. */
    public static final RegistryObject<Block> PREVIEW_GENERATOR_COIL = BLOCKS.register("preview_generator_coil",
            () -> new PreviewItemBlock(BlockBehaviour.Properties.of().noCollission().noOcclusion().noLootTable()
                    .instabreak().pushReaction(PushReaction.DESTROY), new ResourceLocation("create_new_age", "generator_coil")));

    @SuppressWarnings("DataFlowIssue")
    public static final RegistryObject<BlockEntityType<PreviewItemBlock.PreviewItemBlockEntity>> PREVIEW_ITEM_BE = BLOCK_ENTITIES.register("preview_item",
            () -> BlockEntityType.Builder.of(PreviewItemBlock.PreviewItemBlockEntity::new, PREVIEW_GENERATOR_COIL.get()).build(null));

    public static final RegistryObject<Codec<KelpyFishingModifier>> KELPY_FISHING = LOOT_MODIFIERS.register("fishing_kelpy_balls", KelpyFishingModifier.CODEC);

    private QuicreateContent() {
    }

    public static void register(IEventBus modBus) {
        ENTITIES.register(modBus);
        LOOT_MODIFIERS.register(modBus);
        BLOCKS.register(modBus);
        BLOCK_ENTITIES.register(modBus);
    }
}
