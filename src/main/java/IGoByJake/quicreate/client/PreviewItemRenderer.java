package IGoByJake.quicreate.client;

import IGoByJake.quicreate.book.PreviewItemBlock;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.core.Direction;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.registries.ForgeRegistries;

/** Draws the real block's item model for a {@link PreviewItemBlock} in a Field Guide build preview. */
public class PreviewItemRenderer implements BlockEntityRenderer<PreviewItemBlock.PreviewItemBlockEntity> {

    public PreviewItemRenderer(BlockEntityRendererProvider.Context context) {
    }

    @Override
    public void render(PreviewItemBlock.PreviewItemBlockEntity be, float partialTick, PoseStack pose, MultiBufferSource buffers,
                       int light, int overlay) {
        BlockState state = be.getBlockState();
        if (!(state.getBlock() instanceof PreviewItemBlock block)) {
            return;
        }
        var item = ForgeRegistries.ITEMS.getValue(block.item());
        if (item == null) {
            return;
        }
        pose.pushPose();
        pose.translate(0.5, 0.5, 0.5);
        // The same turns the generator coil's blockstate file gives each axis (y first, then x).
        Direction.Axis axis = state.getValue(RotatedPillarBlock.AXIS);
        if (axis == Direction.Axis.X) {
            pose.mulPose(Axis.YP.rotationDegrees(-90));
            pose.mulPose(Axis.XP.rotationDegrees(-90));
        } else if (axis == Direction.Axis.Z) {
            pose.mulPose(Axis.YP.rotationDegrees(-180));
            pose.mulPose(Axis.XP.rotationDegrees(-90));
        }
        Minecraft.getInstance().getItemRenderer().renderStatic(new ItemStack(item), ItemDisplayContext.NONE, light, overlay,
                pose, buffers, be.getLevel(), 0);
        pose.popPose();
    }
}
