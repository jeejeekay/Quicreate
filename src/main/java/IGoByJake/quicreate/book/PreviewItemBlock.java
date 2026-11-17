package IGoByJake.quicreate.book;

import IGoByJake.quicreate.QuicreateContent;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A stand-in block used only in Field Guide build previews, never placed in a world (it has no item).
 *
 * <p>Some blocks, like Create: New Age's generator coil, are drawn by Create's animation system instead of as a
 * normal block, and that system is off inside the book, so they vanish from the preview. A build shows this
 * block in their place ({@code "display"} in a {@code modonomicon:blockstate} matcher, with the real block as
 * {@code "block"}), and its renderer draws the real block's item model, which is what its inventory icon uses.
 * The {@code axis} turns it the same way the real block's states do.
 */
public class PreviewItemBlock extends RotatedPillarBlock implements EntityBlock {

    private final ResourceLocation item;

    public PreviewItemBlock(Properties properties, ResourceLocation item) {
        super(properties);
        this.item = item;
    }

    public ResourceLocation item() {
        return item;
    }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.ENTITYBLOCK_ANIMATED;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new PreviewItemBlockEntity(pos, state);
    }

    public static class PreviewItemBlockEntity extends BlockEntity {
        public PreviewItemBlockEntity(BlockPos pos, BlockState state) {
            super(QuicreateContent.PREVIEW_ITEM_BE.get(), pos, state);
        }
    }
}
