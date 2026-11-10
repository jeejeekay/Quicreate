package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/** A group of lumpy, part-buried boulders: each is one squashed ellipsoid with two smaller lumps on it. */
public class BoulderFeature extends ShapedFeature<BoulderConfiguration> {

    public BoulderFeature(Codec<BoulderConfiguration> codec) {
        super(codec);
    }

    @Override
    protected void build(BoulderConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int count = config.count().sample(random);
        for (int i = 0; i < count; i++) {
            double bx = 0;
            double bz = 0;
            if (i > 0) {
                double angle = random.nextDouble() * Mth.TWO_PI;
                double distance = config.spread() * (0.4 + 0.6 * random.nextDouble());
                bx = Math.cos(angle) * distance;
                bz = Math.sin(angle) * distance;
            }
            double radius = config.radius().sample(random);
            double ry = radius * config.squash();
            int g = ground.at((int) Math.round(bx), (int) Math.round(bz));
            double cy = g + 0.5 + ry * (1.0 - 2.0 * config.sink());
            ellipsoid(shape, bx, cy, bz, radius, ry, radius, config.blocks(), Shape.Mode.FORCE);
            for (int lump = 0; lump < 2; lump++) {
                double angle = random.nextDouble() * Mth.TWO_PI;
                double lx = bx + Math.cos(angle) * radius * 0.5;
                double lz = bz + Math.sin(angle) * radius * 0.5;
                double lr = radius * (0.5 + 0.2 * random.nextDouble());
                ellipsoid(shape, lx, cy + ry * 0.15, lz, lr, lr * config.squash(), lr, config.blocks(), Shape.Mode.FORCE);
            }
        }
    }
}
