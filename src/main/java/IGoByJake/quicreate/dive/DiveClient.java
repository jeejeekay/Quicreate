package IGoByJake.quicreate.dive;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Options;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Pose;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.glfw.GLFW;

/** Client half of the {@link Dive}: the trigger, the movement, ending the pose, and the grey haze. */
@Mod.EventBusSubscriber(modid = Quicreate.MODID, value = Dist.CLIENT)
public final class DiveClient {

    private static long lastDive = Long.MIN_VALUE / 2;
    private static long poseUntil;
    private static long hazeUntil;

    private DiveClient() {
    }

    @SubscribeEvent
    public static void onKey(InputEvent.Key event) {
        if (event.getAction() != GLFW.GLFW_PRESS) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        Options options = mc.options;
        if (player == null || mc.screen != null || !options.keySprint.matches(event.getKey(), event.getScanCode())) {
            return;
        }
        int forward = (options.keyUp.isDown() ? 1 : 0) - (options.keyDown.isDown() ? 1 : 0);
        int left = (options.keyLeft.isDown() ? 1 : 0) - (options.keyRight.isDown() ? 1 : 0);
        if ((forward == 0 && left == 0) || (forward == 1 && left == 0)) {
            return; // standing still or straight forward: ordinary sprint
        }
        long now = player.level().getGameTime();
        if (now - lastDive < Dive.COOLDOWN_TICKS || !player.onGround() || !Dive.canDive(player)) {
            return;
        }
        lastDive = now;

        // Same rotation vanilla uses to turn WASD into a world direction
        float yaw = player.getYRot() * Mth.DEG_TO_RAD;
        double sin = Mth.sin(yaw), cos = Mth.cos(yaw);
        double length = Math.sqrt(forward * forward + left * left);
        double x = (left * cos - forward * sin) / length;
        double z = (forward * cos + left * sin) / length;
        player.setDeltaMovement(x * Dive.SPEED, Dive.HOP, z * Dive.SPEED);
        player.setForcedPose(Pose.SWIMMING);   // vanilla eases the camera down, like crouching
        poseUntil = now + Dive.POSE_TICKS;
        hazeUntil = now + Dive.INVULNERABLE_TICKS;
        DiveNetwork.sendDive();
    }

    /** Ends the dive pose. Returns at once unless a dive is under way. */
    @SubscribeEvent
    public static void onClientTick(TickEvent.ClientTickEvent event) {
        if (poseUntil == 0 || event.phase != TickEvent.Phase.END) {
            return;
        }
        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null) {
            poseUntil = 0;
        } else if (player.level().getGameTime() >= poseUntil) {
            player.setForcedPose(null);
            poseUntil = 0;
        }
    }

    /** Grey haze around the screen edges while invincible, fading out. Draws nothing otherwise. */
    static void renderHaze(GuiGraphics gfx, float partialTick, int width, int height) {
        if (hazeUntil == 0) {
            return;
        }
        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null) {
            hazeUntil = 0;
            return;
        }
        float left = (hazeUntil - (player.level().getGameTime() + partialTick)) / Dive.INVULNERABLE_TICKS;
        if (left <= 0) {
            hazeUntil = 0;
            return;
        }
        float strength = Math.min(1.0F, left * 1.5F);
        int rings = 12;
        int edge = (int) (Math.min(width, height) * 0.28F);
        int t = Math.max(1, edge / rings);
        for (int i = 0; i < rings; i++) {
            float fade = 1.0F - (float) i / rings;
            int alpha = (int) (150 * strength * fade * fade);
            int color = (alpha << 24) | 0x8E9399;
            int a = i * t, b = a + t;
            gfx.fill(a, a, width - a, b, color);                       // top
            gfx.fill(a, height - b, width - a, height - a, color);     // bottom
            gfx.fill(a, b, b, height - b, color);                      // left
            gfx.fill(width - b, b, width - a, height - b, color);      // right
        }
        gfx.fill(0, 0, width, height, ((int) (28 * strength) << 24) | 0x8E9399);
    }

    @Mod.EventBusSubscriber(modid = Quicreate.MODID, value = Dist.CLIENT, bus = Mod.EventBusSubscriber.Bus.MOD)
    public static final class Overlay {
        private Overlay() {
        }

        @SubscribeEvent
        public static void register(RegisterGuiOverlaysEvent event) {
            event.registerAboveAll("dive_haze", (gui, gfx, partialTick, width, height) -> renderHaze(gfx, partialTick, width, height));
        }
    }
}
