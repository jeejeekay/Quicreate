package IGoByJake.quicreate.command;

import IGoByJake.quicreate.worldgen.HelixConfiguration;
import IGoByJake.quicreate.worldgen.QuicreateWorldgen;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.JsonOps;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.util.random.SimpleWeightedRandomList;
import net.minecraft.util.valueproviders.ConstantFloat;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;
import net.minecraft.world.level.levelgen.feature.stateproviders.WeightedStateProvider;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Shape testing: {@code /qshape helix height=40 radius=3 turns=4 thickness=1 strands=3 taper=0.9
 * rungs=0 blocks=packed_ice:4,blue_ice:1 rung=snow_block} builds a tower where you stand (the base
 * sinks 2 blocks, like worldgen), then prints the matching preset JSON, click it to copy.
 * Any setting left out uses the Glacio spire defaults. Best used in a creative test world.
 */
public final class ShapeCommand {

    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();

    private ShapeCommand() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("qshape")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("helix")
                        .executes(context -> helix(context.getSource(), ""))
                        .then(Commands.argument("settings", StringArgumentType.greedyString())
                                .executes(context -> helix(context.getSource(), StringArgumentType.getString(context, "settings"))))));
    }

    private static int helix(CommandSourceStack source, String settings) {
        Map<String, String> values = new HashMap<>();
        for (String part : settings.trim().split("\\s+")) {
            int eq = part.indexOf('=');
            if (eq > 0) {
                values.put(part.substring(0, eq).toLowerCase(), part.substring(eq + 1));
            }
        }
        HelixConfiguration config;
        try {
            config = new HelixConfiguration(
                    ConstantInt.of(Integer.parseInt(values.getOrDefault("height", "40"))),
                    ConstantFloat.of(Float.parseFloat(values.getOrDefault("radius", "3"))),
                    ConstantFloat.of(Float.parseFloat(values.getOrDefault("turns", "4"))),
                    Integer.parseInt(values.getOrDefault("thickness", "1")),
                    Integer.parseInt(values.getOrDefault("strands", "3")),
                    Float.parseFloat(values.getOrDefault("taper", "0.9")),
                    Integer.parseInt(values.getOrDefault("rungs", "0")),
                    provider(values.getOrDefault("blocks", "minecraft:packed_ice:4,minecraft:blue_ice:1")),
                    provider(values.getOrDefault("rung", "minecraft:snow_block")),
                    Integer.parseInt(values.getOrDefault("sink", "2")),
                    List.of());
        } catch (IllegalArgumentException e) {
            source.sendFailure(Component.literal("Bad shape setting: " + e.getMessage()));
            return 0;
        }

        // Same validation as the preset files, so anything that places here also loads as a preset.
        Optional<JsonElement> encoded = HelixConfiguration.CODEC.encodeStart(JsonOps.INSTANCE, config).result();
        if (encoded.isEmpty()) {
            source.sendFailure(Component.literal("Bad shape setting: a value is out of range (height 1-256, radius/turns 0-32, thickness/strands 1-8, taper 0-1, rungs 0-64, sink 0-16)"));
            return 0;
        }

        ServerLevel level = source.getLevel();
        BlockPos origin = BlockPos.containing(source.getPosition());
        QuicreateWorldgen.HELIX.get().place(config, level, level.getChunkSource().getGenerator(), RandomSource.create(), origin);

        JsonObject preset = new JsonObject();
        preset.addProperty("type", "quicreate:helix");
        preset.add("config", encoded.get());
        String json = GSON.toJson(preset);
        source.sendSuccess(() -> Component.literal("Placed helix. Preset (click to copy): ")
                .append(Component.literal(json).withStyle(style -> style
                        .withColor(ChatFormatting.AQUA)
                        .withClickEvent(new ClickEvent(ClickEvent.Action.COPY_TO_CLIPBOARD, json))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal("Copy preset JSON"))))), false);
        return 1;
    }

    /** "minecraft:packed_ice:4,blue_ice:1" -> weighted provider; a single block -> simple provider. */
    private static BlockStateProvider provider(String spec) {
        SimpleWeightedRandomList.Builder<BlockState> list = SimpleWeightedRandomList.builder();
        int entries = 0;
        BlockState single = null;
        for (String raw : spec.split(",")) {
            String entry = raw.trim();
            if (entry.isEmpty()) {
                continue;
            }
            int weight = 1;
            int last = entry.lastIndexOf(':');
            if (last > 0 && entry.substring(last + 1).matches("\\d+")) {
                weight = Integer.parseInt(entry.substring(last + 1));
                entry = entry.substring(0, last);
            }
            ResourceLocation id = ResourceLocation.tryParse(entry.contains(":") ? entry : "minecraft:" + entry);
            if (id == null || !BuiltInRegistries.BLOCK.containsKey(id)) {
                throw new IllegalArgumentException("unknown block '" + entry + "'");
            }
            Block block = BuiltInRegistries.BLOCK.get(id);
            single = block.defaultBlockState();
            list.add(single, weight);
            entries++;
        }
        if (entries == 0) {
            return BlockStateProvider.simple(Blocks.PACKED_ICE);
        }
        return entries == 1 ? BlockStateProvider.simple(single) : new WeightedStateProvider(list.build());
    }
}
