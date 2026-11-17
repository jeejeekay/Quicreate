package IGoByJake.quicreate.worldgen;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.placement.PlacementModifierType;
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
    /** {@code quicreate:wedge}: earthquake slabs pushed up at an angle, with overhanging tips (Mars). */
    public static final RegistryObject<WedgeFeature> WEDGE = FEATURES.register("wedge", () -> new WedgeFeature(WedgeConfiguration.CODEC));

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES = DeferredRegister.create(Registries.STRUCTURE_TYPE, Quicreate.MODID);
    public static final DeferredRegister<StructurePieceType> STRUCTURE_PIECES = DeferredRegister.create(Registries.STRUCTURE_PIECE, Quicreate.MODID);

    /** {@code quicreate:shape}: a shape built as a structure, for shapes too big for a feature (giant Mars arches). */
    public static final RegistryObject<StructureType<ShapeStructure>> SHAPE_STRUCTURE = STRUCTURE_TYPES.register("shape",
            () -> (StructureType<ShapeStructure>) () -> ShapeStructure.CODEC);
    /** {@code quicreate:repositioned}: another structure moved to a chosen height (Cataclysm structures with fixed heights). */
    public static final RegistryObject<StructureType<RepositionedStructure>> REPOSITIONED = STRUCTURE_TYPES.register("repositioned",
            () -> (StructureType<RepositionedStructure>) () -> RepositionedStructure.CODEC);
    /** {@code quicreate:mounded}: another structure with a mountain built around it (Venus ancient factory). */
    public static final RegistryObject<StructureType<MoundedStructure>> MOUNDED = STRUCTURE_TYPES.register("mounded",
            () -> (StructureType<MoundedStructure>) () -> MoundedStructure.CODEC);
    public static final RegistryObject<StructurePieceType> MOUND_PIECE = STRUCTURE_PIECES.register("mound",
            () -> (StructurePieceType) MoundPiece::new);
    public static final RegistryObject<StructurePieceType> SHAPE_PIECE = STRUCTURE_PIECES.register("shape",
            () -> (StructurePieceType) ShapePiece::new);

    public static final DeferredRegister<PlacementModifierType<?>> PLACEMENTS = DeferredRegister.create(Registries.PLACEMENT_MODIFIER_TYPE, Quicreate.MODID);
    /** {@code quicreate:height_limit}: keep only placements between min_y and max_y. */
    public static final RegistryObject<PlacementModifierType<HeightLimitFilter>> HEIGHT_LIMIT = PLACEMENTS.register("height_limit",
            () -> (PlacementModifierType<HeightLimitFilter>) () -> HeightLimitFilter.CODEC);
    /** {@code quicreate:avoid_structures}: skip placements near structures in the quicreate:avoided_by_shapes tag. */
    public static final RegistryObject<PlacementModifierType<AvoidStructuresFilter>> AVOID_STRUCTURES = PLACEMENTS.register("avoid_structures",
            () -> (PlacementModifierType<AvoidStructuresFilter>) () -> AvoidStructuresFilter.CODEC);

    private QuicreateWorldgen() {
    }

    public static void register(IEventBus modBus) {
        FEATURES.register(modBus);
        STRUCTURE_TYPES.register(modBus);
        STRUCTURE_PIECES.register(modBus);
        PLACEMENTS.register(modBus);
    }
}
