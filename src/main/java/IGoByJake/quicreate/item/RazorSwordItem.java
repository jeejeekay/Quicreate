package IGoByJake.quicreate.item;

import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraftforge.common.IForgeShearable;
import net.minecraftforge.common.ToolAction;
import net.minecraftforge.common.ToolActions;

import java.util.List;

/**
 * Maptera razor sword: a sword that is also a full pair of shears. It shears sheep and other
 * shearable mobs, carves pumpkins, harvests hives, disarms tripwire and mines like shears, so
 * leaves, grass and cobwebs drop themselves. Unbreakable.
 */
public class RazorSwordItem extends SwordItem {

    public RazorSwordItem(Tier tier, int damage, float speed, Properties properties) {
        super(tier, damage, speed, properties);
    }

    @Override
    public boolean isDamageable(ItemStack stack) {
        return false;
    }

    @Override
    public boolean canPerformAction(ItemStack stack, ToolAction action) {
        return ToolActions.DEFAULT_SHEARS_ACTIONS.contains(action) || ToolActions.DEFAULT_SWORD_ACTIONS.contains(action);
    }

    @Override
    public float getDestroySpeed(ItemStack stack, BlockState state) {
        if (state.is(Blocks.COBWEB) || state.is(BlockTags.LEAVES)) {
            return 15.0F;
        }
        if (state.is(BlockTags.WOOL)) {
            return 5.0F;
        }
        if (state.is(Blocks.VINE) || state.is(Blocks.GLOW_LICHEN)) {
            return 2.0F;
        }
        return super.getDestroySpeed(stack, state);
    }

    @Override
    public boolean isCorrectToolForDrops(BlockState state) {
        return state.is(Blocks.COBWEB) || state.is(Blocks.REDSTONE_WIRE) || state.is(Blocks.TRIPWIRE) || super.isCorrectToolForDrops(state);
    }

    /** Same as Forge's shears: right-click a sheep, mooshroom, snow golem or any other shearable mob. */
    @Override
    public InteractionResult interactLivingEntity(ItemStack stack, Player player, LivingEntity entity, InteractionHand hand) {
        if (entity instanceof IForgeShearable target) {
            if (entity.level().isClientSide) {
                return InteractionResult.SUCCESS;
            }
            BlockPos pos = entity.blockPosition();
            if (target.isShearable(stack, entity.level(), pos)) {
                int fortune = EnchantmentHelper.getItemEnchantmentLevel(Enchantments.BLOCK_FORTUNE, stack);
                List<ItemStack> drops = target.onSheared(player, stack, entity.level(), pos, fortune);
                RandomSource random = entity.getRandom();
                for (ItemStack drop : drops) {
                    ItemEntity item = entity.spawnAtLocation(drop, 1.0F);
                    if (item != null) {
                        item.setDeltaMovement(item.getDeltaMovement().add(
                                (random.nextFloat() - random.nextFloat()) * 0.1F,
                                random.nextFloat() * 0.05F,
                                (random.nextFloat() - random.nextFloat()) * 0.1F));
                    }
                }
                entity.gameEvent(GameEvent.SHEAR, player);
                return InteractionResult.SUCCESS;
            }
        }
        return InteractionResult.PASS;
    }
}
