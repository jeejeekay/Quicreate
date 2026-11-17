package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;

import java.util.Optional;

/**
 * {@code quicreate:shape}: places one of Quicreate's shapes (a configured feature such as
 * {@code quicreate:mars_arch}) as a structure. Features can only write a 48x48 area, structures
 * can be far bigger, so this is how the giant Mars arches are built. The shape is built from the
 * terrain's base height, so every chunk it crosses builds exactly the same arch.
 */
public class ShapeStructure extends Structure {

    public static final Codec<ShapeStructure> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            settingsCodec(instance),
            ConfiguredFeature.CODEC.fieldOf("feature").forGetter(structure -> structure.feature)
    ).apply(instance, ShapeStructure::new));

    private final Holder<ConfiguredFeature<?, ?>> feature;

    public ShapeStructure(StructureSettings settings, Holder<ConfiguredFeature<?, ?>> feature) {
        super(settings);
        this.feature = feature;
    }

    @Override
    public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        if (!(feature.value().feature() instanceof ShapedFeature<?>) || feature.unwrapKey().isEmpty()) {
            return Optional.empty(); // only named Quicreate shapes can be saved with the chunk
        }
        ChunkPos chunk = context.chunkPos();
        int x = chunk.getMiddleBlockX();
        int z = chunk.getMiddleBlockZ();
        ChunkGenerator generator = context.chunkGenerator();
        int y = generator.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, context.heightAccessor(), context.randomState());
        BlockPos origin = new BlockPos(x, y, z);
        long seed = context.random().nextLong();
        return Optional.of(new GenerationStub(origin, builder -> {
            ShapePiece piece = ShapePiece.create(feature.unwrapKey().get().location(), feature.value(), seed, origin,
                    ground(generator, context.heightAccessor(), context.randomState(), origin));
            if (piece != null) {
                builder.addPiece(piece);
            }
        }));
    }

    /** Ground samples are taken this far apart and blended in between: working out the terrain height is slow. */
    private static final int GROUND_STEP = 4;

    /**
     * Ground from the terrain noise alone, so it's the same however much of the world exists yet,
     * and the same in every chunk (sampled on a fixed world grid and blended).
     */
    static ShapedFeature.Ground ground(ChunkGenerator generator, LevelHeightAccessor heights, RandomState randomState, BlockPos origin) {
        java.util.Map<Long, Integer> samples = new java.util.HashMap<>();
        java.util.function.BiFunction<Integer, Integer, Integer> sample = (wx, wz) -> samples.computeIfAbsent(((long) wx << 32) ^ (wz & 0xFFFFFFFFL),
                key -> generator.getBaseHeight(wx, wz, Heightmap.Types.WORLD_SURFACE_WG, heights, randomState));
        return (dx, dz) -> {
            int wx = origin.getX() + dx, wz = origin.getZ() + dz;
            int gx = Math.floorDiv(wx, GROUND_STEP) * GROUND_STEP, gz = Math.floorDiv(wz, GROUND_STEP) * GROUND_STEP;
            double fx = (wx - gx) / (double) GROUND_STEP, fz = (wz - gz) / (double) GROUND_STEP;
            double h00 = sample.apply(gx, gz), h10 = sample.apply(gx + GROUND_STEP, gz);
            double h01 = sample.apply(gx, gz + GROUND_STEP), h11 = sample.apply(gx + GROUND_STEP, gz + GROUND_STEP);
            double h = (h00 * (1 - fx) + h10 * fx) * (1 - fz) + (h01 * (1 - fx) + h11 * fx) * fz;
            return (int) Math.round(h) - 1 - origin.getY();
        };
    }

    @Override
    public StructureType<?> type() {
        return QuicreateWorldgen.SHAPE_STRUCTURE.get();
    }
}
