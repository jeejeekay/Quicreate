package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/**
 * A giant mushroom: a round stem that can bend toward the top, with a dome or flat cap. The stem is
 * sunk into the ground; the cap only fills open space.
 */
public class GiantMushroomFeature extends ShapedFeature<GiantMushroomConfiguration> {

    public GiantMushroomFeature(Codec<GiantMushroomConfiguration> codec) {
        super(codec);
    }

    @Override
    protected void build(GiantMushroomConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int height = config.stemHeight().sample(random);
        double stemRadius = config.stemRadius().sample(random);
        double bend = config.bend().sample(random);
        double capRadius = config.capRadius().sample(random);
        double capHeight = config.capHeight().sample(random);
        double azimuth = random.nextDouble() * Mth.TWO_PI;
        boolean dome = config.capShape() == GiantMushroomConfiguration.CapShape.DOME;

        int base = ground.at(0, 0) + 1;
        double topX = Math.cos(azimuth) * bend;
        double topZ = Math.sin(azimuth) * bend;

        // Stem; for a dome it carries on up inside the cap until it meets the roof.
        int stemTop = height + (dome ? Math.max(0, (int) Math.floor(capHeight - 1.6)) : 0);
        for (int y = -config.sink(); y <= stemTop; y++) {
            double t = Mth.clamp(y / (double) height, 0.0, 1.0);
            double radius = stemRadius * (1.0 + 0.4 * Math.pow(1.0 - t, 3));
            disk(shape, topX * t * t, base + y, topZ * t * t, radius, config.stem(), y < 0 ? Shape.Mode.FORCE : Shape.Mode.BUILD);
        }

        // Cap.
        int capBase = base + height;
        int reach = (int) Math.ceil(capRadius) + 1;
        int cx = (int) Math.round(topX);
        int cz = (int) Math.round(topZ);
        for (int x = cx - reach; x <= cx + reach; x++) {
            for (int z = cz - reach; z <= cz + reach; z++) {
                double r = Math.sqrt((x - topX) * (x - topX) + (z - topZ) * (z - topZ)) / capRadius;
                if (r > 1.0) {
                    continue;
                }
                double top;
                double bottom;
                if (dome) {
                    top = capHeight * Math.sqrt(1.0 - r * r);
                    bottom = top - 1.6;
                    if (r > 0.7) {
                        bottom = Math.min(bottom, -(r - 0.7) / 0.3 * Math.min(3.0, capHeight * 0.6)); // drooping lip
                    }
                } else {
                    double droop = r > 0.65 ? (r - 0.65) / 0.35 * 1.5 : 0.0;
                    top = 1.0 - droop;
                    bottom = top - Math.max(1.0, capHeight * 0.5);
                }
                int low = (int) Math.ceil(bottom);
                int high = (int) Math.floor(top);
                if (low > high) {
                    low = high = (int) Math.round(top);
                }
                for (int y = low; y <= high; y++) {
                    shape.set(x, capBase + y, z, config.cap(), Shape.Mode.BUILD);
                }
                if (config.underside().isPresent() && r > 0.3 && r < 0.9 && random.nextFloat() < config.undersideChance()
                        && !shape.has(x, capBase + low - 1, z)) {
                    shape.set(x, capBase + low - 1, z, config.underside().get(), Shape.Mode.BUILD);
                }
            }
        }
    }
}
