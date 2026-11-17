package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.Optional;

/**
 * Settings for {@link WedgeFeature}: slabs of ground pushed up at an angle, as if by an earthquake.
 *
 * @param length    how far the slab reaches out from the crack it rises from
 * @param width     width at the crack (it narrows towards the tip by {@code taper})
 * @param thickness thickness of the slab; the overhang starts where the underside leaves the ground
 * @param rise      angle of the slab in degrees (0 = flat, 45 = steep)
 * @param taper     how much narrower the tip is than the base (0 = not at all, 0.9 = nearly a point)
 * @param sweep     how far the slab curves sideways as it reaches out, as a share of its length
 * @param ridge     0 = flat-topped slab, 1 = triangular cross-section (a peaked ridge down the middle)
 * @param lip       how far the top overhangs the underside at the tip, as a share of the thickness
 * @param roughness 0 = smooth, 1 = very uneven top and edges
 * @param riftDepth depth of the open crack along the back of the slab (0 = none)
 * @param chasm     depth of the sloped chasm under the slab, as a share of how high the slab has risen there (0 = none, 1 = mirror image)
 * @param count     slabs side by side, staggered like a fault line
 * @param blocks    slab blocks
 * @param top       optional surface blocks on the top of the slab
 * @param topDepth  how many layers of those surface blocks
 */
public record WedgeConfiguration(IntProvider length, FloatProvider width, FloatProvider thickness, FloatProvider rise,
                                 float taper, float ridge, float sweep, float lip, float roughness, IntProvider riftDepth, float chasm, IntProvider count,
                                 BlockStateProvider blocks, Optional<BlockStateProvider> top, int topDepth)
        implements FeatureConfiguration {

    public static final Codec<WedgeConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(6, 128).fieldOf("length").forGetter(WedgeConfiguration::length),
            FloatProvider.codec(2.0F, 64.0F).fieldOf("width").forGetter(WedgeConfiguration::width),
            FloatProvider.codec(1.0F, 32.0F).fieldOf("thickness").forGetter(WedgeConfiguration::thickness),
            FloatProvider.codec(0.0F, 70.0F).fieldOf("rise").forGetter(WedgeConfiguration::rise),
            Codec.floatRange(0.0F, 0.95F).optionalFieldOf("taper", 0.5F).forGetter(WedgeConfiguration::taper),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("ridge", 0.0F).forGetter(WedgeConfiguration::ridge),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("sweep", 0.2F).forGetter(WedgeConfiguration::sweep),
            Codec.floatRange(0.0F, 3.0F).optionalFieldOf("lip", 0.8F).forGetter(WedgeConfiguration::lip),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("roughness", 0.3F).forGetter(WedgeConfiguration::roughness),
            IntProvider.codec(0, 32).optionalFieldOf("rift_depth", ConstantInt.of(0)).forGetter(WedgeConfiguration::riftDepth),
            Codec.floatRange(0.0F, 2.0F).optionalFieldOf("chasm", 0.0F).forGetter(WedgeConfiguration::chasm),
            IntProvider.codec(1, 6).optionalFieldOf("count", ConstantInt.of(1)).forGetter(WedgeConfiguration::count),
            BlockStateProvider.CODEC.fieldOf("blocks").forGetter(WedgeConfiguration::blocks),
            BlockStateProvider.CODEC.optionalFieldOf("top").forGetter(WedgeConfiguration::top),
            Codec.intRange(1, 16).optionalFieldOf("top_depth", 1).forGetter(WedgeConfiguration::topDepth)
    ).apply(instance, WedgeConfiguration::new));
}
