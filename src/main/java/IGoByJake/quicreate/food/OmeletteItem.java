package IGoByJake.quicreate.food;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.function.Supplier;

/**
 * An omelette eaten in bites, the way Neopian Omelettes does it: whole → nibbled → partial → gone.
 * Each bite gives the item's food (and its effects) and hands back the next stage.
 */
public class OmeletteItem extends Item {

    private final Supplier<? extends Item> next;   // null on the last bite
    private final boolean foil;
    private final String tooltipKey;               // null for none

    public OmeletteItem(Properties properties, @Nullable Supplier<? extends Item> next, boolean foil, @Nullable String tooltipKey) {
        super(properties.stacksTo(1));
        this.next = next;
        this.foil = foil;
        this.tooltipKey = tooltipKey;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        ItemStack rest = next == null ? ItemStack.EMPTY : new ItemStack(next.get());
        ItemStack left = super.finishUsingItem(stack, level, entity);
        if (rest.isEmpty()) {
            return left;
        }
        if (left.isEmpty()) {
            return rest;
        }
        if (entity instanceof Player player && !player.getAbilities().instabuild && !player.getInventory().add(rest)) {
            player.drop(rest, false);
        }
        return left;
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return foil || super.isFoil(stack);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        if (tooltipKey != null) {
            tooltip.add(Component.translatable(tooltipKey).withStyle(ChatFormatting.DARK_GREEN));
        }
    }
}
