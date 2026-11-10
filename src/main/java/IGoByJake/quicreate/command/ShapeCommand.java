package IGoByJake.quicreate.command;

import IGoByJake.quicreate.worldgen.HelixConfiguration;
import IGoByJake.quicreate.worldgen.QuicreateWorldgen;
import IGoByJake.quicreate.worldgen.ShapedFeature;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import com.mojang.brigadier.suggestion.SuggestionsBuilder;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.JsonOps;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Shape testing: {@code /qshape helix height=40 radius=3 turns=4 thickness=1 strands=3 taper=0.9
 * rungs=0 blocks=packed_ice:4,blue_ice:1 rung=snow_block} builds a tower where you stand (the base
 * sinks 2 blocks, like worldgen), then prints the matching preset JSON, click it to copy.
 * Any setting left out uses the Glacio spire defaults. Best used in a creative test world.
 * <p>
 * The other shapes work the same way and start from a named preset, which {@code from=} can swap:
 * {@code /qshape prism_spike from=quicreate:mercury_lone_spike length=30..44 tilt=10..40 count=1..3}.
 * Settings use the preset's JSON names. {@code a..b} is a random range, blocks are written like
 * {@code mercury_stone:6,magma_block:1} (block states such as {@code glacian_log[axis=y]} work too).
 * Tab completion lists every setting.
 */
public final class ShapeCommand {

    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().create();

    private ShapeCommand() {
    }

    private static final Pattern RANGE = Pattern.compile("^(-?\\d+(?:\\.\\d+)?)\\.\\.(-?\\d+(?:\\.\\d+)?)$");
    private static final Pattern NUMBER = Pattern.compile("^-?\\d+(?:\\.\\d+)?$");

    /** A shape the command can place: its feature, the preset it starts from, and its setting names. */
    private record ShapeType(String name, Supplier<? extends ShapedFeature<?>> feature, String preset, List<String> keys) {
    }

    private static final List<ShapeType> TYPES = List.of(
            new ShapeType("prism_spike", QuicreateWorldgen.PRISM_SPIKE, "quicreate:mercury_spike_cluster",
                    List.of("length", "width", "taper", "tilt", "sink", "count", "spread", "arrangement", "blocks")),
            new ShapeType("fissure", QuicreateWorldgen.FISSURE, "quicreate:mercury_fissure",
                    List.of("length", "width", "depth", "lava_depth", "wander", "bridge_chance", "lining_chance", "lava", "lining")),
            new ShapeType("crater", QuicreateWorldgen.CRATER, "quicreate:moon_crater",
                    List.of("radius", "depth", "rim_height", "rim_width", "floor_depth", "floor", "rim", "core", "core_chance", "core_radius")),
            new ShapeType("giant_mushroom", QuicreateWorldgen.GIANT_MUSHROOM, "quicreate:mars_aeronos_mushroom",
                    List.of("stem_height", "stem_radius", "bend", "cap_radius", "cap_height", "cap_shape", "stem", "cap", "underside", "underside_chance", "sink")),
            new ShapeType("arch", QuicreateWorldgen.ARCH, "quicreate:mars_arch",
                    List.of("span", "height", "thickness", "roughness", "sink", "blocks")),
            new ShapeType("boulder", QuicreateWorldgen.BOULDER, "quicreate:moon_boulder",
                    List.of("radius", "squash", "sink", "count", "spread", "blocks")));

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        LiteralArgumentBuilder<CommandSourceStack> root = Commands.literal("qshape")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("helix")
                        .executes(context -> helix(context.getSource(), ""))
                        .then(Commands.argument("settings", StringArgumentType.greedyString())
                                .suggests(keys(List.of("height", "radius", "turns", "thickness", "strands", "taper", "rungs", "blocks", "rung", "sink")))
                                .executes(context -> helix(context.getSource(), StringArgumentType.getString(context, "settings")))));
        for (ShapeType type : TYPES) {
            List<String> keys = new ArrayList<>(type.keys());
            keys.add("from");
            root.then(Commands.literal(type.name())
                    .executes(context -> shaped(context.getSource(), type, ""))
                    .then(Commands.argument("settings", StringArgumentType.greedyString())
                            .suggests(keys(keys))
                            .executes(context -> shaped(context.getSource(), type, StringArgumentType.getString(context, "settings")))));
        }
        dispatcher.register(root);
    }

    /** Suggests "key=" for each setting not typed yet. */
    private static SuggestionProvider<CommandSourceStack> keys(List<String> keys) {
        return (context, builder) -> {
            String remaining = builder.getRemaining();
            int lastSpace = remaining.lastIndexOf(' ');
            String current = remaining.substring(lastSpace + 1);
            if (current.contains("=")) {
                return builder.buildFuture();
            }
            SuggestionsBuilder offset = builder.createOffset(builder.getStart() + lastSpace + 1);
            for (String key : keys) {
                if (key.startsWith(current.toLowerCase()) && !(" " + remaining).contains(" " + key + "=")) {
                    offset.suggest(key + "=");
                }
            }
            return offset.buildFuture();
        };
    }

    private static Map<String, String> settings(String settings) {
        Map<String, String> values = new LinkedHashMap<>();
        for (String part : settings.trim().split("\\s+")) {
            int eq = part.indexOf('=');
            if (eq > 0) {
                values.put(part.substring(0, eq).toLowerCase(), part.substring(eq + 1));
            }
        }
        return values;
    }

    private static int shaped(CommandSourceStack source, ShapeType type, String settings) {
        ShapedFeature<?> feature = type.feature().get();
        return shaped(source, type, feature, settings);
    }

    private static <C extends FeatureConfiguration> int shaped(CommandSourceStack source, ShapeType type, ShapedFeature<C> feature, String settings) {
        Map<String, String> values = settings(settings);
        String presetName = values.remove("from");
        if (presetName == null) {
            presetName = type.preset();
        }
        for (String key : values.keySet()) {
            if (!type.keys().contains(key)) {
                source.sendFailure(Component.literal("Unknown " + type.name() + " setting '" + key + "'. Settings: " + String.join(", ", type.keys())));
                return 0;
            }
        }

        // Start from the preset's settings.
        Registry<ConfiguredFeature<?, ?>> registry = source.getServer().registryAccess().registryOrThrow(Registries.CONFIGURED_FEATURE);
        ResourceLocation presetId = ResourceLocation.tryParse(presetName.contains(":") ? presetName : "quicreate:" + presetName);
        ConfiguredFeature<?, ?> preset = presetId == null ? null : registry.get(presetId);
        if (preset == null || preset.feature() != feature) {
            source.sendFailure(Component.literal("No " + type.name() + " preset called '" + presetName + "'"));
            return 0;
        }
        @SuppressWarnings("unchecked")
        C base = (C) preset.config();
        JsonObject json = feature.configCodec().encodeStart(JsonOps.INSTANCE, base).result()
                .filter(JsonElement::isJsonObject).map(JsonElement::getAsJsonObject).orElseGet(JsonObject::new);
        try {
            for (Map.Entry<String, String> entry : values.entrySet()) {
                json.add(entry.getKey(), value(entry.getValue()));
            }
        } catch (IllegalArgumentException e) {
            source.sendFailure(Component.literal("Bad shape setting: " + e.getMessage()));
            return 0;
        }

        // Same validation as the preset files, so anything that places here also loads as a preset.
        DataResult<C> parsed = feature.configCodec().parse(JsonOps.INSTANCE, json);
        Optional<C> config = parsed.result();
        if (config.isEmpty()) {
            source.sendFailure(Component.literal("Bad shape setting: " + parsed.error().map(DataResult.PartialResult::message).orElse("invalid value")));
            return 0;
        }

        ServerLevel level = source.getLevel();
        BlockPos origin = BlockPos.containing(source.getPosition());
        feature.place(config.get(), level, level.getChunkSource().getGenerator(), RandomSource.create(), origin);

        JsonObject out = new JsonObject();
        out.addProperty("type", "quicreate:" + type.name());
        out.add("config", feature.configCodec().encodeStart(JsonOps.INSTANCE, config.get()).result().orElse(json));
        String text = GSON.toJson(out);
        source.sendSuccess(() -> Component.literal("Placed " + type.name() + " (from " + presetId + "). Preset (click to copy): ")
                .append(Component.literal(text).withStyle(style -> style
                        .withColor(ChatFormatting.AQUA)
                        .withClickEvent(new ClickEvent(ClickEvent.Action.COPY_TO_CLIPBOARD, text))
                        .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, Component.literal("Copy preset JSON"))))), false);
        return 1;
    }

    /** Turns a typed setting into preset JSON: true/false, a number, a..b range, blocks, or plain text. */
    private static JsonElement value(String raw) {
        if (raw.equalsIgnoreCase("true") || raw.equalsIgnoreCase("false")) {
            return new JsonPrimitive(Boolean.parseBoolean(raw));
        }
        Matcher range = RANGE.matcher(raw);
        if (range.matches()) {
            JsonPrimitive min = number(range.group(1));
            JsonPrimitive max = number(range.group(2));
            if (min.getAsDouble() == max.getAsDouble()) {
                return min;
            }
            // Whole-number and decimal ranges name their top end differently; give both, the unused one is ignored.
            JsonObject bounds = new JsonObject();
            bounds.add("min_inclusive", min);
            bounds.add("max_inclusive", max);
            bounds.add("max_exclusive", max);
            JsonObject uniform = new JsonObject();
            uniform.addProperty("type", "minecraft:uniform");
            uniform.add("value", bounds);
            return uniform;
        }
        if (NUMBER.matcher(raw).matches()) {
            return number(raw);
        }
        if (raw.contains(",") || parseState(raw) != null) {
            return blocks(raw);
        }
        return new JsonPrimitive(raw);
    }

    private static JsonPrimitive number(String text) {
        return text.contains(".") ? new JsonPrimitive(Double.parseDouble(text)) : new JsonPrimitive(Integer.parseInt(text));
    }

    private static BlockState parseState(String text) {
        try {
            return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK.asLookup(), text, false).blockState();
        } catch (CommandSyntaxException e) {
            return null;
        }
    }

    /** "mercury_stone:6,magma_block:1" -> weighted provider JSON; a single block -> simple provider JSON. */
    private static JsonElement blocks(String spec) {
        JsonArray entries = new JsonArray();
        JsonElement single = null;
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
            BlockState state = parseState(entry);
            if (state == null) {
                throw new IllegalArgumentException("unknown block '" + entry + "'");
            }
            single = BlockState.CODEC.encodeStart(JsonOps.INSTANCE, state).result()
                    .orElseThrow(() -> new IllegalArgumentException("can't save block '" + raw.trim() + "'"));
            JsonObject weighted = new JsonObject();
            weighted.add("data", single);
            weighted.addProperty("weight", weight);
            entries.add(weighted);
        }
        if (single == null) {
            throw new IllegalArgumentException("no blocks given");
        }
        JsonObject provider = new JsonObject();
        if (entries.size() == 1) {
            provider.addProperty("type", "minecraft:simple_state_provider");
            provider.add("state", single);
        } else {
            provider.addProperty("type", "minecraft:weighted_state_provider");
            provider.add("entries", entries);
        }
        return provider;
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
