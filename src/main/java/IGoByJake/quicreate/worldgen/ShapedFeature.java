package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Predicate;

/**
 * Base for Quicreate's terrain shapes (spikes, fissures, craters, mushrooms, arches, boulders).
 * Each feature describes its blocks as a {@link Shape}; this class handles placing it.
 * <p>
 * During world generation a feature may only write within the chunk being decorated and the ring of
 * chunks around it (a 48x48 area). Rather than letting big shapes get sliced off with flat walls, the
 * whole shape is shifted sideways until it fits, then rebuilt on the ground at its new spot.
 * {@code /qshape} uses the same code, so a tested shape is exactly what generates.
 */
public abstract class ShapedFeature<C extends FeatureConfiguration> extends Feature<C> {

    /** Widest a shape should be built so it can always be shifted into the writable area. */
    public static final int MAX_SPAN = 44;

    private final Codec<C> configCodec;

    protected ShapedFeature(Codec<C> codec) {
        super(codec);
        this.configCodec = codec;
    }

    public Codec<C> configCodec() {
        return configCodec;
    }

    /** Fills {@code shape} with blocks around (0,0,0), the origin (the first air block above the ground). */
    protected abstract void build(C config, RandomSource random, Ground ground, Shape shape);

    /** Height of the top solid block at an offset from the origin, relative to the origin's y. */
    @FunctionalInterface
    public interface Ground {
        int at(int dx, int dz);
    }

    private record Bounds(int minX, int maxX, int minZ, int maxZ) {
        boolean contains(BlockPos pos) {
            return pos.getX() >= minX && pos.getX() <= maxX && pos.getZ() >= minZ && pos.getZ() <= maxZ;
        }
    }

    @Override
    public boolean place(FeaturePlaceContext<C> context) {
        WorldGenLevel level = context.level();
        C config = context.config();
        RandomSource random = context.random();
        BlockPos origin = context.origin();
        long seed = random.nextLong();

        Shape shape = make(config, seed, level, origin);
        if (shape.isEmpty()) {
            return false;
        }
        Bounds bounds = bounds(level);
        if (bounds != null) {
            int sx = fit(shape.minX() + origin.getX(), shape.maxX() + origin.getX(), bounds.minX(), bounds.maxX());
            int sz = fit(shape.minZ() + origin.getZ(), shape.maxZ() + origin.getZ(), bounds.minZ(), bounds.maxZ());
            if (sx != 0 || sz != 0) {
                int x = origin.getX() + sx;
                int z = origin.getZ() + sz;
                origin = new BlockPos(x, level.getHeight(heightmap(level), x, z), z);
                shape = make(config, seed, level, origin);
            }
        }
        return write(shape, level, origin, bounds, random);
    }

    private Shape make(C config, long seed, WorldGenLevel level, BlockPos origin) {
        return buildShape(config, seed, ground(level, origin));
    }

    /** Builds the shape with a fixed seed, so the same seed and ground always give the same blocks. */
    public Shape buildShape(C config, long seed, Ground ground) {
        Shape shape = new Shape();
        build(config, RandomSource.create(seed), ground, shape);
        return shape;
    }

    private static boolean write(Shape shape, WorldGenLevel level, BlockPos origin, Bounds bounds, RandomSource random) {
        Predicate<BlockPos> allowed = bounds == null ? null : bounds::contains;
        return writeFiltered(shape, level, origin, allowed, random);
    }

    /** Writes the shape's blocks that pass {@code allowed} (null = all), using the FORCE/BUILD rules. */
    public static boolean writeFiltered(Shape shape, WorldGenLevel level, BlockPos origin, Predicate<BlockPos> allowed, RandomSource random) {
        boolean placed = false;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (Map.Entry<BlockPos, Shape.Put> entry : shape.blocks().entrySet()) {
            pos.setWithOffset(origin, entry.getKey());
            if (pos.getY() <= level.getMinBuildHeight() || pos.getY() >= level.getMaxBuildHeight()) {
                continue;
            }
            if ((allowed != null && !allowed.test(pos)) || !level.ensureCanWrite(pos)) {
                continue;
            }
            BlockState existing = level.getBlockState(pos);
            if (existing.hasBlockEntity() || existing.getDestroySpeed(level, pos) < 0) {
                continue; // never break chests, spawners, bedrock and the like
            }
            if (entry.getValue().mode() == Shape.Mode.BUILD && !existing.isAir() && !existing.canBeReplaced()) {
                continue;
            }
            BlockState state = entry.getValue().block().getState(random, pos);
            if (state != existing) {
                level.setBlock(pos, state, Block.UPDATE_CLIENTS);
                placed = true;
            }
        }
        return placed;
    }

    /** The writable area during world generation, or null when placing in a live world (the command). */
    private static Bounds bounds(WorldGenLevel level) {
        if (level instanceof WorldGenRegion region) {
            ChunkPos centre = region.getCenter();
            return new Bounds(centre.getMinBlockX() - 16, centre.getMaxBlockX() + 16, centre.getMinBlockZ() - 16, centre.getMaxBlockZ() + 16);
        }
        return null;
    }

    /** How far to move [min, max] so it lies inside [lo, hi] (with a 1 block margin). */
    private static int fit(int min, int max, int lo, int hi) {
        lo += 1;
        hi -= 1;
        if (max - min > hi - lo) {
            return (lo + hi) / 2 - (min + max) / 2;
        }
        if (min < lo) {
            return lo - min;
        }
        if (max > hi) {
            return hi - max;
        }
        return 0;
    }

    private static Heightmap.Types heightmap(WorldGenLevel level) {
        return level instanceof WorldGenRegion ? Heightmap.Types.WORLD_SURFACE_WG : Heightmap.Types.WORLD_SURFACE;
    }

    private static Ground ground(WorldGenLevel level, BlockPos origin) {
        Heightmap.Types type = heightmap(level);
        Map<Long, Integer> cache = new HashMap<>();
        int ox = origin.getX();
        int oy = origin.getY();
        int oz = origin.getZ();
        return (dx, dz) -> cache.computeIfAbsent(((long) dx << 32) ^ (dz & 0xFFFFFFFFL),
                key -> level.getHeight(type, ox + dx, oz + dz) - 1 - oy);
    }

    // ---- Helpers shared by the shapes ----

    /** A filled horizontal disk. */
    protected static void disk(Shape shape, double cx, int y, double cz, double radius, BlockStateProvider block, Shape.Mode mode) {
        int reach = (int) Math.ceil(radius) + 1;
        int bx = (int) Math.round(cx);
        int bz = (int) Math.round(cz);
        double limit = (radius + 0.25) * (radius + 0.25);
        for (int x = bx - reach; x <= bx + reach; x++) {
            for (int z = bz - reach; z <= bz + reach; z++) {
                if ((x - cx) * (x - cx) + (z - cz) * (z - cz) <= limit) {
                    shape.set(x, y, z, block, mode);
                }
            }
        }
    }

    /** A filled ellipsoid. */
    protected static void ellipsoid(Shape shape, double cx, double cy, double cz, double rx, double ry, double rz,
                                    BlockStateProvider block, Shape.Mode mode) {
        rx = Math.max(rx, 0.5);
        ry = Math.max(ry, 0.5);
        rz = Math.max(rz, 0.5);
        for (int x = (int) Math.floor(cx - rx); x <= (int) Math.ceil(cx + rx); x++) {
            for (int y = (int) Math.floor(cy - ry); y <= (int) Math.ceil(cy + ry); y++) {
                for (int z = (int) Math.floor(cz - rz); z <= (int) Math.ceil(cz + rz); z++) {
                    double fx = (x - cx) / rx;
                    double fy = (y - cy) / ry;
                    double fz = (z - cz) / rz;
                    if (fx * fx + fy * fy + fz * fz <= 1.0) {
                        shape.set(x, y, z, block, mode);
                    }
                }
            }
        }
    }
}
