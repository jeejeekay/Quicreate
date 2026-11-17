package IGoByJake.quicreate.pelican;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.AbstractFish;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.registries.ForgeRegistries;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * A pelican that keeps a player company. It almost never lands: it circles above the nearest player, and only
 * perches on a wide flat patch well away from everyone. Punching it just scares it off (arrows still hit).
 * Every so often it drops a gift near the player (loot table quicreate:gameplay/pelican/gift), or dives on a
 * fish in nearby water and drops the fish by you. PelicanSpawner keeps about one around each player and makes it
 * bring its first gift (9 string by default) within the first few minutes.
 *
 * <p>No pathfinding: it steers straight toward a target point each tick, which is cheap.
 */
public class Pelican extends Mob {
    public static final ResourceLocation GIFT = new ResourceLocation(Quicreate.MODID, "gameplay/pelican/gift");
    public static final ResourceLocation FIRST_GIFT = new ResourceLocation(Quicreate.MODID, "gameplay/pelican/first_gift");
    public static final ResourceLocation FISH = new ResourceLocation(Quicreate.MODID, "gameplay/pelican/fish");

    /** Synced pose: 0 flying, 1 perched, 2 diving. */
    private static final EntityDataAccessor<Integer> STATE = SynchedEntityData.defineId(Pelican.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<ItemStack> CARRY = SynchedEntityData.defineId(Pelican.class, EntityDataSerializers.ITEM_STACK);
    /** Ticks left with the bill open (drops and scoops). */
    private static final EntityDataAccessor<Integer> MOUTH = SynchedEntityData.defineId(Pelican.class, EntityDataSerializers.INT);

    /** Client-side bill opening, 0 shut to 1 wide, eased each tick. */
    private float mouth;
    private float mouthO;
    /** Server: ticks until the opened bill lets the parcel fall (-1 = not opening yet). */
    private int dropDelay = -1;

    private enum Task { CIRCLE, FLEE, DELIVER, DIVE_ABOVE, DIVE_DOWN, PERCH_FLY, PERCHED, LEAVE }

    private Task task = Task.CIRCLE;
    private int taskTicks;
    private double circleAngle;
    private double circleRadius = 10;
    private Vec3 target = Vec3.ZERO;
    @Nullable private UUID friend;
    @Nullable private Entity diveFish;
    private final List<ItemStack> parcel = new ArrayList<>();
    private boolean firstGift;
    private int giftCooldown;
    private int diveCooldown;
    private int perchCooldown;

    public Pelican(EntityType<? extends Mob> type, Level level) {
        super(type, level);
        this.setNoGravity(true);
        this.circleAngle = this.random.nextDouble() * Math.PI * 2;
        this.giftCooldown = 6000 + this.random.nextInt(12000);
        this.diveCooldown = 2400 + this.random.nextInt(6000);
        this.perchCooldown = 2400 + this.random.nextInt(4800);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 6.0D).add(Attributes.FLYING_SPEED, 0.6D);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(STATE, 0);
        this.entityData.define(CARRY, ItemStack.EMPTY);
        this.entityData.define(MOUTH, 0);
    }

    public boolean isPerched() { return this.entityData.get(STATE) == 1; }

    public boolean isDiving() { return this.entityData.get(STATE) == 2; }

    public ItemStack carried() { return this.entityData.get(CARRY); }

    /** Something is in the pouch (it bulges). */
    public boolean pouchFull() { return !carried().isEmpty(); }

    /** 0 = bill shut, 1 = wide open. */
    public float mouthOpen(float partial) { return Mth.lerp(partial, this.mouthO, this.mouth); }

    private void openMouth(int ticks) { this.entityData.set(MOUTH, Math.max(this.entityData.get(MOUTH), ticks)); }

    @Override
    public void tick() {
        super.tick();
        this.mouthO = this.mouth;
        float want = this.entityData.get(MOUTH) > 0 ? 1F : 0F;
        this.mouth += (want - this.mouth) * 0.25F;
        if (!this.level().isClientSide && this.entityData.get(MOUTH) > 0) this.entityData.set(MOUTH, this.entityData.get(MOUTH) - 1);
    }

    /** Bring these items to this player next. */
    public void queueGift(Player player, List<ItemStack> items, boolean first) {
        this.parcel.clear();
        this.parcel.addAll(items);
        this.friend = player.getUUID();
        this.firstGift = first;
        if (!items.isEmpty()) this.entityData.set(CARRY, items.get(0).copyWithCount(1));
        setTask(Task.DELIVER);
    }

    public boolean busyDelivering() {
        return !this.parcel.isEmpty();
    }

    private void setTask(Task t) {
        if (t != Task.DELIVER) this.dropDelay = -1;
        if (this.task == Task.PERCHED && t != Task.PERCHED) {
            this.setNoGravity(true);
            this.setDeltaMovement(this.getDeltaMovement().add(0, 0.35, 0));
        }
        this.task = t;
        this.taskTicks = 0;
        this.entityData.set(STATE, t == Task.PERCHED ? 1 : (t == Task.DIVE_DOWN ? 2 : 0));
    }

    @Nullable
    private Player friendPlayer() {
        if (this.friend != null) {
            Player p = this.level().getPlayerByUUID(this.friend);
            if (p != null && p.isAlive() && !p.isSpectator() && p.distanceToSqr(this) < 128 * 128) return p;
        }
        Player p = this.level().getNearestPlayer(this, 96);
        if (p != null && !p.isSpectator()) {
            this.friend = p.getUUID();
            return p;
        }
        return null;
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        this.taskTicks++;
        if (this.giftCooldown > 0) this.giftCooldown--;
        if (this.diveCooldown > 0) this.diveCooldown--;
        if (this.perchCooldown > 0) this.perchCooldown--;
        Player p = friendPlayer();
        if (p == null && this.task != Task.PERCHED && this.task != Task.LEAVE) setTask(Task.LEAVE);

        switch (this.task) {
            case CIRCLE -> circle(p);
            case FLEE -> {
                steer(this.target, 0.9);
                if (this.taskTicks > 70) setTask(this.parcel.isEmpty() ? Task.CIRCLE : Task.DELIVER);
            }
            case DELIVER -> deliver(p);
            case DIVE_ABOVE -> {
                if (this.diveFish != null && this.diveFish.isAlive()) this.target = this.diveFish.position();
                steer(this.target.add(0, 9, 0), 0.6);
                if (horizontalDistance(this.target) < 2.0 || this.taskTicks > 400) setTask(Task.DIVE_DOWN);
            }
            case DIVE_DOWN -> dive();
            case PERCH_FLY -> {
                steer(this.target.add(0, 0.05, 0), 0.45);
                if (this.position().distanceTo(this.target) < 0.6) {
                    this.setPos(this.target.x, this.target.y, this.target.z);
                    this.setDeltaMovement(Vec3.ZERO);
                    this.setNoGravity(false);
                    setTask(Task.PERCHED);
                } else if (this.taskTicks > 600 || (p != null && p.distanceToSqr(this.target) < 14 * 14)) {
                    setTask(Task.CIRCLE);
                }
            }
            case PERCHED -> {
                this.setDeltaMovement(this.getDeltaMovement().multiply(0, 1, 0));
                if ((p != null && p.distanceToSqr(this) < 9 * 9) || this.taskTicks > 600 + this.random.nextInt(1000) || !this.parcel.isEmpty()) {
                    this.perchCooldown = 3600 + this.random.nextInt(6000);
                    setTask(this.parcel.isEmpty() ? Task.CIRCLE : Task.DELIVER);
                }
            }
            case LEAVE -> {
                Vec3 v = this.getDeltaMovement().multiply(1, 0, 1);
                Vec3 dir = v.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : v.normalize();
                steer(this.position().add(dir.scale(8)).add(0, 2, 0), 0.7);
                if (this.taskTicks > 400) this.discard();
                if (p != null) setTask(Task.CIRCLE);
            }
        }
        if (this.task != Task.PERCHED) faceVelocity();
    }

    private void circle(@Nullable Player p) {
        if (p == null) return;
        if (!this.parcel.isEmpty()) { setTask(Task.DELIVER); return; }
        this.circleAngle += 0.025;
        if (this.random.nextInt(400) == 0) this.circleRadius = 8 + this.random.nextDouble() * 7;
        double h = 11 + Math.sin(this.tickCount * 0.01) * 3;
        Vec3 c = p.position().add(Math.cos(this.circleAngle) * this.circleRadius, h, Math.sin(this.circleAngle) * this.circleRadius);
        steer(c, 0.4);
        if (this.level() instanceof ServerLevel sl) {
            if (this.giftCooldown <= 0) {
                this.giftCooldown = 12000 + this.random.nextInt(12000);
                if (this.random.nextFloat() < 0.5F) queueGift(p, roll(sl, GIFT), false);
            } else if (this.diveCooldown <= 0) {
                this.diveCooldown = 3600 + this.random.nextInt(6000);
                startDive(sl, p);
            } else if (this.perchCooldown <= 0) {
                this.perchCooldown = 1200;
                findPerch(sl, p);
            }
        }
    }

    private void deliver(@Nullable Player p) {
        if (p == null || this.parcel.isEmpty()) {
            if (this.parcel.isEmpty()) setTask(Task.CIRCLE);
            return;
        }
        if (this.taskTicks == 1) this.target = dropPoint(p);
        Vec3 over = new Vec3(this.target.x, Math.max(this.target.y, p.getY()) + 5, this.target.z);
        steer(over, 0.6);
        if (this.dropDelay < 0 && (this.position().distanceTo(over) < 1.5 || this.taskTicks > 900)) {
            this.dropDelay = 10; // hover, open the bill, then let go
            openMouth(30);
        }
        if (this.dropDelay > 0 && --this.dropDelay == 0) {
            this.dropDelay = -1;
            // Out of the pouch, just in front of the body.
            float yaw = this.yBodyRot * ((float) Math.PI / 180F);
            double mx = this.getX() - Mth.sin(yaw) * 0.7, mz = this.getZ() + Mth.cos(yaw) * 0.7;
            for (ItemStack s : this.parcel) {
                ItemEntity e = new ItemEntity(this.level(), mx, this.getY() + 0.1, mz, s.copy());
                e.setDeltaMovement(0, -0.1, 0);
                this.level().addFreshEntity(e);
            }
            this.parcel.clear();
            this.entityData.set(CARRY, ItemStack.EMPTY);
            if (this.firstGift) PelicanSpawner.markFirstGiftDelivered(p);
            this.firstGift = false;
            setTask(Task.CIRCLE);
        }
    }

    /** A spot within 2 blocks of the player with ground under it, so gifts don't fall into the void. */
    private Vec3 dropPoint(Player p) {
        for (int i = 0; i < 12; i++) {
            double x = p.getX() + (this.random.nextDouble() - 0.5) * 4;
            double z = p.getZ() + (this.random.nextDouble() - 0.5) * 4;
            BlockPos top = this.level().getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, BlockPos.containing(x, 0, z));
            if (top.getY() > this.level().getMinBuildHeight() && Math.abs(top.getY() - p.getY()) < 6) return new Vec3(x, top.getY(), z);
        }
        return p.position();
    }

    private void startDive(ServerLevel level, Player p) {
        // Prefer a real fish near the surface; otherwise any open water near the player.
        List<AbstractFish> fish = level.getEntitiesOfClass(AbstractFish.class, p.getBoundingBox().inflate(20, 8, 20),
                f -> f.isInWater() && level.canSeeSky(f.blockPosition().above(2)));
        if (!fish.isEmpty()) {
            this.diveFish = fish.get(this.random.nextInt(fish.size()));
            this.target = this.diveFish.position();
            setTask(Task.DIVE_ABOVE);
            return;
        }
        for (int i = 0; i < 24; i++) {
            int x = Mth.floor(p.getX()) + this.random.nextInt(33) - 16;
            int z = Mth.floor(p.getZ()) + this.random.nextInt(33) - 16;
            BlockPos top = level.getHeightmapPos(Heightmap.Types.WORLD_SURFACE, new BlockPos(x, 0, z)).below();
            if (level.getFluidState(top).is(FluidTags.WATER) && level.getFluidState(top.below()).is(FluidTags.WATER)) {
                this.diveFish = null;
                this.target = Vec3.atBottomCenterOf(top).add(0, 1, 0);
                setTask(Task.DIVE_ABOVE);
                return;
            }
        }
    }

    private void dive() {
        Vec3 surface = this.diveFish != null && this.diveFish.isAlive()
                ? new Vec3(this.diveFish.getX(), Math.ceil(this.diveFish.getY()) + 0.2, this.diveFish.getZ()) : this.target;
        steer(surface, 1.1);
        boolean hit = this.position().distanceTo(surface) < 1.0 || this.isInWater();
        if (!hit && this.taskTicks < 160) return;
        if (hit && this.level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.SPLASH, this.getX(), this.getY(), this.getZ(), 30, 0.5, 0.1, 0.5, 0.15);
            openMouth(14); // scoop
            this.playSound(SoundEvents.GENERIC_SPLASH, 0.6F, 1.3F);
            List<ItemStack> catchItems = new ArrayList<>();
            if (this.diveFish != null && this.diveFish.isAlive()) {
                Item item = ForgeRegistries.ITEMS.getValue(ForgeRegistries.ENTITY_TYPES.getKey(this.diveFish.getType()));
                if (item != null && item != net.minecraft.world.item.Items.AIR) {
                    catchItems.add(new ItemStack(item));
                    this.diveFish.discard();
                }
            }
            if (catchItems.isEmpty()) catchItems.addAll(roll(sl, FISH));
            Player p = friendPlayer();
            this.diveFish = null;
            this.setDeltaMovement(0, 0.7, 0);
            if (p != null && !catchItems.isEmpty()) {
                queueGift(p, catchItems, false);
                return;
            }
        }
        this.diveFish = null;
        setTask(Task.CIRCLE);
    }

    /** A 3x3 flat, solid, open-sky patch at least 14 blocks from every player. */
    private void findPerch(ServerLevel level, Player p) {
        for (int i = 0; i < 16; i++) {
            int x = Mth.floor(this.getX()) + this.random.nextInt(49) - 24;
            int z = Mth.floor(this.getZ()) + this.random.nextInt(49) - 24;
            BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, new BlockPos(x, 0, z));
            if (top.getY() <= level.getMinBuildHeight() + 1) continue;
            if (level.getNearestPlayer(top.getX(), top.getY(), top.getZ(), 14, false) != null) continue;
            boolean flat = true;
            for (int dx = -1; dx <= 1 && flat; dx++) {
                for (int dz = -1; dz <= 1 && flat; dz++) {
                    BlockPos q = top.offset(dx, 0, dz);
                    flat = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, q).getY() == top.getY()
                            && level.getBlockState(q.below()).isFaceSturdy(level, q.below(), net.minecraft.core.Direction.UP)
                            && level.getFluidState(q.below()).isEmpty();
                }
            }
            if (flat) {
                this.target = Vec3.atBottomCenterOf(top);
                setTask(Task.PERCH_FLY);
                return;
            }
        }
    }

    private void steer(Vec3 to, double speed) {
        Vec3 d = to.subtract(this.position());
        double len = d.length();
        Vec3 want = len < 1.0E-3 ? Vec3.ZERO : d.scale(Math.min(speed, len * 0.25) / len);
        Vec3 v = this.getDeltaMovement();
        Vec3 nv = v.add(want.subtract(v).scale(0.1));
        if (this.horizontalCollision) nv = nv.add(0, 0.15, 0);
        this.setDeltaMovement(nv);
    }

    private double horizontalDistance(Vec3 to) {
        double dx = to.x - this.getX(), dz = to.z - this.getZ();
        return Math.sqrt(dx * dx + dz * dz);
    }

    private void faceVelocity() {
        Vec3 v = this.getDeltaMovement();
        if (v.horizontalDistanceSqr() > 1.0E-4) {
            float yaw = (float) (Mth.atan2(v.z, v.x) * (180F / Math.PI)) - 90F;
            this.setYRot(Mth.rotLerp(0.3F, this.getYRot(), yaw));
            this.yBodyRot = this.getYRot();
            this.yHeadRot = this.getYRot();
        }
        float pitch = (float) (-Mth.atan2(v.y, Math.sqrt(v.horizontalDistanceSqr())) * (180F / Math.PI));
        this.setXRot(Mth.clamp(Mth.lerp(0.2F, this.getXRot(), pitch * 0.6F), -40F, 70F));
    }

    private List<ItemStack> roll(ServerLevel level, ResourceLocation table) {
        LootParams params = new LootParams.Builder(level)
                .withParameter(LootContextParams.ORIGIN, this.position())
                .withParameter(LootContextParams.THIS_ENTITY, this)
                .create(LootContextParamSets.GIFT);
        return level.getServer().getLootData().getLootTable(table).getRandomItems(params);
    }

    // --- you can't punch a pelican: it just flies off. Arrows and other damage still work.
    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (!this.level().isClientSide && source.getEntity() instanceof Player player && !source.is(DamageTypeTags.IS_PROJECTILE)) {
            Vec3 away = this.position().subtract(player.position()).multiply(1, 0, 1);
            if (away.lengthSqr() < 1.0E-3) away = new Vec3(1, 0, 0);
            this.target = this.position().add(away.normalize().scale(14)).add(0, 8, 0);
            this.playSound(SoundEvents.PARROT_HURT, 1.0F, 0.45F);
            this.setDeltaMovement(this.getDeltaMovement().add(away.normalize().scale(0.6)).add(0, 0.5, 0));
            setTask(Task.FLEE);
            return false;
        }
        return super.hurt(source, amount);
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    protected void checkFallDamage(double y, boolean onGround, net.minecraft.world.level.block.state.BlockState state, BlockPos pos) {}

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return this.parcel.isEmpty();
    }

    /** Pelicans are quiet: no idle calls, just a low grunt when hurt. */
    @Nullable
    @Override
    protected SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    public float getVoicePitch() {
        return 0.45F + this.random.nextFloat() * 0.1F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PARROT_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PARROT_DEATH;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("GiftCooldown", this.giftCooldown);
        tag.putInt("DiveCooldown", this.diveCooldown);
        if (this.friend != null) tag.putUUID("Friend", this.friend);
        if (!this.parcel.isEmpty()) {
            net.minecraft.nbt.ListTag list = new net.minecraft.nbt.ListTag();
            for (ItemStack s : this.parcel) list.add(s.save(new CompoundTag()));
            tag.put("Parcel", list);
            tag.putBoolean("FirstGift", this.firstGift);
        }
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.giftCooldown = tag.getInt("GiftCooldown");
        this.diveCooldown = tag.getInt("DiveCooldown");
        if (tag.hasUUID("Friend")) this.friend = tag.getUUID("Friend");
        this.parcel.clear();
        net.minecraft.nbt.ListTag list = tag.getList("Parcel", 10);
        for (int i = 0; i < list.size(); i++) this.parcel.add(ItemStack.of(list.getCompound(i)));
        this.firstGift = tag.getBoolean("FirstGift");
        if (!this.parcel.isEmpty()) {
            this.entityData.set(CARRY, this.parcel.get(0).copyWithCount(1));
            setTask(Task.DELIVER);
        }
    }
}
