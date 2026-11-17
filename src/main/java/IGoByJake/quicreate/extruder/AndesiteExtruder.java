package IGoByJake.quicreate.extruder;

import IGoByJake.quicreate.Quicreate;
import com.oierbravo.createmechanicalextruder.components.extruder.ExtruderRenderer;
import com.oierbravo.createmechanicalextruder.components.extruder.ExtruderVisual;
import com.simibubi.create.api.stress.BlockStressValues;
import dev.engine_room.flywheel.lib.visualization.SimpleBlockEntityVisualizer;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Registers the Andesite Extruder. Only called when Create: Mechanical Extruder is loaded (see Quicreate), so the
 * extruder classes are never touched without it.
 */
public final class AndesiteExtruder {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, Quicreate.MODID);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, Quicreate.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, Quicreate.MODID);

    public static final RegistryObject<AndesiteExtruderBlock> BLOCK = BLOCKS.register("andesite_extruder",
            () -> new AndesiteExtruderBlock(BlockBehaviour.Properties.copy(Blocks.ANDESITE)
                    .mapColor(MapColor.STONE).strength(1.5F, 6.0F).noOcclusion().requiresCorrectToolForDrops()));
    public static final RegistryObject<Item> ITEM = ITEMS.register("andesite_extruder",
            () -> new BlockItem(BLOCK.get(), new Item.Properties()));
    @SuppressWarnings("DataFlowIssue")
    public static final RegistryObject<BlockEntityType<AndesiteExtruderBlockEntity>> BLOCK_ENTITY =
            BLOCK_ENTITIES.register("andesite_extruder", () -> BlockEntityType.Builder.of(
                    (pos, state) -> new AndesiteExtruderBlockEntity(AndesiteExtruder.BLOCK_ENTITY.get(), pos, state),
                    BLOCK.get()).build(null));

    /** Stress per rpm. The brass Mechanical Extruder costs 64 in this pack; the andesite one is an early machine. */
    public static final double STRESS_IMPACT = 4.0;

    private AndesiteExtruder() {
    }

    public static void register(IEventBus modBus) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        BLOCK_ENTITIES.register(modBus);
        modBus.addListener(AndesiteExtruder::commonSetup);
        modBus.addListener(AndesiteExtruder::creativeTab);
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> modBus.addListener(Client::clientSetup));
    }

    private static void commonSetup(FMLCommonSetupEvent event) {
        event.enqueueWork(() -> BlockStressValues.IMPACTS.register(BLOCK.get(), () -> STRESS_IMPACT));
    }

    private static void creativeTab(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.FUNCTIONAL_BLOCKS) {
            event.accept(ITEM);
        }
    }

    /** Client-only: reuse the Mechanical Extruder's renderer (filter slot) and Flywheel visual (pole and shaft). */
    static final class Client {
        static void clientSetup(FMLClientSetupEvent event) {
            event.enqueueWork(() -> {
                BlockEntityRenderers.register(BLOCK_ENTITY.get(), ExtruderRenderer::new);
                SimpleBlockEntityVisualizer.builder(BLOCK_ENTITY.get())
                        .factory(ExtruderVisual::new)
                        .skipVanillaRender(be -> false)
                        .apply();
            });
        }
    }
}
