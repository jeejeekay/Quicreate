package IGoByJake.quicreate.entity;

import IGoByJake.quicreate.QuicreateContent;
import IGoByJake.quicreate.item.ObsidianFishingRodItem;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.stats.Stats;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FishingHook;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.player.ItemFishedEvent;

import java.util.List;

/**
 * The obsidian rod's bobber. It is a vanilla FishingHook (so the player's fishing slot, the line renderer and
 * other mods' fishing hooks all treat it normally) but with its own tick: it floats on lava instead of water, it
 * doesn't burn, and the bite timings are the same as a normal rod (100-600 ticks, minus Lure). It doesn't hook mobs.
 *
 * What it catches depends on where: in the Nether, the block most of the pool is built from picks the table
 * ({@code #quicreate:lava_lining/<name>} -> {@code quicreate:gameplay/lava_fishing/<name>}); anywhere else, or an
 * unlined pool, uses {@code quicreate:gameplay/lava_fishing}. Catches go straight to the player, since an item
 * thrown out of lava would burn.
 */
public class LavaFishingHook extends FishingHook {

    /** Linings checked in order; the one with the most blocks around the bobber wins. */
    private static final String[] LININGS = {"obsidian", "nether_bricks", "soul", "magma"};
    private static final int MIN_LINING = 6;

    private static final EntityDataAccessor<Boolean> BITING = SynchedEntityData.defineId(LavaFishingHook.class, EntityDataSerializers.BOOLEAN);

    private enum State { FLYING, BOBBING }

    private State state = State.FLYING;
    private int luck;
    private int lure;
    private int life;
    private int nibble;
    private int timeUntilLured;
    private int timeUntilHooked;
    private float fishAngle;

    public LavaFishingHook(EntityType<? extends FishingHook> type, Level level) {
        super(type, level);
    }

    public LavaFishingHook(Player player, Level level, int luck, int lure) {
        this(QuicreateContent.LAVA_FISHING_HOOK.get(), level);
        this.luck = Math.max(0, luck);
        this.lure = Math.max(0, lure);
        this.setOwner(player); // also sets player.fishing
        // Same throw as vanilla.
        float xr = player.getXRot();
        float yr = player.getYRot();
        float c = Mth.cos(-yr * ((float) Math.PI / 180F) - (float) Math.PI);
        float s = Mth.sin(-yr * ((float) Math.PI / 180F) - (float) Math.PI);
        float cx = -Mth.cos(-xr * ((float) Math.PI / 180F));
        float sx = Mth.sin(-xr * ((float) Math.PI / 180F));
        this.moveTo(player.getX() - s * 0.3D, player.getEyeY(), player.getZ() - c * 0.3D, yr, xr);
        Vec3 v = new Vec3(-s, Mth.clamp(-(sx / cx), -5.0F, 5.0F), -c);
        double len = v.length();
        v = v.multiply(0.6D / len + this.random.triangle(0.5D, 0.0103365D), 0.6D / len + this.random.triangle(0.5D, 0.0103365D),
                0.6D / len + this.random.triangle(0.5D, 0.0103365D));
        this.setDeltaMovement(v);
        this.setYRot((float) (Mth.atan2(v.x, v.z) * (180F / (float) Math.PI)));
        this.setXRot((float) (Mth.atan2(v.y, v.horizontalDistance()) * (180F / (float) Math.PI)));
        this.yRotO = this.getYRot();
        this.xRotO = this.getXRot();
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(BITING, false);
    }

    private boolean biting() {
        return this.entityData.get(BITING);
    }

    private boolean shouldStop(Player player) {
        boolean main = player.getMainHandItem().getItem() instanceof ObsidianFishingRodItem;
        boolean off = player.getOffhandItem().getItem() instanceof ObsidianFishingRodItem;
        if (!player.isRemoved() && player.isAlive() && (main || off) && this.distanceToSqr(player) <= 1024.0D) return false;
        this.discard();
        return true;
    }

    @Override
    public void tick() {
        this.baseTick();
        Player player = this.getPlayerOwner();
        if (player == null) {
            this.discard();
            return;
        }
        if (!this.level().isClientSide && shouldStop(player)) return;

        if (this.onGround()) {
            if (++this.life >= 1200) {
                this.discard();
                return;
            }
        } else {
            this.life = 0;
        }

        BlockPos pos = this.blockPosition();
        FluidState fluid = this.level().getFluidState(pos);
        float height = fluid.is(FluidTags.LAVA) ? fluid.getHeight(this.level(), pos) : 0.0F;
        boolean inLava = height > 0.0F;

        if (this.state == State.FLYING) {
            if (inLava) {
                this.setDeltaMovement(this.getDeltaMovement().multiply(0.3D, 0.2D, 0.3D));
                this.state = State.BOBBING;
                return;
            }
        } else {
            Vec3 v = this.getDeltaMovement();
            double d = this.getY() + v.y - pos.getY() - height;
            if (Math.abs(d) < 0.01D) d += Math.signum(d) * 0.1D;
            this.setDeltaMovement(v.x * 0.9D, v.y - d * this.random.nextFloat() * 0.2D, v.z * 0.9D);
            if (inLava) {
                if (biting()) this.setDeltaMovement(this.getDeltaMovement().add(0, -0.1D * this.random.nextFloat() * this.random.nextFloat(), 0));
                if (!this.level().isClientSide) catching(pos);
            }
        }

        if (!fluid.is(FluidTags.LAVA)) this.setDeltaMovement(this.getDeltaMovement().add(0, -0.03D, 0));
        this.move(MoverType.SELF, this.getDeltaMovement());
        this.updateRotation();
        if (this.state == State.FLYING && (this.onGround() || this.horizontalCollision)) this.setDeltaMovement(Vec3.ZERO);
        this.setDeltaMovement(this.getDeltaMovement().scale(0.92D));
        this.reapplyPosition();
    }

    /** Vanilla's bite timer, with lava particles. */
    private void catching(BlockPos pos) {
        ServerLevel level = (ServerLevel) this.level();
        if (this.nibble > 0) {
            if (--this.nibble <= 0) {
                this.timeUntilLured = 0;
                this.timeUntilHooked = 0;
                this.entityData.set(BITING, false);
            }
        } else if (this.timeUntilHooked > 0) {
            if (--this.timeUntilHooked > 0) {
                this.fishAngle += (float) this.random.triangle(0.0D, 9.188D);
                float a = this.fishAngle * ((float) Math.PI / 180F);
                double r = this.timeUntilHooked * 0.1F;
                double x = this.getX() + Mth.sin(a) * r;
                double z = this.getZ() + Mth.cos(a) * r;
                double y = pos.getY() + 1.0D;
                if (this.random.nextFloat() < 0.15F) level.sendParticles(ParticleTypes.SMOKE, x, y, z, 1, 0, 0, 0, 0.0D);
                if (this.random.nextFloat() < 0.05F) level.sendParticles(ParticleTypes.LAVA, x, y, z, 1, 0, 0, 0, 0.0D);
            } else {
                this.playSound(SoundEvents.LAVA_POP, 1.0F, 0.8F + this.random.nextFloat() * 0.4F);
                double y = this.getY() + 0.5D;
                level.sendParticles(ParticleTypes.LAVA, this.getX(), y, this.getZ(), 4, 0.1, 0, 0.1, 0.0D);
                level.sendParticles(ParticleTypes.FLAME, this.getX(), y, this.getZ(), 8, 0.2, 0, 0.2, 0.02D);
                this.nibble = Mth.nextInt(this.random, 20, 40);
                this.entityData.set(BITING, true);
            }
        } else if (this.timeUntilLured > 0) {
            if (--this.timeUntilLured <= 0) {
                this.fishAngle = Mth.nextFloat(this.random, 0.0F, 360.0F);
                this.timeUntilHooked = Mth.nextInt(this.random, 20, 80);
            } else if (this.random.nextFloat() < 0.02F) {
                level.sendParticles(ParticleTypes.SMOKE, this.getX(), this.getY() + 0.3, this.getZ(), 1, 0.2, 0, 0.2, 0.01D);
            }
        } else {
            this.timeUntilLured = Mth.nextInt(this.random, 100, 600) - this.lure * 20 * 5;
        }
    }

    @Override
    public int retrieve(ItemStack rod) {
        Player player = this.getPlayerOwner();
        if (this.level().isClientSide || player == null || shouldStop(player)) return 0;
        int damage = 0;
        if (this.nibble > 0) {
            ServerLevel level = (ServerLevel) this.level();
            LootParams params = new LootParams.Builder(level)
                    .withParameter(LootContextParams.ORIGIN, this.position())
                    .withParameter(LootContextParams.TOOL, rod)
                    .withParameter(LootContextParams.THIS_ENTITY, this)
                    .withLuck(this.luck + player.getLuck())
                    .create(LootContextParamSets.FISHING);
            LootTable table = level.getServer().getLootData().getLootTable(pickTable(level));
            List<ItemStack> loot = table.getRandomItems(params);
            ItemFishedEvent event = new ItemFishedEvent(loot, this.onGround() ? 2 : 1, this);
            MinecraftForge.EVENT_BUS.post(event);
            if (event.isCanceled()) {
                this.discard();
                return event.getRodDamage();
            }
            CriteriaTriggers.FISHING_ROD_HOOKED.trigger((ServerPlayer) player, rod, this, loot);
            for (ItemStack stack : loot) {
                if (stack.is(ItemTags.FISHES)) player.awardStat(Stats.FISH_CAUGHT, 1);
                if (!player.getInventory().add(stack)) {
                    ItemEntity drop = new ItemEntity(level, player.getX(), player.getY() + 0.5, player.getZ(), stack);
                    drop.setNoPickUpDelay();
                    level.addFreshEntity(drop);
                }
                level.addFreshEntity(new ExperienceOrb(level, player.getX(), player.getY() + 0.5D, player.getZ() + 0.5D, this.random.nextInt(6) + 1));
            }
            player.playSound(SoundEvents.ITEM_PICKUP, 0.3F, 1.0F);
            damage = 1;
        }
        if (this.onGround()) damage = 2;
        this.discard();
        return damage;
    }

    /** Nether pools built mostly from a lining block use that lining's table. */
    private ResourceLocation pickTable(ServerLevel level) {
        ResourceLocation base = new ResourceLocation("quicreate", "gameplay/lava_fishing");
        if (level.dimension() != Level.NETHER) return base;
        BlockPos c = this.blockPosition();
        int[] counts = new int[LININGS.length];
        for (BlockPos p : BlockPos.betweenClosed(c.offset(-2, -3, -2), c.offset(2, 0, 2))) {
            var state = level.getBlockState(p);
            for (int i = 0; i < LININGS.length; i++) {
                if (state.is(LINING_TAGS[i])) counts[i]++;
            }
        }
        int best = -1;
        for (int i = 0; i < LININGS.length; i++) {
            if (counts[i] >= MIN_LINING && (best < 0 || counts[i] > counts[best])) best = i;
        }
        return best < 0 ? new ResourceLocation("quicreate", "gameplay/lava_fishing/nether")
                : new ResourceLocation("quicreate", "gameplay/lava_fishing/" + LININGS[best]);
    }

    @SuppressWarnings("unchecked")
    private static final TagKey<Block>[] LINING_TAGS = new TagKey[LININGS.length];

    static {
        for (int i = 0; i < LININGS.length; i++) {
            LINING_TAGS[i] = net.minecraft.tags.BlockTags.create(new ResourceLocation("quicreate", "lava_lining/" + LININGS[i]));
        }
    }
}
