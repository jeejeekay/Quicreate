package IGoByJake.quicreate.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.HashMap;
import java.util.Map;

/**
 * The blocks one {@link ShapedFeature} wants to place, as offsets from the feature's origin.
 * FORCE blocks replace terrain (carving, rock that sinks into the ground); BUILD blocks only fill
 * air and replaceable blocks (caps, rims, anything that should sit on top of the world).
 */
public final class Shape {

    public static final BlockStateProvider AIR = BlockStateProvider.simple(Blocks.AIR);

    public enum Mode {
        FORCE,
        BUILD
    }

    public record Put(BlockStateProvider block, Mode mode) {
    }

    private final Map<BlockPos, Put> blocks = new HashMap<>();
    private int minX = Integer.MAX_VALUE;
    private int maxX = Integer.MIN_VALUE;
    private int minZ = Integer.MAX_VALUE;
    private int maxZ = Integer.MIN_VALUE;
    private int minY = Integer.MAX_VALUE;
    private int maxY = Integer.MIN_VALUE;

    public void set(int x, int y, int z, BlockStateProvider block, Mode mode) {
        blocks.put(new BlockPos(x, y, z), new Put(block, mode));
        track(x, z);
        trackY(y);
    }

    public void setIfAbsent(int x, int y, int z, BlockStateProvider block, Mode mode) {
        if (blocks.putIfAbsent(new BlockPos(x, y, z), new Put(block, mode)) == null) {
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
        return blocks.isEmpty();
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
