package IGoByJake.quicreate.advancement;

import IGoByJake.quicreate.Quicreate;
import com.google.gson.JsonObject;
import net.minecraft.advancements.critereon.AbstractCriterionTriggerInstance;
import net.minecraft.advancements.critereon.ContextAwarePredicate;
import net.minecraft.advancements.critereon.DeserializationContext;
import net.minecraft.advancements.critereon.SerializationContext;
import net.minecraft.advancements.critereon.SimpleCriterionTrigger;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.util.GsonHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.ForgeRegistries;

import javax.annotation.Nullable;

/**
 * Advancement trigger "quicreate:has_items": the player holds at least {@code count} of an item (or of any items
 * in a tag) across their whole inventory, not just in one stack. Used by the guide book's progress advancements,
 * the way the old quest book counted items.
 *
 * <pre>{"trigger": "quicreate:has_items", "conditions": {"item": "minecraft:sand", "count": 16}}
 * {"trigger": "quicreate:has_items", "conditions": {"tag": "minecraft:logs", "count": 16}}</pre>
 *
 * Checked once a second for every player by {@link QuicreateTriggers}.
 */
public class HasItemsTrigger extends SimpleCriterionTrigger<HasItemsTrigger.Instance> {
    public static final ResourceLocation ID = new ResourceLocation(Quicreate.MODID, "has_items");

    @Override
    public ResourceLocation getId() {
        return ID;
    }

    @Override
    protected Instance createInstance(JsonObject json, ContextAwarePredicate player, DeserializationContext context) {
        Item item = null;
        TagKey<Item> tag = null;
        if (json.has("item")) {
            ResourceLocation id = new ResourceLocation(GsonHelper.getAsString(json, "item"));
            item = ForgeRegistries.ITEMS.getValue(id);
            if (item == null) {
                Quicreate.LOGGER.warn("[quicreate:has_items] unknown item {}", id);
            }
        }
        if (json.has("tag")) {
            tag = TagKey.create(Registries.ITEM, new ResourceLocation(GsonHelper.getAsString(json, "tag")));
        }
        int count = GsonHelper.getAsInt(json, "count", 1);
        return new Instance(player, item, tag, count);
    }

    public void trigger(ServerPlayer player) {
        this.trigger(player, instance -> instance.matches(player));
    }

    public static class Instance extends AbstractCriterionTriggerInstance {
        @Nullable
        private final Item item;
        @Nullable
        private final TagKey<Item> tag;
        private final int count;

        public Instance(ContextAwarePredicate player, @Nullable Item item, @Nullable TagKey<Item> tag, int count) {
            super(ID, player);
            this.item = item;
            this.tag = tag;
            this.count = Math.max(1, count);
        }

        private boolean accepts(ItemStack stack) {
            if (stack.isEmpty()) {
                return false;
            }
            if (item != null) {
                return stack.is(item);
            }
            return tag != null && stack.is(tag);
        }

        public boolean matches(ServerPlayer player) {
            if (item == null && tag == null) {
                return false;
            }
            Inventory inv = player.getInventory();
            int found = 0;
            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack stack = inv.getItem(i);
                if (accepts(stack)) {
                    found += stack.getCount();
                    if (found >= count) {
                        return true;
                    }
                }
            }
            return false;
        }

        @Override
        public JsonObject serializeToJson(SerializationContext context) {
            JsonObject json = super.serializeToJson(context);
            if (item != null) {
                ResourceLocation key = ForgeRegistries.ITEMS.getKey(item);
                if (key != null) {
                    json.addProperty("item", key.toString());
                }
            }
            if (tag != null) {
                json.addProperty("tag", tag.location().toString());
            }
            json.addProperty("count", count);
            return json;
        }
    }
}
