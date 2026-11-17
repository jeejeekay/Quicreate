package IGoByJake.quicreate.item;

import IGoByJake.quicreate.entity.LavaFishingHook;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.FishingRodItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A fireproof rod that fishes in lava (see LavaFishingHook). Same bite timing as a normal rod; Lure and Luck of
 * the Sea work as usual. Made by wrapping a fishing rod in obsidian scales.
 */
public class ObsidianFishingRodItem extends FishingRodItem {
    public ObsidianFishingRodItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.fishing != null) {
            if (!level.isClientSide) {
                int damage = player.fishing.retrieve(stack);
                stack.hurtAndBreak(damage, player, p -> p.broadcastBreakEvent(hand));
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FISHING_BOBBER_RETRIEVE, SoundSource.NEUTRAL,
                    1.0F, 0.4F / (level.getRandom().nextFloat() * 0.4F + 0.8F));
            player.gameEvent(GameEvent.ITEM_INTERACT_FINISH);
        } else {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FISHING_BOBBER_THROW, SoundSource.NEUTRAL,
                    0.5F, 0.4F / (level.getRandom().nextFloat() * 0.4F + 0.8F));
            if (!level.isClientSide) {
                int lure = EnchantmentHelper.getFishingSpeedBonus(stack);
                int luck = EnchantmentHelper.getFishingLuckBonus(stack);
                level.addFreshEntity(new LavaFishingHook(player, level, luck, lure));
            }
            player.awardStat(Stats.ITEM_USED.get(this));
            player.gameEvent(GameEvent.ITEM_INTERACT_START);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tips, TooltipFlag flag) {
        tips.add(Component.translatable("item.quicreate.obsidian_fishing_rod.desc").withStyle(ChatFormatting.GOLD));
    }
}
