package IGoByJake.quicreate.pelican;

import IGoByJake.quicreate.Quicreate;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

public class PelicanRenderer extends MobRenderer<Pelican, PelicanModel> {
    private static final ResourceLocation TEX = new ResourceLocation(Quicreate.MODID, "textures/entity/pelican.png");

    public PelicanRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new PelicanModel(ctx.bakeLayer(PelicanModel.LAYER)), 0.45F);
    }

    @Override
    public ResourceLocation getTextureLocation(Pelican bird) {
        return TEX;
    }

    @Override
    protected void setupRotations(Pelican bird, PoseStack pose, float age, float bodyYaw, float partial) {
        super.setupRotations(bird, pose, age, bodyYaw, partial);
        if (!bird.isPerched()) {
            // Pitch with its flight path (nose down in a dive) and a slow bank while circling.
            pose.mulPose(Axis.XP.rotationDegrees(bird.getViewXRot(partial)));
            pose.mulPose(Axis.ZP.rotationDegrees(Mth.sin(age * 0.02F) * 7F));
        }
    }
}
