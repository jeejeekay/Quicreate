package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

/**
 * Settings for {@link FissureFeature}: a winding crack in the ground with lava at the bottom.
 *
 * @param length        crack length
 * @param width         width at the widest point (the ends narrow to a point)
 * @param depth         drop from the ground to the lava surface
 * @param lavaDepth     how deep the lava is in the widest part
 * @param wander        0 = straight, 1 = very winding
 * @param bridgeChance  chance per block of length for a thin rock bridge across the crack
 * @param liningChance  chance for each wall block to be swapped for lining (the lava is always sealed in)
 * @param lava          the liquid at the bottom
 * @param lining        wall, floor and bridge blocks
 */
public record FissureConfiguration(IntProvider length, FloatProvider width, IntProvider depth, IntProvider lavaDepth, float wander,
                                   float bridgeChance, float liningChance, BlockStateProvider lava, BlockStateProvider lining)
        implements FeatureConfiguration {

    public static final Codec<FissureConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(4, 44).fieldOf("length").forGetter(FissureConfiguration::length),
            FloatProvider.codec(1.0F, 12.0F).fieldOf("width").forGetter(FissureConfiguration::width),
            IntProvider.codec(1, 48).fieldOf("depth").forGetter(FissureConfiguration::depth),
            IntProvider.codec(1, 16).optionalFieldOf("lava_depth", ConstantInt.of(3)).forGetter(FissureConfiguration::lavaDepth),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("wander", 0.35F).forGetter(FissureConfiguration::wander),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("bridge_chance", 0.05F).forGetter(FissureConfiguration::bridgeChance),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("lining_chance", 0.6F).forGetter(FissureConfiguration::liningChance),
            BlockStateProvider.CODEC.optionalFieldOf("lava", BlockStateProvider.simple(Blocks.LAVA)).forGetter(FissureConfiguration::lava),
            BlockStateProvider.CODEC.optionalFieldOf("lining", BlockStateProvider.simple(Blocks.BLACKSTONE)).forGetter(FissureConfiguration::lining)
    ).apply(instance, FissureConfiguration::new));
}
