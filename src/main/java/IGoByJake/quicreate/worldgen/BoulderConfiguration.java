package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

/**
 * Settings for {@link BoulderFeature}.
 *
 * @param radius boulder radius
 * @param squash height compared to width (0.5 = half as tall as wide)
 * @param sink   share of the boulder's height that is buried
 * @param count  boulders per group
 * @param spread how far extra boulders in a group sit from the first
 * @param blocks boulder blocks
 */
public record BoulderConfiguration(FloatProvider radius, float squash, float sink, IntProvider count, float spread, BlockStateProvider blocks)
        implements FeatureConfiguration {

    public static final Codec<BoulderConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            FloatProvider.codec(0.5F, 8.0F).fieldOf("radius").forGetter(BoulderConfiguration::radius),
            Codec.floatRange(0.2F, 2.0F).optionalFieldOf("squash", 0.75F).forGetter(BoulderConfiguration::squash),
            Codec.floatRange(0.0F, 0.9F).optionalFieldOf("sink", 0.3F).forGetter(BoulderConfiguration::sink),
            IntProvider.codec(1, 8).optionalFieldOf("count", ConstantInt.of(1)).forGetter(BoulderConfiguration::count),
            Codec.floatRange(0.0F, 16.0F).optionalFieldOf("spread", 3.0F).forGetter(BoulderConfiguration::spread),
            BlockStateProvider.CODEC.fieldOf("blocks").forGetter(BoulderConfiguration::blocks)
    ).apply(instance, BoulderConfiguration::new));
}
