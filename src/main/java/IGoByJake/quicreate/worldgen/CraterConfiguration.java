package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.ConstantFloat;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.Optional;

/**
 * Settings for {@link CraterFeature}: a bowl dug into the ground with a raised rim.
 *
 * @param radius     bowl radius (the rim sits outside this)
 * @param depth      depth of the bowl's centre below the ground
 * @param rimHeight  how high the rim rises above the ground
 * @param rimWidth   rim width as a share of the radius
 * @param floorDepth how many blocks of floor material line the bowl
 * @param floor      bowl lining
 * @param rim        rim blocks
 * @param core       optional blocks scattered in the bottom of the bowl (ice shards on the Moon)
 * @param coreChance chance for each floor block near the centre to be a core block
 * @param coreRadius how far out from the centre core blocks can appear, as a share of the radius
 */
public record CraterConfiguration(FloatProvider radius, FloatProvider depth, FloatProvider rimHeight, float rimWidth, int floorDepth,
                                  BlockStateProvider floor, BlockStateProvider rim, Optional<BlockStateProvider> core,
                                  float coreChance, float coreRadius)
        implements FeatureConfiguration {

    public static final Codec<CraterConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            FloatProvider.codec(2.0F, 18.0F).fieldOf("radius").forGetter(CraterConfiguration::radius),
            FloatProvider.codec(1.0F, 24.0F).fieldOf("depth").forGetter(CraterConfiguration::depth),
            FloatProvider.codec(0.0F, 8.0F).optionalFieldOf("rim_height", ConstantFloat.of(2.0F)).forGetter(CraterConfiguration::rimHeight),
            Codec.floatRange(0.1F, 1.0F).optionalFieldOf("rim_width", 0.4F).forGetter(CraterConfiguration::rimWidth),
            Codec.intRange(1, 6).optionalFieldOf("floor_depth", 2).forGetter(CraterConfiguration::floorDepth),
            BlockStateProvider.CODEC.fieldOf("floor").forGetter(CraterConfiguration::floor),
            BlockStateProvider.CODEC.fieldOf("rim").forGetter(CraterConfiguration::rim),
            BlockStateProvider.CODEC.optionalFieldOf("core").forGetter(CraterConfiguration::core),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("core_chance", 0.2F).forGetter(CraterConfiguration::coreChance),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("core_radius", 0.4F).forGetter(CraterConfiguration::coreRadius)
    ).apply(instance, CraterConfiguration::new));
}
