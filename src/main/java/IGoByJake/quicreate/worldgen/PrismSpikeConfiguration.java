package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.StringRepresentable;
import net.minecraft.util.valueproviders.ConstantFloat;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

/**
 * Settings for {@link PrismSpikeFeature}: triangular prisms that lean out of the ground.
 *
 * @param length      spike length along its axis, including the part sunk into the ground
 * @param width       side length of the triangle at the base
 * @param taper       0 = straight prism, 1 = sharp point at the tip
 * @param tilt        lean away from vertical, in degrees
 * @param sink        share of the length that is buried (0.25 = a quarter underground)
 * @param count       spikes per cluster (or monoliths per ring)
 * @param spread      cluster: how far extra spikes sit from the first; ring: ring radius
 * @param arrangement cluster = spikes leaning in random directions; ring = evenly spaced around a circle, leaning outward
 * @param blocks      spike blocks
 */
public record PrismSpikeConfiguration(IntProvider length, FloatProvider width, float taper, FloatProvider tilt, float sink,
                                      IntProvider count, float spread, Arrangement arrangement, BlockStateProvider blocks)
        implements FeatureConfiguration {

    public enum Arrangement implements StringRepresentable {
        CLUSTER("cluster"),
        RING("ring");

        public static final Codec<Arrangement> CODEC = StringRepresentable.fromEnum(Arrangement::values);

        private final String name;

        Arrangement(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    public static final Codec<PrismSpikeConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(1, 128).fieldOf("length").forGetter(PrismSpikeConfiguration::length),
            FloatProvider.codec(1.0F, 24.0F).fieldOf("width").forGetter(PrismSpikeConfiguration::width),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("taper", 0.8F).forGetter(PrismSpikeConfiguration::taper),
            FloatProvider.codec(0.0F, 80.0F).optionalFieldOf("tilt", ConstantFloat.of(0.0F)).forGetter(PrismSpikeConfiguration::tilt),
            Codec.floatRange(0.0F, 0.9F).optionalFieldOf("sink", 0.25F).forGetter(PrismSpikeConfiguration::sink),
            IntProvider.codec(1, 12).optionalFieldOf("count", UniformInt.of(1, 3)).forGetter(PrismSpikeConfiguration::count),
            Codec.floatRange(0.0F, 24.0F).optionalFieldOf("spread", 8.0F).forGetter(PrismSpikeConfiguration::spread),
            Arrangement.CODEC.optionalFieldOf("arrangement", Arrangement.CLUSTER).forGetter(PrismSpikeConfiguration::arrangement),
            BlockStateProvider.CODEC.fieldOf("blocks").forGetter(PrismSpikeConfiguration::blocks)
    ).apply(instance, PrismSpikeConfiguration::new));
}
