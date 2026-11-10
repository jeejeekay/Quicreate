package IGoByJake.quicreate.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;

import javax.annotation.Nullable;
import java.util.List;

/**
 * Light / medium / heavy kelpy balls, fished up instead of crates. Right-click anywhere (air or a
 * block) to open one, sneak to open the whole stack. Deployers can open them too. Contents come
 * from the loot table {@code quicreate:kelpy_ball_<size>}.
 */
public class KelpyBallItem extends Item {

    private final ResourceLocation lootTable;

    public KelpyBallItem(ResourceLocation lootTable, Properties properties) {
        super(properties);
        this.lootTable = lootTable;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            int count = player.isShiftKeyDown() ? stack.getCount() : 1;
            LootTable table = server.getServer().getLootData().getLootTable(this.lootTable);
            for (int i = 0; i < count; i++) {
                LootParams params = new LootParams.Builder(server)
                        .withParameter(LootContextParams.ORIGIN, player.position())
                        .withParameter(LootContextParams.THIS_ENTITY, player)
                        .withLuck(player.getLuck())
                        .create(LootContextParamSets.GIFT);
                for (ItemStack drop : table.getRandomItems(params)) {
                    if (!player.getInventory().add(drop)) {
                        player.drop(drop, false);
                    }
                }
            }
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundType.WET_GRASS.getBreakSound(), SoundSource.PLAYERS, 1.0F, 0.8F);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BUNDLE_DROP_CONTENTS, SoundSource.PLAYERS, 0.8F, 1.0F);
            player.awardStat(Stats.ITEM_USED.get(this));
            if (!player.getAbilities().instabuild) {
                stack.shrink(count);
            }
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("item.quicreate.kelpy_ball.tooltip.open").withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("item.quicreate.kelpy_ball.tooltip.stack").withStyle(ChatFormatting.DARK_GRAY));
    }
}
