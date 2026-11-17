package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.placement.PlacementContext;
import net.minecraft.world.level.levelgen.placement.PlacementFilter;
import net.minecraft.world.level.levelgen.placement.PlacementModifierType;
import net.minecraft.world.level.levelgen.structure.BoundingBox;

/**
 * {@code quicreate:avoid_structures}: drops a placement within {@code radius} blocks of a structure in the
 * {@code quicreate:avoided_by_shapes} tag, so other mods' features (Venus spires) don't grow inside them.
 */
public class AvoidStructuresFilter extends PlacementFilter {

    public static final Codec<AvoidStructuresFilter> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            Codec.intRange(0, 32).optionalFieldOf("radius", 6).forGetter(filter -> filter.radius)
    ).apply(instance, AvoidStructuresFilter::new));

    private final int radius;

    public AvoidStructuresFilter(int radius) {
        this.radius = radius;
    }

    @Override
    protected boolean shouldPlace(PlacementContext context, RandomSource random, BlockPos pos) {
        BoundingBox box = new BoundingBox(pos.getX() - radius, pos.getY() - radius, pos.getZ() - radius,
                pos.getX() + radius, pos.getY() + radius * 3, pos.getZ() + radius);
        return !ShapedFeature.touchesAvoided(context.getLevel(), box);
    }

    @Override
    public PlacementModifierType<?> type() {
        return QuicreateWorldgen.AVOID_STRUCTURES.get();
    }
}
