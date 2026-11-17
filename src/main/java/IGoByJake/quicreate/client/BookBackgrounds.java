package IGoByJake.quicreate.client;

import IGoByJake.quicreate.Quicreate;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.ResourceManagerReloadListener;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterClientReloadListenersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.io.InputStream;
import java.util.List;

/**
 * Guide book tab backgrounds made from block textures at runtime: each block texture the player already has
 * (vanilla, Ad Astra, Create) is tiled into a 512x512 texture and darkened so the book's icons stay readable.
 * Nothing is copied into this mod; the book refers to {@code quicreate:textures/gui/book/tiled/<name>.png}.
 * Rebuilt on every resource reload, so resource packs change the backgrounds too.
 */
@Mod.EventBusSubscriber(modid = Quicreate.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class BookBackgrounds {
    /** name, source texture, tint (0xRRGGBB, or -1 for none), brightness 0..1 */
    private record Tile(String name, ResourceLocation source, int tint, float brightness) {
    }

    private static final List<Tile> TILES = List.of(
            new Tile("water", new ResourceLocation("minecraft", "textures/block/water_still.png"), 0x3F76E4, 0.75f),
            new Tile("sand", new ResourceLocation("minecraft", "textures/block/sand.png"), -1, 0.55f),
            new Tile("iron_block", new ResourceLocation("minecraft", "textures/block/iron_block.png"), -1, 0.45f),
            new Tile("copper_block", new ResourceLocation("minecraft", "textures/block/copper_block.png"), -1, 0.5f),
            new Tile("steel_block", new ResourceLocation("ad_astra", "textures/block/steel_block.png"), -1, 0.55f),
            new Tile("moon_stone", new ResourceLocation("ad_astra", "textures/block/moon_stone.png"), -1, 0.55f),
            new Tile("mars_stone", new ResourceLocation("ad_astra", "textures/block/mars_stone.png"), -1, 0.6f),
            new Tile("venus_stone", new ResourceLocation("ad_astra", "textures/block/venus_stone.png"), -1, 0.6f),
            new Tile("glacio_stone", new ResourceLocation("ad_astra", "textures/block/glacio_stone.png"), -1, 0.55f),
            new Tile("dark_oak_planks", new ResourceLocation("minecraft", "textures/block/dark_oak_planks.png"), -1, 0.75f),
            new Tile("stone_bricks", new ResourceLocation("minecraft", "textures/block/stone_bricks.png"), -1, 0.5f),
            new Tile("moss_block", new ResourceLocation("minecraft", "textures/block/moss_block.png"), -1, 0.55f),
            new Tile("mud_bricks", new ResourceLocation("minecraft", "textures/block/mud_bricks.png"), -1, 0.55f),
            new Tile("andesite_casing", new ResourceLocation("create", "textures/block/andesite_casing.png"), -1, 0.5f),
            new Tile("hay_block", new ResourceLocation("minecraft", "textures/block/hay_block_side.png"), -1, 0.45f),
            new Tile("green_wool", new ResourceLocation("minecraft", "textures/block/green_wool.png"), -1, 0.6f));

    private static final int SIZE = 512;
    private static final int PIXEL = 2;   // each texel drawn 2x2, so one block is 32 px of the 512 texture

    private BookBackgrounds() {
    }

    @SubscribeEvent
    public static void onRegisterReloadListeners(RegisterClientReloadListenersEvent event) {
        event.registerReloadListener((ResourceManagerReloadListener) BookBackgrounds::rebuild);
    }

    private static void rebuild(ResourceManager resources) {
        for (Tile tile : TILES) {
            NativeImage out = new NativeImage(SIZE, SIZE, false);
            try (InputStream in = resources.open(tile.source()); NativeImage src = NativeImage.read(in)) {
                int frame = Math.min(src.getWidth(), src.getHeight());    // animated textures: first frame only
                for (int y = 0; y < SIZE; y++) {
                    for (int x = 0; x < SIZE; x++) {
                        int abgr = src.getPixelRGBA((x / PIXEL) % frame, (y / PIXEL) % frame);
                        out.setPixelRGBA(x, y, shade(abgr, tile.tint(), tile.brightness()));
                    }
                }
            } catch (Exception e) {
                Quicreate.LOGGER.warn("[book] background {} not built from {}: {}", tile.name(), tile.source(), e.getMessage());
                out.fillRect(0, 0, SIZE, SIZE, 0xFF2A2A2A);
            }
            ResourceLocation id = new ResourceLocation(Quicreate.MODID, "textures/gui/book/tiled/" + tile.name() + ".png");
            Minecraft.getInstance().getTextureManager().register(id, new DynamicTexture(out));
        }
    }

    /** NativeImage pixels are ABGR. Applies an optional tint, darkens, and makes the pixel opaque. */
    private static int shade(int abgr, int tint, float brightness) {
        int r = abgr & 0xFF;
        int g = (abgr >> 8) & 0xFF;
        int b = (abgr >> 16) & 0xFF;
        if (tint >= 0) {
            r = r * ((tint >> 16) & 0xFF) / 255;
            g = g * ((tint >> 8) & 0xFF) / 255;
            b = b * (tint & 0xFF) / 255;
        }
        r = (int) (r * brightness);
        g = (int) (g * brightness);
        b = (int) (b * brightness);
        return 0xFF000000 | (b << 16) | (g << 8) | r;
    }
}
