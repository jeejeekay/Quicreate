package IGoByJake.quicreate.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.IntArrayTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.synth.SimplexNoise;

import java.util.ArrayList;
import java.util.List;

/**
 * The mountain of a {@link MoundedStructure}. It is the structure's first piece, so it is placed before the structure
 * in every chunk: it fills everything from the ground up to the mountain's surface, then the structure's own templates
 * place their blocks and air over it. Only the templates' structure-void cells (the outside of the building) keep the
 * mountain block. The tunnel is cleared (through any terrain too) from the entrance out to the edge.
 */
public class MoundPiece extends StructurePiece {

    private final List<BoundingBox> boxes;
    private final BoundingBox structure;
    private final BoundingBox tunnel;      // null: no entrance
    private final BlockState block;
    private final int cover;
    private final float slope;
    private final int margin;
    private final long seed;

    MoundPiece(List<BoundingBox> boxes, BoundingBox entrance, Direction facing, BlockState block, int cover, float slope, int margin, long seed) {
        super(QuicreateWorldgen.MOUND_PIECE.get(), 0, outer(boxes, margin, cover));
        this.boxes = boxes;
        this.structure = BoundingBox.encapsulatingBoxes(boxes).orElseThrow();
        this.tunnel = entrance == null || facing == null ? null : extend(entrance, facing, margin + 8);
        this.block = block;
        this.cover = cover;
        this.slope = slope;
        this.margin = margin;
        this.seed = seed;
    }

    public MoundPiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(QuicreateWorldgen.MOUND_PIECE.get(), tag);
        this.boxes = new ArrayList<>();
        for (Tag t : tag.getList("boxes", Tag.TAG_INT_ARRAY)) {
            boxes.add(box(((IntArrayTag) t).getAsIntArray()));
        }
        this.structure = BoundingBox.encapsulatingBoxes(boxes).orElse(getBoundingBox());
        this.tunnel = tag.contains("tunnel") ? box(tag.getIntArray("tunnel")) : null;
        this.block = NbtUtils.readBlockState(BuiltInRegistries.BLOCK.asLookup(), tag.getCompound("block"));
        this.cover = tag.getInt("cover");
        this.slope = tag.getFloat("slope");
        this.margin = tag.getInt("margin");
        this.seed = tag.getLong("seed");
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        ListTag list = new ListTag();
        for (BoundingBox b : boxes) {
            list.add(new IntArrayTag(ints(b)));
        }
        tag.put("boxes", list);
        if (tunnel != null) {
            tag.putIntArray("tunnel", ints(tunnel));
        }
        tag.put("block", NbtUtils.writeBlockState(block));
        tag.putInt("cover", cover);
        tag.putFloat("slope", slope);
        tag.putInt("margin", margin);
        tag.putLong("seed", seed);
    }

    private static BoundingBox outer(List<BoundingBox> boxes, int margin, int cover) {
        BoundingBox all = BoundingBox.encapsulatingBoxes(boxes).orElseThrow();
        return new BoundingBox(all.minX() - margin, all.minY() - 64, all.minZ() - margin,
                all.maxX() + margin, all.maxY() + cover + 4, all.maxZ() + margin);
    }

    /** The entrance box stretched outward in the way it faces. */
    private static BoundingBox extend(BoundingBox entrance, Direction facing, int length) {
        BoundingBox far = entrance.moved(facing.getStepX() * length, 0, facing.getStepZ() * length);
        return BoundingBox.encapsulatingBoxes(List.of(entrance, far)).orElse(entrance);
    }

    private static int[] ints(BoundingBox b) {
        return new int[]{b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ()};
    }

    private static BoundingBox box(int[] a) {
        return new BoundingBox(a[0], a[1], a[2], a[3], a[4], a[5]);
    }

    /** Horizontal distance to the nearest piece, 0 when over or under one. */
    private double distance(int x, int z) {
        double best = Double.MAX_VALUE;
        for (BoundingBox b : boxes) {
            int dx = Math.max(Math.max(b.minX() - x, 0), x - b.maxX());
            int dz = Math.max(Math.max(b.minZ() - z, 0), z - b.maxZ());
            best = Math.min(best, Math.sqrt(dx * dx + dz * dz));
        }
        return best;
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
                            BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
        RandomState randomState = level.getLevel().getChunkSource().randomState();
        SimplexNoise noise = new SimplexNoise(RandomSource.create(seed));
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int roof = structure.maxY();
        BoundingBox area = getBoundingBox();
        int minX = Math.max(chunkBox.minX(), area.minX()), maxX = Math.min(chunkBox.maxX(), area.maxX());
        int minZ = Math.max(chunkBox.minZ(), area.minZ()), maxZ = Math.min(chunkBox.maxZ(), area.maxZ());
        for (int x = minX; x <= maxX; x++) {
            for (int z = minZ; z <= maxZ; z++) {
                double d = distance(x, z);
                if (d > margin) {
                    continue;
                }
                double bumps = 2.5 * noise.getValue(x * 0.045, z * 0.045) + 1.2 * noise.getValue(x * 0.13 + 97, z * 0.13 + 41);
                int top = Mth.floor(roof + cover + bumps - slope * d);
                if (d == 0) {
                    top = Math.max(top, roof + 1);
                }
                int ground = generator.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level, randomState) - 1;
                boolean inTunnel = tunnel != null && x >= tunnel.minX() && x <= tunnel.maxX() && z >= tunnel.minZ() && z <= tunnel.maxZ();
                int low = Math.max(chunkBox.minY(), inTunnel ? Math.min(ground + 1, tunnel.minY()) : ground + 1);
                int high = Math.min(chunkBox.maxY(), Math.max(top, inTunnel ? tunnel.maxY() : top));
                for (int y = low; y <= high; y++) {
                    pos.set(x, y, z);
                    if (inTunnel && y >= tunnel.minY() && y <= tunnel.maxY()) {
                        level.setBlock(pos, air, 2);  // keep the way in open, through hills too
                    } else if (y <= top && y > ground) {
                        level.setBlock(pos, block, 2);
                    }
                }
            }
        }
    }
}
