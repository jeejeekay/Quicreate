package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.util.Mth;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;

import java.util.Optional;

/**
 * {@code quicreate:repositioned}: generates another structure exactly as it normally would, then
 * moves it up or down so its bottom sits at a chosen height. For structures whose own code ignores
 * {@code start_height} (Cataclysm's burning arena, ruined citadel and sunken city).
 * <p>
 * Give {@code bottom_y} for a fixed height, or {@code bottom_above_surface} to sit relative to the
 * ground at the structure's centre (negative = buried). Override the original structure's file
 * with this type and put the original definition inline under {@code structure}, so its id, locator
 * eyes and tags all keep working.
 */
public class RepositionedStructure extends Structure {

    public static final Codec<RepositionedStructure> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            settingsCodec(instance),
            Structure.CODEC.fieldOf("structure").forGetter(structure -> structure.inner),
            IntProvider.CODEC.optionalFieldOf("bottom_y").forGetter(structure -> structure.bottomY),
            IntProvider.CODEC.optionalFieldOf("bottom_above_surface").forGetter(structure -> structure.bottomAboveSurface)
    ).apply(instance, RepositionedStructure::new));

    private final Holder<Structure> inner;
    private final Optional<IntProvider> bottomY;
    private final Optional<IntProvider> bottomAboveSurface;

    public RepositionedStructure(StructureSettings settings, Holder<Structure> inner, Optional<IntProvider> bottomY, Optional<IntProvider> bottomAboveSurface) {
        super(settings);
        this.inner = inner;
        this.bottomY = bottomY;
        this.bottomAboveSurface = bottomAboveSurface;
    }

    @Override
    public Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        return inner.value().findValidGenerationPoint(context).map(stub -> new GenerationStub(stub.position(), builder -> {
            StructurePiecesBuilder original = stub.getPiecesBuilder();
            if (original.isEmpty()) {
                return;
            }
            BoundingBox box = original.getBoundingBox();
            int target;
            if (bottomY.isPresent()) {
                target = bottomY.get().sample(context.random());
            } else if (bottomAboveSurface.isPresent()) {
                BlockPos at = stub.position();
                int surface = context.chunkGenerator().getBaseHeight(at.getX(), at.getZ(), Heightmap.Types.WORLD_SURFACE_WG,
                        context.heightAccessor(), context.randomState());
                target = surface + bottomAboveSurface.get().sample(context.random());
            } else {
                target = box.minY();
            }
            // Keep the whole structure inside the world.
            int lowest = context.heightAccessor().getMinBuildHeight() + 1;
            int highest = context.heightAccessor().getMaxBuildHeight() - 1 - box.getYSpan();
            target = Mth.clamp(target, lowest, Math.max(lowest, highest));
            original.offsetPiecesVertically(target - box.minY());
            for (StructurePiece piece : original.build().pieces()) {
                builder.addPiece(piece);
            }
        }));
    }

    @Override
    public StructureType<?> type() {
        return QuicreateWorldgen.REPOSITIONED.get();
    }
}
