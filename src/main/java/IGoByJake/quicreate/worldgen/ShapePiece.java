package IGoByJake.quicreate.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * The single piece of a {@link ShapeStructure}. It saves only the shape's name, seed and origin;
 * each chunk rebuilds the shape and writes the part inside that chunk. A few recent shapes are
 * kept in memory so a big arch isn't rebuilt for every chunk it crosses.
 */
public class ShapePiece extends StructurePiece {

    private static final int CACHE_SIZE = 6;
    private static final Map<String, Shape> CACHE = new LinkedHashMap<>(16, 0.75F, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, Shape> eldest) {
            return size() > CACHE_SIZE;
        }
    };

    private final ResourceLocation featureId;
    private final ConfiguredFeature<?, ?> feature;
    private final long seed;
    private final BlockPos origin;

    private ShapePiece(ResourceLocation featureId, ConfiguredFeature<?, ?> feature, long seed, BlockPos origin, BoundingBox box) {
        super(QuicreateWorldgen.SHAPE_PIECE.get(), 0, box);
        this.featureId = featureId;
        this.feature = feature;
        this.seed = seed;
        this.origin = origin;
    }

    /** Builds the shape once to size the piece; null if it came out empty. */
    static ShapePiece create(ResourceLocation featureId, ConfiguredFeature<?, ?> feature, long seed, BlockPos origin, ShapedFeature.Ground ground) {
        Shape shape = build(feature, seed, ground);
        if (shape == null || shape.isEmpty()) {
            return null;
        }
        remember(featureId, seed, origin, shape);
        BoundingBox box = new BoundingBox(origin.getX() + shape.minX(), origin.getY() + shape.minY(), origin.getZ() + shape.minZ(),
                origin.getX() + shape.maxX(), origin.getY() + shape.maxY(), origin.getZ() + shape.maxZ());
        return new ShapePiece(featureId, feature, seed, origin, box);
    }

    public ShapePiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(QuicreateWorldgen.SHAPE_PIECE.get(), tag);
        this.featureId = new ResourceLocation(tag.getString("feature"));
        this.feature = context.registryAccess().registryOrThrow(Registries.CONFIGURED_FEATURE).get(featureId);
        this.seed = tag.getLong("seed");
        this.origin = NbtUtils.readBlockPos(tag.getCompound("origin"));
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        tag.putString("feature", featureId.toString());
        tag.putLong("seed", seed);
        tag.put("origin", NbtUtils.writeBlockPos(origin));
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                            BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
        if (feature == null) {
            return; // the shape was removed from the data pack
        }
        Shape shape = recall(featureId, seed, origin);
        if (shape == null) {
            shape = build(feature, seed, ShapeStructure.ground(generator, level, level.getLevel().getChunkSource().randomState(), origin));
            if (shape == null) {
                return;
            }
            remember(featureId, seed, origin, shape);
        }
        ShapedFeature.writeFiltered(shape, level, origin, chunkBox::isInside, random);
    }

    private static Shape build(ConfiguredFeature<?, ?> feature, long seed, ShapedFeature.Ground ground) {
        if (feature.feature() instanceof ShapedFeature<?> shaped) {
            return buildWith(shaped, feature.config(), seed, ground);
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static <C extends FeatureConfiguration> Shape buildWith(ShapedFeature<C> shaped, FeatureConfiguration config, long seed, ShapedFeature.Ground ground) {
        return shaped.buildShape((C) config, seed, ground);
    }

    private static String key(ResourceLocation featureId, long seed, BlockPos origin) {
        return featureId + "/" + seed + "/" + origin.asLong();
    }

    private static void remember(ResourceLocation featureId, long seed, BlockPos origin, Shape shape) {
        synchronized (CACHE) {
            CACHE.put(key(featureId, seed, origin), shape);
        }
    }

    private static Shape recall(ResourceLocation featureId, long seed, BlockPos origin) {
        synchronized (CACHE) {
            return CACHE.get(key(featureId, seed, origin));
        }
    }
}
