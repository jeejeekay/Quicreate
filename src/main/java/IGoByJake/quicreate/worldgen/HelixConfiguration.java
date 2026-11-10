package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.List;

/**
 * Settings for {@link HelixFeature}. Height, radius and turns accept a plain number or a vanilla
 * value provider (e.g. {"type":"minecraft:uniform","value":{"min_inclusive":32,"max_inclusive":48}})
 * so each tower can vary.
 *
 * @param height          tower height in blocks
 * @param radius          distance from the centre line to each strand at the base
 * @param turns           full twists from bottom to top
 * @param strandThickness strand width in blocks
 * @param strands         number of strands, spaced evenly around the centre (2 = double helix)
 * @param taper           0 = straight, 0.9 = radius shrinks to 10% at the top
 * @param rungSpacing     a rung joins the strands every N blocks of height; 0 = no rungs
 * @param blocks          strand blocks
 * @param rungBlock       rung blocks
 * @param sink            how many blocks below the surface the base starts
 * @param inhabitants     mobs placed on the upper strands when the tower generates
 */
public record HelixConfiguration(IntProvider height, FloatProvider radius, FloatProvider turns, int strandThickness, int strands,
                                 float taper, int rungSpacing, BlockStateProvider blocks, BlockStateProvider rungBlock, int sink,
                                 List<HelixInhabitant> inhabitants)
        implements FeatureConfiguration {

    public static final Codec<HelixConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(1, 256).fieldOf("height").forGetter(HelixConfiguration::height),
            FloatProvider.codec(0.0F, 32.0F).fieldOf("radius").forGetter(HelixConfiguration::radius),
            FloatProvider.codec(0.0F, 32.0F).fieldOf("turns").forGetter(HelixConfiguration::turns),
            Codec.intRange(1, 8).optionalFieldOf("strand_thickness", 2).forGetter(HelixConfiguration::strandThickness),
            Codec.intRange(1, 8).optionalFieldOf("strands", 2).forGetter(HelixConfiguration::strands),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("taper", 0.0F).forGetter(HelixConfiguration::taper),
            Codec.intRange(0, 64).optionalFieldOf("rung_spacing", 0).forGetter(HelixConfiguration::rungSpacing),
            BlockStateProvider.CODEC.fieldOf("blocks").forGetter(HelixConfiguration::blocks),
            BlockStateProvider.CODEC.optionalFieldOf("rung_block", BlockStateProvider.simple(Blocks.SNOW_BLOCK)).forGetter(HelixConfiguration::rungBlock),
            Codec.intRange(0, 16).optionalFieldOf("sink", 2).forGetter(HelixConfiguration::sink),
            HelixInhabitant.CODEC.listOf().optionalFieldOf("inhabitants", List.of()).forGetter(HelixConfiguration::inhabitants)
    ).apply(instance, HelixConfiguration::new));
}
