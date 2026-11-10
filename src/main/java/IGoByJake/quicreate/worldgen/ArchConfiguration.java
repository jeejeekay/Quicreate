package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

/**
 * Settings for {@link ArchFeature}: a natural rock arch.
 *
 * @param span      distance between the two feet
 * @param height    height of the top of the arch above the higher foot
 * @param thickness radius of the arch at its top (the legs are thicker)
 * @param roughness 0 = smooth tube, 1 = very lumpy
 * @param sink      how far the legs go into the ground
 * @param blocks    arch blocks
 */
public record ArchConfiguration(IntProvider span, IntProvider height, FloatProvider thickness, float roughness, int sink,
                                BlockStateProvider blocks)
        implements FeatureConfiguration {

    public static final Codec<ArchConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(4, 96).fieldOf("span").forGetter(ArchConfiguration::span),
            IntProvider.codec(3, 96).fieldOf("height").forGetter(ArchConfiguration::height),
            FloatProvider.codec(0.5F, 16.0F).fieldOf("thickness").forGetter(ArchConfiguration::thickness),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("roughness", 0.25F).forGetter(ArchConfiguration::roughness),
            Codec.intRange(0, 16).optionalFieldOf("sink", 3).forGetter(ArchConfiguration::sink),
            BlockStateProvider.CODEC.fieldOf("blocks").forGetter(ArchConfiguration::blocks)
    ).apply(instance, ArchConfiguration::new));
}
