package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.StringRepresentable;
import net.minecraft.util.valueproviders.ConstantFloat;
import net.minecraft.util.valueproviders.FloatProvider;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.Optional;

/**
 * Settings for {@link GiantMushroomFeature}.
 *
 * @param stemHeight      stem height from the ground to the cap
 * @param stemRadius      stem radius (the base flares a little wider)
 * @param bend            how far the top of the stem leans sideways
 * @param capRadius       cap radius
 * @param capHeight       dome: how tall the dome is; flat: twice the cap thickness
 * @param capShape        dome (tall rounded cap with a drooping lip) or flat (a wide plate)
 * @param stem            stem blocks
 * @param cap             cap blocks
 * @param underside       optional blocks hung under the cap (glowing gills)
 * @param undersideChance chance for each spot under the cap to get an underside block
 * @param sink            how many blocks the stem goes into the ground
 */
public record GiantMushroomConfiguration(IntProvider stemHeight, FloatProvider stemRadius, FloatProvider bend, FloatProvider capRadius,
                                         FloatProvider capHeight, CapShape capShape, BlockStateProvider stem, BlockStateProvider cap,
                                         Optional<BlockStateProvider> underside, float undersideChance, int sink)
        implements FeatureConfiguration {

    public enum CapShape implements StringRepresentable {
        DOME("dome"),
        FLAT("flat");

        public static final Codec<CapShape> CODEC = StringRepresentable.fromEnum(CapShape::values);

        private final String name;

        CapShape(String name) {
            this.name = name;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    public static final Codec<GiantMushroomConfiguration> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            IntProvider.codec(2, 64).fieldOf("stem_height").forGetter(GiantMushroomConfiguration::stemHeight),
            FloatProvider.codec(0.5F, 6.0F).fieldOf("stem_radius").forGetter(GiantMushroomConfiguration::stemRadius),
            FloatProvider.codec(0.0F, 16.0F).optionalFieldOf("bend", ConstantFloat.of(0.0F)).forGetter(GiantMushroomConfiguration::bend),
            FloatProvider.codec(1.0F, 20.0F).fieldOf("cap_radius").forGetter(GiantMushroomConfiguration::capRadius),
            FloatProvider.codec(1.0F, 16.0F).optionalFieldOf("cap_height", ConstantFloat.of(3.0F)).forGetter(GiantMushroomConfiguration::capHeight),
            CapShape.CODEC.optionalFieldOf("cap_shape", CapShape.DOME).forGetter(GiantMushroomConfiguration::capShape),
            BlockStateProvider.CODEC.fieldOf("stem").forGetter(GiantMushroomConfiguration::stem),
            BlockStateProvider.CODEC.fieldOf("cap").forGetter(GiantMushroomConfiguration::cap),
            BlockStateProvider.CODEC.optionalFieldOf("underside").forGetter(GiantMushroomConfiguration::underside),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("underside_chance", 0.1F).forGetter(GiantMushroomConfiguration::undersideChance),
            Codec.intRange(0, 8).optionalFieldOf("sink", 2).forGetter(GiantMushroomConfiguration::sink)
    ).apply(instance, GiantMushroomConfiguration::new));
}
