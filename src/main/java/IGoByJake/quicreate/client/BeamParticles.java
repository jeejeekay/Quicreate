package IGoByJake.quicreate.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.particle.Particle;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/** Client-only: the master sword beam's trail, with lifetimes cut short so it doesn't hang in the air. */
public final class BeamParticles {

    private static final int PER_TICK = 6;      // spread along the distance flown this tick
    private static final int LIFE = 4;          // ticks; plus 0-1 random

    private BeamParticles() {
    }

    public static void trail(double x, double y, double z, Vec3 motion) {
        Minecraft mc = Minecraft.getInstance();
        RandomSource random = mc.level == null ? RandomSource.create() : mc.level.random;
        for (int i = 0; i < PER_TICK; i++) {
            double f = i / (double) PER_TICK;
            spawn(mc, ParticleTypes.END_ROD, x - motion.x * f, y - motion.y * f, z - motion.z * f, LIFE + random.nextInt(2));
        }
        spawn(mc, ParticleTypes.ELECTRIC_SPARK, x, y, z, 2);
    }

    private static void spawn(Minecraft mc, ParticleOptions type, double x, double y, double z, int life) {
        Particle p = mc.particleEngine.createParticle(type, x, y, z, 0, 0, 0);
        if (p != null) {
            p.setLifetime(life);
        }
    }
}
