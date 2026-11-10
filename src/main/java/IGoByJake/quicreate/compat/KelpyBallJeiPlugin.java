package IGoByJake.quicreate.compat;

import IGoByJake.quicreate.ModRegistry;
import IGoByJake.quicreate.Quicreate;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.gui.drawable.IDrawable;
import mezz.jei.api.gui.ingredient.IRecipeSlotsView;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.registration.IRecipeCatalystRegistration;
import mezz.jei.api.registration.IRecipeCategoryRegistration;
import mezz.jei.api.registration.IRecipeRegistration;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.EnchantedBookItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.minecraftforge.registries.RegistryObject;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * JEI page "Kelpy Ball Contents": what each kelpy ball can contain, with the chance per roll and
 * the count. Read straight from the loot table files inside the Quicreate jar, so it needs no
 * server data and always matches those files.
 */
@JeiPlugin
public class KelpyBallJeiPlugin implements IModPlugin {

    public static final RecipeType<Contents> TYPE = RecipeType.create(Quicreate.MODID, "kelpy_ball", Contents.class);

    public record Drop(List<ItemStack> stacks, float chance, int min, int max) {
    }

    public record Contents(ItemStack ball, int minRolls, int maxRolls, List<Drop> drops) {
    }

    @Override
    public ResourceLocation getPluginUid() {
        return new ResourceLocation(Quicreate.MODID, "jei_plugin");
    }

    @Override
    public void registerCategories(IRecipeCategoryRegistration registration) {
        registration.addRecipeCategories(new Category(registration.getJeiHelpers().getGuiHelper()));
    }

    @Override
    public void registerRecipes(IRecipeRegistration registration) {
        List<Contents> all = new ArrayList<>();
        for (Map.Entry<RegistryObject<Item>, String> ball : Map.of(
                ModRegistry.LIGHT_KELPY_BALL, "kelpy_ball_light",
                ModRegistry.MEDIUM_KELPY_BALL, "kelpy_ball_medium",
                ModRegistry.HEAVY_KELPY_BALL, "kelpy_ball_heavy").entrySet()) {
            Contents contents = read(new ItemStack(ball.getKey().get()), ball.getValue());
            if (contents != null) {
                all.add(contents);
            }
        }
        all.sort((a, b) -> Integer.compare(BuiltInRegistries.ITEM.getId(a.ball().getItem()), BuiltInRegistries.ITEM.getId(b.ball().getItem())));
        registration.addRecipes(TYPE, all);
    }

    @Override
    public void registerRecipeCatalysts(IRecipeCatalystRegistration registration) {
        registration.addRecipeCatalyst(new ItemStack(ModRegistry.LIGHT_KELPY_BALL.get()), TYPE);
        registration.addRecipeCatalyst(new ItemStack(ModRegistry.MEDIUM_KELPY_BALL.get()), TYPE);
        registration.addRecipeCatalyst(new ItemStack(ModRegistry.HEAVY_KELPY_BALL.get()), TYPE);
    }

    // ------------------------------------------------------------------ loot table reading

    private static Contents read(ItemStack ball, String table) {
        String path = "/data/" + Quicreate.MODID + "/loot_tables/" + table + ".json";
        try (InputStream in = KelpyBallJeiPlugin.class.getResourceAsStream(path)) {
            if (in == null) {
                Quicreate.LOGGER.warn("JEI: missing loot table {}", path);
                return null;
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            JsonObject pool = root.getAsJsonArray("pools").get(0).getAsJsonObject();
            int[] rolls = range(pool.get("rolls"));
            JsonArray entries = pool.getAsJsonArray("entries");
            int totalWeight = 0;
            for (JsonElement e : entries) {
                totalWeight += weight(e.getAsJsonObject());
            }
            List<Drop> drops = new ArrayList<>();
            for (JsonElement e : entries) {
                JsonObject entry = e.getAsJsonObject();
                List<ItemStack> stacks = stacks(entry);
                if (stacks.isEmpty()) {
                    continue;
                }
                int[] count = {1, 1};
                if (entry.has("functions")) {
                    for (JsonElement f : entry.getAsJsonArray("functions")) {
                        JsonObject function = f.getAsJsonObject();
                        if ("minecraft:set_count".equals(function.get("function").getAsString())) {
                            count = range(function.get("count"));
                        }
                    }
                }
                drops.add(new Drop(stacks, totalWeight == 0 ? 0 : (float) weight(entry) / totalWeight, count[0], count[1]));
            }
            drops.sort((a, b) -> Float.compare(b.chance(), a.chance()));
            return new Contents(ball, rolls[0], rolls[1], drops);
        } catch (Exception ex) {
            Quicreate.LOGGER.error("JEI: couldn't read loot table {}", path, ex);
            return null;
        }
    }

    private static int weight(JsonObject entry) {
        return entry.has("weight") ? entry.get("weight").getAsInt() : 1;
    }

    private static int[] range(JsonElement value) {
        if (value == null) {
            return new int[]{1, 1};
        }
        if (value.isJsonPrimitive()) {
            int v = (int) value.getAsFloat();
            return new int[]{v, v};
        }
        JsonObject o = value.getAsJsonObject();
        return new int[]{(int) o.get("min").getAsFloat(), (int) o.get("max").getAsFloat()};
    }

    private static List<ItemStack> stacks(JsonObject entry) {
        String type = entry.get("type").getAsString();
        String name = entry.get("name").getAsString();
        List<ItemStack> stacks = new ArrayList<>();
        if ("minecraft:tag".equals(type)) {
            TagKey<Item> tag = TagKey.create(Registries.ITEM, new ResourceLocation(name));
            for (Holder<Item> holder : BuiltInRegistries.ITEM.getTagOrEmpty(tag)) {
                stacks.add(new ItemStack(holder.value()));
            }
            return stacks;
        }
        ResourceLocation id = ResourceLocation.tryParse(name);
        if (id == null || !BuiltInRegistries.ITEM.containsKey(id)) {
            return stacks;
        }
        ItemStack stack = new ItemStack(BuiltInRegistries.ITEM.get(id));
        if (stack.is(Items.BOOK) && entry.has("functions")) {
            for (JsonElement f : entry.getAsJsonArray("functions")) {
                JsonObject function = f.getAsJsonObject();
                if ("minecraft:set_enchantments".equals(function.get("function").getAsString())) {
                    ItemStack book = new ItemStack(Items.ENCHANTED_BOOK);
                    for (Map.Entry<String, JsonElement> enchant : function.getAsJsonObject("enchantments").entrySet()) {
                        Enchantment enchantment = BuiltInRegistries.ENCHANTMENT.get(new ResourceLocation(enchant.getKey()));
                        if (enchantment != null) {
                            EnchantedBookItem.addEnchantment(book, new EnchantmentInstance(enchantment, (int) enchant.getValue().getAsFloat()));
                        }
                    }
                    stack = book;
                }
            }
        }
        stacks.add(stack);
        return stacks;
    }

    // ------------------------------------------------------------------ category

    private static final int COLUMNS = 9;

    public static class Category implements IRecipeCategory<Contents> {

        private final IDrawable background;
        private final IDrawable icon;
        private final IDrawable slot;

        public Category(IGuiHelper gui) {
            this.background = gui.createBlankDrawable(getWidth(), getHeight());
            this.icon = gui.createDrawableIngredient(VanillaTypes.ITEM_STACK, new ItemStack(ModRegistry.MEDIUM_KELPY_BALL.get()));
            this.slot = gui.getSlotDrawable();
        }

        @Override
        public RecipeType<Contents> getRecipeType() {
            return TYPE;
        }

        @Override
        public Component getTitle() {
            return Component.translatable("jei.quicreate.kelpy_ball");
        }

        public int getWidth() {
            return 34 + COLUMNS * 18;
        }

        public int getHeight() {
            return 12 + 2 * 18;
        }

        @SuppressWarnings("removal")
        public IDrawable getBackground() {
            return this.background;
        }

        @Override
        public IDrawable getIcon() {
            return this.icon;
        }

        @Override
        public void setRecipe(IRecipeLayoutBuilder builder, Contents recipe, IFocusGroup focuses) {
            builder.addSlot(RecipeIngredientRole.INPUT, 1, 13)
                    .setBackground(this.slot, -1, -1)
                    .addItemStack(recipe.ball());
            int index = 0;
            for (Drop drop : recipe.drops()) {
                if (index >= COLUMNS * 2) {
                    break;
                }
                int x = 34 + (index % COLUMNS) * 18 + 1;
                int y = 12 + (index / COLUMNS) * 18 + 1;
                builder.addSlot(RecipeIngredientRole.OUTPUT, x, y)
                        .setBackground(this.slot, -1, -1)
                        .addItemStacks(drop.stacks())
                        .addTooltipCallback((view, tooltip) -> {
                            tooltip.add(Component.translatable("jei.quicreate.kelpy_ball.chance",
                                    String.format("%.1f", drop.chance() * 100)).withStyle(ChatFormatting.GOLD));
                            if (drop.max() > 1) {
                                tooltip.add(Component.translatable("jei.quicreate.kelpy_ball.count",
                                        drop.min() == drop.max() ? String.valueOf(drop.min()) : drop.min() + "-" + drop.max()).withStyle(ChatFormatting.GRAY));
                            }
                        });
                index++;
            }
        }

        @Override
        public void draw(Contents recipe, IRecipeSlotsView slots, GuiGraphics graphics, double mouseX, double mouseY) {
            String rolls = recipe.minRolls() == recipe.maxRolls() ? String.valueOf(recipe.minRolls()) : recipe.minRolls() + "-" + recipe.maxRolls();
            graphics.drawString(Minecraft.getInstance().font, Component.translatable("jei.quicreate.kelpy_ball.rolls", rolls), 34, 1, 0xFF404040, false);
        }
    }
}
