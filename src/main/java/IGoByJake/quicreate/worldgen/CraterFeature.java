package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

/**
 * An impact crater: a smooth bowl that blends into the surrounding ground at its edge, a raised rim
 * around it, optional core blocks scattered in the bottom and an optional meteorite in the middle.
 * Craters wider than a feature can write (radius over about 16) are placed as {@code quicreate:shape} structures.
 */
public class CraterFeature extends ShapedFeature<CraterConfiguration> {

    public CraterFeature(Codec<CraterConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean clipSafe() {
        return true;
    }

    @Override
    protected void build(CraterConfiguration config, RandomSource random, Ground ground, Shape shape) {
        double radius = config.radius().sample(random);
        double depth = config.depth().sample(random);
        double rimHeight = config.rimHeight().sample(random);
        double rimWidth = Math.max(1.5, radius * config.rimWidth());
        int centre = ground.at(0, 0);
        int reach = (int) Math.ceil(radius + rimWidth);

        for (int dx = -reach; dx <= reach; dx++) {
            for (int dz = -reach; dz <= reach; dz++) {
                if (config.core().isEmpty() && shape.skipColumn(dx, dz)) {
                    continue; // not in the chunk being built (core blocks use random numbers, so only without them)
                }
                double r = Math.sqrt(dx * dx + dz * dz);
                int g = ground.at(dx, dz);
                if (r < radius) {
                    double f = r / radius;
                    // Bowl around the centre's height, easing into the real ground at the edge.
                    double bowl = centre - depth * (1.0 - f * f) + (g - centre) * f * f * f * f;
                    int top = Math.min((int) Math.round(bowl), g);
                    for (int y = top + 1; y <= g + 1; y++) {
                        shape.set(dx, y, dz, Shape.AIR, Shape.Mode.FORCE);
                    }
                    for (int y = top - config.floorDepth() + 1; y <= top; y++) {
                        BlockStateProvider block = config.floor();
                        if (config.core().isPresent() && f < config.coreRadius() && random.nextFloat() < config.coreChance()) {
                            block = config.core().get();
                        }
                        shape.set(dx, y, dz, block, Shape.Mode.FORCE);
                    }
                } else if (r < radius + rimWidth) {
                    double bump = Math.sin(Math.PI * (r - radius) / rimWidth);
                    int height = (int) Math.round(rimHeight * bump);
                    shape.set(dx, g, dz, config.rim(), Shape.Mode.FOUNDATION); // never a ring floating over a dip
                    for (int y = g + 1; y <= g + height; y++) {
                        shape.set(dx, y, dz, config.rim(), Shape.Mode.BUILD);
                    }
                }
            }
        }
        if (config.meteorite().isPresent()) {
            // A lumpy rock sitting half in the bowl's deepest point.
            double r = config.meteoriteRadius().sample(random);
            double floor = centre - depth;
            ellipsoid(shape, 0.5, floor + r * 0.35, 0.5, r * 1.1, r * 0.85, r, config.meteorite().get(), Shape.Mode.FORCE);
            for (int i = 0; i < 3; i++) {
                double angle = random.nextDouble() * Math.PI * 2;
                double d = r * (0.5 + 0.4 * random.nextDouble());
                double s = r * (0.45 + 0.25 * random.nextDouble());
                ellipsoid(shape, Math.cos(angle) * d, floor + s * 0.5, Math.sin(angle) * d, s, s * 0.8, s, config.meteorite().get(), Shape.Mode.FORCE);
            }
        }
    }
}
