package IGoByJake.quicreate.entity;

import IGoByJake.quicreate.QuicreateContent;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.ForgeEventFactory;

/** The master sword's beam: no model, just a particle trail. 2 damage that ignores and grants no hit invulnerability. */
public class SwordBeamEntity extends Projectile {

    private static final int LIFETIME = 16;
    private static final float DAMAGE = 2.0F;

    public SwordBeamEntity(EntityType<? extends SwordBeamEntity> type, Level level) {
        super(type, level);
        this.setNoGravity(true);
    }

    public SwordBeamEntity(Level level, LivingEntity owner) {
        this(QuicreateContent.SWORD_BEAM.get(), level);
        this.setOwner(owner);
        this.setPos(owner.getX(), owner.getEyeY() - 0.2D, owner.getZ());
    }

    @Override
    protected void defineSynchedData() {
    }

    @Override
    public void tick() {
        super.tick();
        if (this.tickCount > LIFETIME) {
            this.discard();
            return;
        }
        HitResult hit = ProjectileUtil.getHitResultOnMoveVector(this, this::canHitEntity);
        if (hit.getType() != HitResult.Type.MISS && !ForgeEventFactory.onProjectileImpact(this, hit)) {
            this.onHit(hit);
        }
        Vec3 motion = this.getDeltaMovement();
        if (this.level().isClientSide) {
            for (int i = 0; i < 3; i++) {
                double f = i / 3.0D;
                this.level().addParticle(ParticleTypes.END_ROD, this.getX() - motion.x * f, this.getY() - motion.y * f, this.getZ() - motion.z * f, 0, 0, 0);
            }
            if (this.tickCount % 2 == 0) {
                this.level().addParticle(ParticleTypes.ELECTRIC_SPARK, this.getX(), this.getY(), this.getZ(), 0, 0, 0);
            }
        }
        this.setPos(this.getX() + motion.x, this.getY() + motion.y, this.getZ() + motion.z);
        ProjectileUtil.rotateTowardsMovement(this, 1.0F);
    }

    @Override
    protected void onHitEntity(EntityHitResult result) {
        if (this.level().isClientSide) {
            return;
        }
        Entity target = result.getEntity();
        Entity owner = this.getOwner();
        // Ignore the target's current invulnerability, and give it none afterwards.
        int invulnerable = target.invulnerableTime;
        target.invulnerableTime = 0;
        target.hurt(this.damageSources().mobProjectile(this, owner instanceof LivingEntity living ? living : null), DAMAGE);
        target.invulnerableTime = invulnerable;
        this.discard();
    }

    @Override
    protected void onHitBlock(BlockHitResult result) {
        super.onHitBlock(result);
        if (!this.level().isClientSide) {
            this.discard();
        }
    }
}
