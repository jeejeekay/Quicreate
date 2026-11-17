package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/**
 * Earthquake slabs: wedges of ground broken free along a crack and pushed up at an angle. Each slab
 * starts buried at the crack and rises as it reaches out; once its underside leaves the ground it
 * hangs over open air, ending in a cliff whose top juts out past its base. Several slabs side by side
 * are staggered like a fault line, and an open crack can run along their backs.
 */
public class WedgeFeature extends ShapedFeature<WedgeConfiguration> {

    public WedgeFeature(Codec<WedgeConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean clipSafe() {
        return true;
    }

    @Override
    protected void build(WedgeConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int count = config.count().sample(random);
        double azimuth = random.nextDouble() * Mth.TWO_PI;
        double side = random.nextBoolean() ? 1 : -1;
        // Centre the row of slabs on the origin, so a wide fault line stays within the 8 chunks a
        // structure can reach (anything further out would be cut off).
        double offset = -(count - 1) * (config.width().getMinValue() + config.width().getMaxValue()) * 0.5 * 0.975 * 0.5;
        for (int i = 0; i < count; i++) {
            int length = config.length().sample(random);
            double width = config.width().sample(random);
            double heading = azimuth + (random.nextDouble() - 0.5) * 0.35;
            // Neighbours sit beside the first slab, a little forward or back, like broken pavement.
            double ax = Math.cos(azimuth), az = Math.sin(azimuth);
            double stagger = i == 0 ? 0 : (random.nextDouble() - 0.5) * length * 0.4;
            double bx = -az * offset * side + ax * stagger;
            double bz = ax * offset * side + az * stagger;
            offset += width * (0.85 + 0.25 * random.nextDouble());
            slab(config, random, ground, shape, bx, bz, heading, length, width, side);
        }
    }

    private static void slab(WedgeConfiguration config, RandomSource random, Ground ground, Shape shape,
                             double bx, double bz, double heading, int length, double width, double side) {
        double thickness = config.thickness().sample(random);
        double slope = Math.tan(Math.toRadians(config.rise().sample(random)));
        int rift = config.riftDepth().sample(random);
        double ux = Math.cos(heading), uz = Math.sin(heading);   // along the slab
        double vx = -uz, vz = ux;                                // across it
        double sweep = config.sweep() * length * side;
        double lip = config.lip() * thickness;
        double rough = config.roughness();
        double p1 = random.nextDouble() * Mth.TWO_PI, p2 = random.nextDouble() * Mth.TWO_PI, p3 = random.nextDouble() * Mth.TWO_PI;
        int base = ground.at((int) Math.round(bx), (int) Math.round(bz));

        double reach = length + Math.abs(sweep) + width + 4;
        // Only the columns that will be kept (one chunk, when a structure builds it chunk by chunk).
        int x0 = Math.max((int) Math.floor(bx - reach), shape.clipMinX()), x1 = Math.min((int) Math.ceil(bx + reach), shape.clipMaxX());
        int z0 = Math.max((int) Math.floor(bz - reach), shape.clipMinZ()), z1 = Math.min((int) Math.ceil(bz + reach), shape.clipMaxZ());
        for (int x = x0; x <= x1; x++) {
            for (int z = z0; z <= z1; z++) {
                double rx = x - bx, rz = z - bz;
                double a = rx * ux + rz * uz;
                if (a < -3 || a > length) {
                    continue;
                }
                double f = Math.max(0, a) / length;
                double centre = sweep * f * f;
                double c = rx * vx + rz * vz - centre;
                double half = width / 2 * (1 - config.taper() * f)
                        * (1 + rough * (0.18 * Math.sin(a * 0.31 + p1) + 0.1 * Math.sin(a * 0.83 + p2)));
                if (half < 0.6 || Math.abs(c) > half) {
                    continue;
                }
                int g = ground.at(x, z);
                if (a < 0) {
                    // The crack behind the slab.
                    for (int y = base - rift + 1; y <= g + 1 && rift > 0; y++) {
                        shape.set(x, y, z, Shape.AIR, Shape.Mode.FORCE);
                    }
                    continue;
                }
                double edge = Math.abs(c) / half;                  // 0 middle, 1 edge
                double ridge = config.ridge();
                double bump = rough * (1.2 * Math.sin(a * 0.45 + c * 0.6 + p3) + 0.6 * Math.sin(c * 1.3 + p1));
                double under = base + a * slope - thickness;       // underside along the middle
                // ridge 1: the top slopes straight down to the edges (a triangular cross-section);
                // ridge 0: a flat slab with rounded shoulders.
                double topY = under + thickness * (1 - ridge * edge) - (1 - ridge) * edge * edge * thickness * 0.35 + bump;
                double bottomY = under + (1 - ridge) * thickness * 0.3 * edge * edge;
                int top = (int) Math.round(topY);
                int bottom = (int) Math.floor(bottomY);
                if (top < g - 1 && a > 2) {
                    continue; // buried in rising ground: nothing would show
                }
                // Sloped chasm: the slab's shape mirrored into the ground below it, as if the slab was torn out of it.
                double chasmDepth = config.chasm() * a * slope * (1 - 0.5 * edge * edge);
                boolean overChasm = chasmDepth >= 1;
                if (overChasm) {
                    int floor = (int) Math.round(g - chasmDepth);
                    for (int y = floor + 1; y < Math.min(bottom, g + 2); y++) {
                        shape.set(x, y, z, Shape.AIR, Shape.Mode.FORCE);
                    }
                }
                // Where the underside is still in the ground, anchor it 2 blocks down; past that it hangs free.
                int from = bottom > g || overChasm ? bottom : Math.min(bottom, g - 2);
                for (int y = from; y <= top; y++) {
                    // The cliff at the tip leans out: the top reaches the full length, the underside stops short.
                    double depthIn = Mth.clamp((topY - y) / thickness, 0, 1);
                    if (a > length - lip * depthIn) {
                        continue;
                    }
                    boolean surface = y > top - config.topDepth() && config.top().isPresent();
                    shape.set(x, y, z, surface ? config.top().get() : config.blocks(), Shape.Mode.FORCE);
                }
            }
        }
    }
}
