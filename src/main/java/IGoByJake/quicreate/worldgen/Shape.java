package IGoByJake.quicreate.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.HashMap;
import java.util.Map;

/**
 * The blocks one {@link ShapedFeature} wants to place, as offsets from the feature's origin.
 * FORCE blocks replace terrain (carving, rock that sinks into the ground); BUILD blocks only fill
 * air and replaceable blocks (caps, rims, anything that should sit on top of the world). FOUNDATION blocks
 * are FORCE blocks that also fill any gap underneath them.
 */
public final class Shape {

    public static final BlockStateProvider AIR = BlockStateProvider.simple(Blocks.AIR);

    public enum Mode {
        FORCE,
        BUILD,
        /** Like FORCE, then fills down to the first solid block below, so it never floats (crater rims). */
        FOUNDATION
    }

    public record Put(BlockStateProvider block, Mode mode) {
    }

    private final Map<BlockPos, Put> blocks = new HashMap<>();
    /** False for a shape that only measures its size (see {@link #measuring()}). */
    private final boolean store;
    /** Blocks outside this area are ignored (see {@link #clipped}). */
    private final int clipMinX, clipMaxX, clipMinZ, clipMaxZ;
    private boolean any;
    private int minX = Integer.MAX_VALUE;
    private int maxX = Integer.MIN_VALUE;
    private int minZ = Integer.MAX_VALUE;
    private int maxZ = Integer.MIN_VALUE;
    private int minY = Integer.MAX_VALUE;
    private int maxY = Integer.MIN_VALUE;

    public Shape() {
        this(true, Integer.MIN_VALUE, Integer.MAX_VALUE, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }

    private Shape(boolean store, int clipMinX, int clipMaxX, int clipMinZ, int clipMaxZ) {
        this.store = store;
        this.clipMinX = clipMinX;
        this.clipMaxX = clipMaxX;
        this.clipMinZ = clipMinZ;
        this.clipMaxZ = clipMaxZ;
    }

    /** A shape that keeps no blocks, only its size: cheap way to size a giant structure. */
    public static Shape measuring() {
        return new Shape(false, Integer.MIN_VALUE, Integer.MAX_VALUE, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }

    /** A shape that keeps only the blocks in one area (one chunk of a giant structure). */
    public static Shape clipped(int minX, int maxX, int minZ, int maxZ) {
        return new Shape(true, minX, maxX, minZ, maxZ);
    }

    /** True if nothing in this column would be kept, so a shape can skip working it out. */
    public boolean skipColumn(int x, int z) {
        return x < clipMinX || x > clipMaxX || z < clipMinZ || z > clipMaxZ;
    }

    public int clipMinX() {
        return clipMinX;
    }

    public int clipMaxX() {
        return clipMaxX;
    }

    public int clipMinZ() {
        return clipMinZ;
    }

    public int clipMaxZ() {
        return clipMaxZ;
    }

    public void set(int x, int y, int z, BlockStateProvider block, Mode mode) {
        if (skipColumn(x, z)) {
            return;
        }
        if (store) {
            blocks.put(new BlockPos(x, y, z), new Put(block, mode));
        }
        any = true;
        track(x, z);
        trackY(y);
    }

    public void setIfAbsent(int x, int y, int z, BlockStateProvider block, Mode mode) {
        if (skipColumn(x, z)) {
            return;
        }
        if (!store) {
            set(x, y, z, block, mode);
        } else if (blocks.putIfAbsent(new BlockPos(x, y, z), new Put(block, mode)) == null) {
            any = true;
            track(x, z);
            trackY(y);
        }
    }

    public boolean has(int x, int y, int z) {
        return blocks.containsKey(new BlockPos(x, y, z));
    }

    public void addAll(Shape other) {
        blocks.putAll(other.blocks);
        if (!other.isEmpty()) {
            track(other.minX, other.minZ);
            track(other.maxX, other.maxZ);
            trackY(other.minY);
            trackY(other.maxY);
        }
    }

    /** True if this shape and {@code other} together stay within {@code span} blocks on both horizontal axes. */
    public boolean fitsWith(Shape other, int span) {
        if (isEmpty() || other.isEmpty()) {
            return true;
        }
        return Math.max(maxX, other.maxX) - Math.min(minX, other.minX) <= span
                && Math.max(maxZ, other.maxZ) - Math.min(minZ, other.minZ) <= span;
    }

    private void track(int x, int z) {
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minZ = Math.min(minZ, z);
        maxZ = Math.max(maxZ, z);
    }

    private void trackY(int y) {
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
    }

    public Map<BlockPos, Put> blocks() {
        return blocks;
    }

    public boolean isEmpty() {
        return store ? blocks.isEmpty() : !any;
    }

    public int minX() {
        return minX;
    }

    public int maxX() {
        return maxX;
    }

    public int minZ() {
        return minZ;
    }

    public int maxZ() {
        return maxZ;
    }

    public int minY() {
        return minY;
    }

    public int maxY() {
        return maxY;
    }
}
