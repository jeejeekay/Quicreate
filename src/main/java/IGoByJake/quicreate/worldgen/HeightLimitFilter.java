package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.placement.PlacementContext;
import net.minecraft.world.level.levelgen.placement.PlacementFilter;
import net.minecraft.world.level.levelgen.placement.PlacementModifierType;

/**
 * {@code quicreate:height_limit}: a placement filter that keeps only positions between {@code min_y} and
 * {@code max_y} (both optional, inclusive). Used to keep the Moon's pit mushrooms out of surface buildings.
 */
public class HeightLimitFilter extends PlacementFilter {

    public static final Codec<HeightLimitFilter> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            Codec.INT.optionalFieldOf("min_y", Integer.MIN_VALUE).forGetter(filter -> filter.minY),
            Codec.INT.optionalFieldOf("max_y", Integer.MAX_VALUE).forGetter(filter -> filter.maxY)
    ).apply(instance, HeightLimitFilter::new));

    private final int minY;
    private final int maxY;

    public HeightLimitFilter(int minY, int maxY) {
        this.minY = minY;
        this.maxY = maxY;
    }

    @Override
    protected boolean shouldPlace(PlacementContext context, RandomSource random, BlockPos pos) {
        return pos.getY() >= minY && pos.getY() <= maxY;
    }

    @Override
    public PlacementModifierType<?> type() {
        return QuicreateWorldgen.HEIGHT_LIMIT.get();
    }
}
