package IGoByJake.quicreate.pelican;

import IGoByJake.quicreate.Quicreate;
import IGoByJake.quicreate.QuicreateContent;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.List;

/**
 * Keeps about one pelican near each player in the overworld (rarely two), and makes sure each player's
 * first gift (quicreate:gameplay/pelican/first_gift: 9 string, the island's first string) is on its way at a random moment in their first
 * few minutes. Runs once a second per player.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID)
public final class PelicanSpawner {
    private static final String KEY = "quicreate_pelican";
    /** Pack settings: where pelicans appear, how soon the first gift arrives, and how often a second pelican joins. */
    private static final java.util.Set<String> DIMENSIONS = java.util.Set.of("minecraft:overworld");
    private static final int FIRST_GIFT_SECONDS = 300;
    private static final float SECOND_PELICAN_CHANCE = 0.03F;

    private PelicanSpawner() {}

    private static CompoundTag data(Player p) {
        CompoundTag root = p.getPersistentData();
        if (!root.contains(Player.PERSISTED_NBT_TAG)) root.put(Player.PERSISTED_NBT_TAG, new CompoundTag());
        CompoundTag persisted = root.getCompound(Player.PERSISTED_NBT_TAG);
        if (!persisted.contains(KEY)) persisted.put(KEY, new CompoundTag());
        return persisted.getCompound(KEY);
    }

    public static void markFirstGiftDelivered(Player p) {
        data(p).putBoolean("Delivered", true);
    }

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || !(event.player instanceof ServerPlayer player) || player.tickCount % 20 != 0) return;
        if (player.isSpectator()) return;
        ServerLevel level = player.serverLevel();
        if (!DIMENSIONS.contains(level.dimension().location().toString())) return;

        CompoundTag d = data(player);
        int seconds = d.getInt("Seconds") + 1;
        d.putInt("Seconds", seconds);
        if (!d.contains("GiftAt")) d.putInt("GiftAt", 45 + player.getRandom().nextInt(Math.max(1, FIRST_GIFT_SECONDS - 150)));

        List<Pelican> near = level.getEntitiesOfClass(Pelican.class, player.getBoundingBox().inflate(96));
        boolean firstDue = !d.getBoolean("Delivered") && seconds >= d.getInt("GiftAt");

        if (near.isEmpty() && (seconds >= 30 || firstDue) && (firstDue || seconds % 10 == 0)) {
            Pelican g = spawn(level, player);
            if (g != null) near = List.of(g);
        } else if (near.size() == 1 && seconds % 60 == 0 && player.getRandom().nextFloat() < SECOND_PELICAN_CHANCE) {
            spawn(level, player);
        }

        // First gift: hand it to a pelican if none is already bringing it; retry every two minutes until it arrives.
        if (firstDue && !near.isEmpty() && seconds >= d.getInt("NextTry")) {
            Pelican g = near.get(0);
            if (!g.busyDelivering()) {
                LootParams params = new LootParams.Builder(level)
                        .withParameter(LootContextParams.ORIGIN, player.position())
                        .withParameter(LootContextParams.THIS_ENTITY, g)
                        .create(LootContextParamSets.GIFT);
                g.queueGift(player, level.getServer().getLootData().getLootTable(Pelican.FIRST_GIFT).getRandomItems(params), true);
                d.putInt("NextTry", seconds + 120);
            }
        }
    }

    private static Pelican spawn(ServerLevel level, ServerPlayer player) {
        double a = player.getRandom().nextDouble() * Math.PI * 2;
        double x = player.getX() + Math.cos(a) * 28;
        double z = player.getZ() + Math.sin(a) * 28;
        double y = Math.min(level.getMaxBuildHeight() - 4, player.getY() + 14);
        Pelican g = QuicreateContent.PELICAN.get().create(level);
        if (g == null) return null;
        g.moveTo(x, y, z, (float) Math.toDegrees(-a), 0);
        g.finalizeSpawn(level, level.getCurrentDifficultyAt(BlockPos.containing(x, y, z)), MobSpawnType.EVENT, null, null);
        level.addFreshEntity(g);
        return g;
    }
}
