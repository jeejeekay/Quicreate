package IGoByJake.quicreate.dive;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

/**
 * Netherite space suit dive.
 * <ul>
 *   <li>Trigger (client, {@link DiveClient}): press sprint while moving in any direction except straight forward,
 *       on the ground, wearing all four Netherite space suit pieces, not slowed.</li>
 *   <li>Dive: a burst of speed that way plus a small hop, in the crawling pose for {@link #POSE_TICKS}.</li>
 *   <li>Invincible to mob and projectile hits for {@link #INVULNERABLE_TICKS}; the diver sees a grey haze.</li>
 *   <li>Costs 1 saturation, or 1 hunger point when saturation is empty (4 exhaustion, as vanilla counts it).</li>
 *   <li>{@link #COOLDOWN_TICKS} between dives. The {@link #STREAK}th dive within {@link #STREAK_WINDOW_TICKS} gives
 *       Slowness II for {@link #SLOW_TICKS}, and nobody can dive while slowed.</li>
 * </ul>
 * Only the dive itself, incoming attacks and a tick check that returns at once unless someone is mid-dive run code.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID)
public final class Dive {

    public static final int COOLDOWN_TICKS = 10;          // 0.5 s
    public static final int INVULNERABLE_TICKS = 10;      // 0.5 s
    public static final int POSE_TICKS = 10;
    public static final double SPEED = 1.0;              // about X*.75 blocks
    public static final double HOP = 0.5;
    public static final float EXHAUSTION = 4.0F;          // 1 saturation, else 1 hunger point
    public static final int STREAK = 3;
    public static final int STREAK_WINDOW_TICKS = 150;    // 7.5 s
    public static final int SLOW_TICKS = 60;              // 3 s
    public static final int SLOW_AMPLIFIER = 1;           // Slowness II

    private static final ResourceLocation[] SUIT = {
            new ResourceLocation("ad_astra", "netherite_space_helmet"),
            new ResourceLocation("ad_astra", "netherite_space_suit"),
            new ResourceLocation("ad_astra", "netherite_space_pants"),
            new ResourceLocation("ad_astra", "netherite_space_boots")};
    private static final EquipmentSlot[] SLOTS = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};

    /** Server side, by player. */
    private static final Map<UUID, Deque<Long>> RECENT = new HashMap<>();
    private static final Map<UUID, Long> INVULNERABLE_UNTIL = new HashMap<>();
    private static final Map<UUID, Long> POSE_UNTIL = new HashMap<>();

    private Dive() {
    }

    public static boolean wearsSuit(Player player) {
        for (int i = 0; i < SLOTS.length; i++) {
            Item item = player.getItemBySlot(SLOTS[i]).getItem();
            if (!SUIT[i].equals(ForgeRegistries.ITEMS.getKey(item))) {
                return false;
            }
        }
        return true;
    }

    /** Checks both sides make before a dive. The ground check is client only: the hop may already be under way
     *  when the server hears about it. */
    public static boolean canDive(Player player) {
        return !player.isPassenger() && !player.isSpectator() && !player.getAbilities().flying
                && !player.isInWater() && !player.isFallFlying() && !player.hasEffect(MobEffects.MOVEMENT_SLOWDOWN)
                && wearsSuit(player);
    }

    /** The client asked to dive (it has already moved itself). */
    static void serverDive(ServerPlayer player) {
        if (!canDive(player)) {
            return;
        }
        long now = player.level().getGameTime();
        Deque<Long> recent = RECENT.computeIfAbsent(player.getUUID(), u -> new ArrayDeque<>());
        if (!recent.isEmpty() && now - recent.peekLast() < COOLDOWN_TICKS) {
            return;
        }
        while (!recent.isEmpty() && now - recent.peekFirst() >= STREAK_WINDOW_TICKS) {
            recent.pollFirst();
        }
        recent.addLast(now);
        player.causeFoodExhaustion(EXHAUSTION);
        INVULNERABLE_UNTIL.put(player.getUUID(), now + INVULNERABLE_TICKS);
        POSE_UNTIL.put(player.getUUID(), now + POSE_TICKS);
        player.setForcedPose(Pose.SWIMMING);
        if (recent.size() >= STREAK) {
            recent.clear();
            player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, SLOW_TICKS, SLOW_AMPLIFIER));
        }
    }

    @SubscribeEvent
    public static void onAttacked(LivingAttackEvent event) {
        if (INVULNERABLE_UNTIL.isEmpty() || !(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        Long until = INVULNERABLE_UNTIL.get(player.getUUID());
        if (until == null || player.level().getGameTime() > until) {
            return;
        }
        DamageSource source = event.getSource();
        if (source.getDirectEntity() instanceof Projectile || source.getEntity() instanceof LivingEntity) {
            event.setCanceled(true);
        }
    }

    /** Ends the dive pose. Returns at once when nobody is diving. */
    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || POSE_UNTIL.isEmpty()) {
            return;
        }
        long now = event.getServer().overworld().getGameTime();
        for (Iterator<Map.Entry<UUID, Long>> it = POSE_UNTIL.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<UUID, Long> e = it.next();
            if (now >= e.getValue()) {
                ServerPlayer player = event.getServer().getPlayerList().getPlayer(e.getKey());
                if (player != null) {
                    player.setForcedPose(null);
                }
                it.remove();
            }
        }
        INVULNERABLE_UNTIL.values().removeIf(until -> now > until);
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        UUID id = event.getEntity().getUUID();
        RECENT.remove(id);
        INVULNERABLE_UNTIL.remove(id);
        if (POSE_UNTIL.remove(id) != null) {
            event.getEntity().setForcedPose(null);
        }
    }
}
