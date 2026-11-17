package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * {@code quicreate:mounded}: generates another structure exactly as it normally would, then builds a mountain around it
 * so the structure sits inside it. The mountain covers the roof, fills under any overhang down to the ground, slopes
 * away on every side, and leaves a tunnel in front of the entrance.
 * <ul>
 *   <li>{@code structure}: the original definition, inline, so its id, tags and advancements keep working.</li>
 *   <li>{@code block}: what the mountain is made of.</li>
 *   <li>{@code cover}: blocks of mountain over the highest roof.</li>
 *   <li>{@code slope}: how many blocks the mountain drops per block outward (1 = 45°).</li>
 *   <li>{@code margin}: how far out from the structure the mountain may reach.</li>
 *   <li>{@code entrance} (optional): a box in one template's own coordinates and the way it faces; a tunnel that size
 *       is kept open from it to the edge of the mountain.</li>
 * </ul>
 */
public class MoundedStructure extends Structure {

    public record Entrance(ResourceLocation template, BlockPos from, BlockPos to, Direction facing) {
        public static final Codec<Entrance> CODEC = RecordCodecBuilder.create(i -> i.group(
                ResourceLocation.CODEC.fieldOf("template").forGetter(Entrance::template),
                BlockPos.CODEC.fieldOf("from").forGetter(Entrance::from),
                BlockPos.CODEC.fieldOf("to").forGetter(Entrance::to),
                Direction.CODEC.fieldOf("facing").forGetter(Entrance::facing)
        ).apply(i, Entrance::new));
    }

    public static final Codec<MoundedStructure> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            settingsCodec(instance),
            Structure.CODEC.fieldOf("structure").forGetter(s -> s.inner),
            BlockState.CODEC.fieldOf("block").forGetter(s -> s.block),
            Codec.intRange(0, 16).optionalFieldOf("cover", 3).forGetter(s -> s.cover),
            Codec.floatRange(0.2F, 8.0F).optionalFieldOf("slope", 1.2F).forGetter(s -> s.slope),
            Codec.intRange(1, 64).optionalFieldOf("margin", 32).forGetter(s -> s.margin),
            Entrance.CODEC.optionalFieldOf("entrance").forGetter(s -> s.entrance)
    ).apply(instance, MoundedStructure::new));

    private final Holder<Structure> inner;
    private final BlockState block;
    private final int cover;
    private final float slope;
    private final int margin;
    private final Optional<Entrance> entrance;

    public MoundedStructure(StructureSettings settings, Holder<Structure> inner, BlockState block, int cover, float slope,
                            int margin, Optional<Entrance> entrance) {
        super(settings);
        this.inner = inner;
        this.block = block;
        this.cover = cover;
        this.slope = slope;
        this.margin = margin;
        this.entrance = entrance;
    }

    @Override
    public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        return inner.value().findValidGenerationPoint(context).map(stub -> new GenerationStub(stub.position(), builder -> {
            StructurePiecesBuilder original = stub.getPiecesBuilder();
            if (original.isEmpty()) {
                return;
            }
            List<StructurePiece> pieces = original.build().pieces();
            List<BoundingBox> boxes = new ArrayList<>();
            BoundingBox tunnel = null;
            Direction facing = null;
            for (StructurePiece piece : pieces) {
                boxes.add(piece.getBoundingBox());
                if (tunnel == null && entrance.isPresent() && piece instanceof PoolElementStructurePiece pool
                        && pool.getElement().toString().contains(entrance.get().template().toString())) {
                    Entrance e = entrance.get();
                    BlockPos a = StructureTemplate.transform(e.from(), Mirror.NONE, pool.getRotation(), BlockPos.ZERO).offset(pool.getPosition());
                    BlockPos b = StructureTemplate.transform(e.to(), Mirror.NONE, pool.getRotation(), BlockPos.ZERO).offset(pool.getPosition());
                    tunnel = BoundingBox.fromCorners(a, b);
                    facing = pool.getRotation().rotate(e.facing());
                }
            }
            long seed = stub.position().asLong() * 31L + context.seed();
            builder.addPiece(new MoundPiece(boxes, tunnel, facing, block, cover, slope, margin, seed));
            for (StructurePiece piece : pieces) {
                builder.addPiece(piece);
            }
        }));
    }

    @Override
    public StructureType<?> type() {
        return QuicreateWorldgen.MOUNDED.get();
    }
}
