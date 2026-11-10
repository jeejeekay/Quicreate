package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/**
 * Triangular prisms tilted in random directions and sunk into the ground (Mercury spikes), or an
 * upright ring of them (monolith rings). Extra spikes in a cluster that would push the cluster past
 * the worldgen size limit are dropped rather than cut off.
 */
public class PrismSpikeFeature extends ShapedFeature<PrismSpikeConfiguration> {

    public PrismSpikeFeature(Codec<PrismSpikeConfiguration> codec) {
        super(codec);
    }

    @Override
    protected void build(PrismSpikeConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int count = config.count().sample(random);
        double ringPhase = random.nextDouble() * Mth.TWO_PI;
        for (int i = 0; i < count; i++) {
            double bx;
            double bz;
            double azimuth;
            if (config.arrangement() == PrismSpikeConfiguration.Arrangement.RING) {
                double angle = ringPhase + i * Mth.TWO_PI / count;
                bx = Math.cos(angle) * config.spread();
                bz = Math.sin(angle) * config.spread();
                azimuth = angle;
            } else if (i == 0) {
                bx = 0;
                bz = 0;
                azimuth = random.nextDouble() * Mth.TWO_PI;
            } else {
                double angle = random.nextDouble() * Mth.TWO_PI;
                double distance = config.spread() * (0.5 + 0.5 * random.nextDouble());
                bx = Math.cos(angle) * distance;
                bz = Math.sin(angle) * distance;
                azimuth = angle + (random.nextDouble() - 0.5) * 1.2; // lean roughly away from the first spike
            }
            Shape spike = new Shape();
            spike(config, random, ground, spike, bx, bz, azimuth);
            if (i == 0 || shape.fitsWith(spike, MAX_SPAN)) {
                shape.addAll(spike);
            }
        }
    }

    private static void spike(PrismSpikeConfiguration config, RandomSource random, Ground ground, Shape shape, double bx, double bz, double azimuth) {
        int length = config.length().sample(random);
        double width = config.width().sample(random);
        double tilt = Math.toRadians(config.tilt().sample(random));
        double roll = random.nextDouble() * Mth.TWO_PI;
        double circumradius = width / Math.sqrt(3.0);

        // A long spike leaning far reaches past what worldgen can write; stand it up just enough to fit
        // rather than cutting it off, so the tallest spikes lean the least.
        double maxLean = MAX_SPAN - 2 * circumradius - 2;
        if (length * Math.sin(tilt) > maxLean) {
            tilt = Math.asin(Mth.clamp(maxLean / length, 0.0, 1.0));
        }

        // Axis direction.
        double dx = Math.sin(tilt) * Math.cos(azimuth);
        double dy = Math.cos(tilt);
        double dz = Math.sin(tilt) * Math.sin(azimuth);

        // Two directions across the axis, for the triangle.
        double ax = 0;
        double ay = 1;
        double az = 0;
        if (Math.abs(dy) > 0.99) {
            ax = 1;
            ay = 0;
        }
        double e1x = dy * az - dz * ay;
        double e1y = dz * ax - dx * az;
        double e1z = dx * ay - dy * ax;
        double e1len = Math.sqrt(e1x * e1x + e1y * e1y + e1z * e1z);
        e1x /= e1len;
        e1y /= e1len;
        e1z /= e1len;
        double e2x = dy * e1z - dz * e1y;
        double e2y = dz * e1x - dx * e1z;
        double e2z = dx * e1y - dy * e1x;

        // Base where the axis meets the ground, then pushed back along the axis by the sunk length.
        double sunk = config.sink() * length;
        double ox = bx - dx * sunk;
        double oy = ground.at((int) Math.round(bx), (int) Math.round(bz)) + 0.5 - dy * sunk;
        double oz = bz - dz * sunk;

        double reach = circumradius + 1;
        double tx = ox + dx * length;
        double ty = oy + dy * length;
        double tz = oz + dz * length;
        double[] normalCos = new double[3];
        double[] normalSin = new double[3];
        for (int j = 0; j < 3; j++) {
            normalCos[j] = Math.cos(roll + j * Mth.TWO_PI / 3);
            normalSin[j] = Math.sin(roll + j * Mth.TWO_PI / 3);
        }

        for (int x = (int) Math.floor(Math.min(ox, tx) - reach); x <= (int) Math.ceil(Math.max(ox, tx) + reach); x++) {
            for (int y = (int) Math.floor(Math.min(oy, ty) - reach); y <= (int) Math.ceil(Math.max(oy, ty) + reach); y++) {
                for (int z = (int) Math.floor(Math.min(oz, tz) - reach); z <= (int) Math.ceil(Math.max(oz, tz) + reach); z++) {
                    double vx = x - ox;
                    double vy = y - oy;
                    double vz = z - oz;
                    double along = vx * dx + vy * dy + vz * dz;
                    if (along < 0 || along > length) {
                        continue;
                    }
                    double radius = circumradius * (1.0 - config.taper() * along / length);
                    if (radius < 0.3) {
                        continue;
                    }
                    double u = vx * e1x + vy * e1y + vz * e1z;
                    double w = vx * e2x + vy * e2y + vz * e2z;
                    double inradius = radius * 0.5;
                    boolean inside = true;
                    for (int j = 0; j < 3 && inside; j++) {
                        inside = u * normalCos[j] + w * normalSin[j] <= inradius;
                    }
                    if (inside) {
                        shape.set(x, y, z, config.blocks(), Shape.Mode.FORCE);
                    }
                }
            }
        }
    }
}
