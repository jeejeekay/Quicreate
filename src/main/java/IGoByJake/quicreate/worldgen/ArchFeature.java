package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/**
 * A rock arch: a lumpy half-ellipse between two feet, thickest at the legs, with the legs carried
 * down into the ground so neither foot floats on uneven terrain.
 */
public class ArchFeature extends ShapedFeature<ArchConfiguration> {

    public ArchFeature(Codec<ArchConfiguration> codec) {
        super(codec);
    }

    @Override
    protected void build(ArchConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int span = config.span().sample(random);
        int height = config.height().sample(random);
        double thickness = config.thickness().sample(random);
        double azimuth = random.nextDouble() * Mth.TWO_PI;
        double ux = Math.cos(azimuth);
        double uz = Math.sin(azimuth);
        double half = span / 2.0;
        double phase1 = random.nextDouble() * Mth.TWO_PI;
        double phase2 = random.nextDouble() * Mth.TWO_PI;

        int footAx = (int) Math.round(-ux * half);
        int footAz = (int) Math.round(-uz * half);
        int footBx = (int) Math.round(ux * half);
        int footBz = (int) Math.round(uz * half);
        int groundA = ground.at(footAx, footAz);
        int groundB = ground.at(footBx, footBz);
        int base = Math.max(groundA, groundB);

        // Enough spheres along the curve to overlap smoothly; big arches use fewer per block.
        double arc = Math.PI * Math.sqrt((half * half + height * height) / 2.0);
        int steps = (int) Math.ceil(arc / Math.max(0.5, thickness * 0.35)) + 1;
        for (int i = 0; i <= steps; i++) {
            double theta = Math.PI * i / steps;
            double along = -half * Math.cos(theta);
            double y = base + height * Math.sin(theta);
            double legs = 1.0 - Math.sin(theta);
            double lumps = 1.0 + config.roughness() * (0.35 * Math.sin(5 * theta + phase1) + 0.2 * Math.sin(13 * theta + phase2));
            double radius = thickness * (1.0 + 0.6 * legs * legs) * lumps;
            ellipsoid(shape, ux * along, y, uz * along, radius, radius, radius, config.blocks(), Shape.Mode.FORCE);
        }

        double legRadius = thickness * 1.6;
        for (int y = groundA - config.sink(); y <= base; y++) {
            disk(shape, -ux * half, y, -uz * half, legRadius, config.blocks(), Shape.Mode.FORCE);
        }
        for (int y = groundB - config.sink(); y <= base; y++) {
            disk(shape, ux * half, y, uz * half, legRadius, config.blocks(), Shape.Mode.FORCE);
        }
    }
}
