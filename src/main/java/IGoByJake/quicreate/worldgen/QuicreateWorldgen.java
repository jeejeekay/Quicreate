package IGoByJake.quicreate.worldgen;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class QuicreateWorldgen {

    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(ForgeRegistries.FEATURES, Quicreate.MODID);

    /** {@code quicreate:helix}: twisted multi-strand towers (Glacio helix spires). */
    public static final RegistryObject<HelixFeature> HELIX = FEATURES.register("helix", () -> new HelixFeature(HelixConfiguration.CODEC));
    /** {@code quicreate:prism_spike}: tilted triangular spikes and monolith rings (Mercury). */
    public static final RegistryObject<PrismSpikeFeature> PRISM_SPIKE = FEATURES.register("prism_spike", () -> new PrismSpikeFeature(PrismSpikeConfiguration.CODEC));
    /** {@code quicreate:fissure}: lava cracks (Mercury). */
    public static final RegistryObject<FissureFeature> FISSURE = FEATURES.register("fissure", () -> new FissureFeature(FissureConfiguration.CODEC));
    /** {@code quicreate:crater}: impact craters (Moon). */
    public static final RegistryObject<CraterFeature> CRATER = FEATURES.register("crater", () -> new CraterFeature(CraterConfiguration.CODEC));
    /** {@code quicreate:giant_mushroom}: Aeronos and Strophar mushrooms (Mars). */
    public static final RegistryObject<GiantMushroomFeature> GIANT_MUSHROOM = FEATURES.register("giant_mushroom", () -> new GiantMushroomFeature(GiantMushroomConfiguration.CODEC));
    /** {@code quicreate:arch}: rock arches (Mars, Venus). */
    public static final RegistryObject<ArchFeature> ARCH = FEATURES.register("arch", () -> new ArchFeature(ArchConfiguration.CODEC));
    /** {@code quicreate:boulder}: boulder groups. */
    public static final RegistryObject<BoulderFeature> BOULDER = FEATURES.register("boulder", () -> new BoulderFeature(BoulderConfiguration.CODEC));

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES = DeferredRegister.create(Registries.STRUCTURE_TYPE, Quicreate.MODID);
    public static final DeferredRegister<StructurePieceType> STRUCTURE_PIECES = DeferredRegister.create(Registries.STRUCTURE_PIECE, Quicreate.MODID);

    /** {@code quicreate:shape}: a shape built as a structure, for shapes too big for a feature (giant Mars arches). */
    public static final RegistryObject<StructureType<ShapeStructure>> SHAPE_STRUCTURE = STRUCTURE_TYPES.register("shape",
            () -> (StructureType<ShapeStructure>) () -> ShapeStructure.CODEC);
    /** {@code quicreate:repositioned}: another structure moved to a chosen height (Cataclysm structures with fixed heights). */
    public static final RegistryObject<StructureType<RepositionedStructure>> REPOSITIONED = STRUCTURE_TYPES.register("repositioned",
            () -> (StructureType<RepositionedStructure>) () -> RepositionedStructure.CODEC);
    public static final RegistryObject<StructurePieceType> SHAPE_PIECE = STRUCTURE_PIECES.register("shape",
            () -> (StructurePieceType) ShapePiece::new);

    private QuicreateWorldgen() {
    }

    public static void register(IEventBus modBus) {
        FEATURES.register(modBus);
        STRUCTURE_TYPES.register(modBus);
        STRUCTURE_PIECES.register(modBus);
    }
}
