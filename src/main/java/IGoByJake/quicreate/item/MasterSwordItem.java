package IGoByJake.quicreate.item;

import IGoByJake.quicreate.entity.SwordBeamEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.phys.HitResult;

/**
 * Platinum master sword: a fully charged swing at full health also fires a sword beam (2 damage,
 * ignores and doesn't grant hit invulnerability). Works on swings into the air and on hits;
 * swings at blocks (mining) don't fire. Unbreakable.
 */
public class MasterSwordItem extends SwordItem {

    private static final String LAST_SWING = "quicreate:master_sword_last_swing";

    public MasterSwordItem(Tier tier, int damage, float speed, Properties properties) {
        super(tier, damage, speed, properties);
    }

    @Override
    public boolean isDamageable(ItemStack stack) {
        return false;
    }

    /**
     * Called on the server for every swing (the client reports air swings too). Vanilla only
     * tracks charge for real hits, so the charge is measured from this sword's previous swing.
     */
    @Override
    public boolean onEntitySwing(ItemStack stack, LivingEntity entity) {
        if (entity instanceof ServerPlayer player) {
            long now = player.level().getGameTime();
            CompoundTag data = player.getPersistentData();
            long last = data.contains(LAST_SWING) ? data.getLong(LAST_SWING) : Long.MIN_VALUE / 2;
            data.putLong(LAST_SWING, now);

            boolean fullyCharged = now - last >= player.getCurrentItemAttackStrengthDelay();
            boolean fullHealth = player.getHealth() >= player.getMaxHealth();
            boolean mining = player.pick(4.5D, 0.0F, false).getType() == HitResult.Type.BLOCK;
            if (fullyCharged && fullHealth && !mining) {
                SwordBeamEntity beam = new SwordBeamEntity(player.level(), player);
                beam.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 1.6F, 0.0F);
                player.level().addFreshEntity(beam);
                player.level().playSound(null, player.getX(), player.getY(), player.getZ(),
                        SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 0.9F, 1.6F);
            }
        }
        return false;
    }
}
