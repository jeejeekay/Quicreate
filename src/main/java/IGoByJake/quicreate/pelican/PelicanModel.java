package IGoByJake.quicreate.pelican;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

/**
 * A white pelican: big body, S-necked head, long upper bill, and a hinged lower bill carrying the throat pouch.
 * The lower bill swings down to drop gifts and to scoop fish; the pouch bulges while it's carrying something.
 */
public class PelicanModel extends HierarchicalModel<Pelican> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(new ResourceLocation(Quicreate.MODID, "pelican"), "main");

    private final ModelPart root;
    private final ModelPart neck;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart pouch;
    private final ModelPart leftWing;
    private final ModelPart rightWing;
    private final ModelPart leftLeg;
    private final ModelPart rightLeg;

    public PelicanModel(ModelPart root) {
        this.root = root;
        this.neck = root.getChild("neck");
        this.head = this.neck.getChild("head");
        this.jaw = this.head.getChild("jaw");
        this.pouch = this.jaw.getChild("pouch");
        this.leftWing = root.getChild("left_wing");
        this.rightWing = root.getChild("right_wing");
        this.leftLeg = root.getChild("left_leg");
        this.rightLeg = root.getChild("right_leg");
    }

    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition r = mesh.getRoot();
        r.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 0).addBox(-3.5F, -3.0F, -5.5F, 7, 6, 11), PartPose.offset(0, 17, 0));
        PartDefinition neck = r.addOrReplaceChild("neck", CubeListBuilder.create().texOffs(36, 0).addBox(-1.5F, -5.0F, -1.5F, 3, 5, 3),
                PartPose.offset(0, 15, -5));
        PartDefinition head = neck.addOrReplaceChild("head", CubeListBuilder.create().texOffs(48, 0).addBox(-2.0F, -3.0F, -2.5F, 4, 3, 4),
                PartPose.offset(0, -5, 0));
        head.addOrReplaceChild("bill", CubeListBuilder.create().texOffs(36, 8).addBox(-1.0F, -0.5F, -9.0F, 2, 1, 9),
                PartPose.offset(0, -1.5F, -2.5F));
        // Lower bill hinges at the back of the bill; the pouch hangs from it.
        PartDefinition jaw = head.addOrReplaceChild("jaw", CubeListBuilder.create().texOffs(0, 17).addBox(-1.0F, 0.0F, -9.0F, 2, 1, 9),
                PartPose.offset(0, -1.0F, -2.5F));
        jaw.addOrReplaceChild("pouch", CubeListBuilder.create().texOffs(22, 17).addBox(-1.0F, 0.0F, -7.0F, 2, 3, 7),
                PartPose.offset(0, 1.0F, -1.0F));
        PartDefinition rw = r.addOrReplaceChild("right_wing", CubeListBuilder.create().texOffs(0, 27).addBox(-11.0F, 0.0F, -2.0F, 11, 1, 8),
                PartPose.offset(-3.5F, 15, -2));
        rw.addOrReplaceChild("right_tip", CubeListBuilder.create().texOffs(38, 27).addBox(-16.0F, 0.0F, -1.0F, 5, 1, 6), PartPose.ZERO);
        PartDefinition lw = r.addOrReplaceChild("left_wing", CubeListBuilder.create().texOffs(0, 36).addBox(0.0F, 0.0F, -2.0F, 11, 1, 8),
                PartPose.offset(3.5F, 15, -2));
        lw.addOrReplaceChild("left_tip", CubeListBuilder.create().texOffs(38, 36).addBox(11.0F, 0.0F, -1.0F, 5, 1, 6), PartPose.ZERO);
        r.addOrReplaceChild("tail", CubeListBuilder.create().texOffs(0, 45).addBox(-2.5F, -0.5F, 0.0F, 5, 1, 3), PartPose.offset(0, 16, 5.5F));
        r.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(16, 45).addBox(-0.5F, 0.0F, -0.5F, 1, 4, 1), PartPose.offset(-1.5F, 20, 1));
        r.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(16, 45).addBox(-0.5F, 0.0F, -0.5F, 1, 4, 1), PartPose.offset(1.5F, 20, 1));
        return LayerDefinition.create(mesh, 64, 64);
    }

    @Override
    public ModelPart root() {
        return this.root;
    }

    @Override
    public void setupAnim(Pelican bird, float limbSwing, float limbAmount, float age, float headYaw, float headPitch) {
        this.root().getAllParts().forEach(ModelPart::resetPose);
        float partial = age - bird.tickCount;
        // Bill: swings open to drop or scoop.
        this.jaw.xRot = bird.mouthOpen(partial) * 0.75F;
        if (bird.pouchFull()) {
            this.pouch.yScale = 1.6F;
            this.pouch.zScale = 1.1F;
        }
        // Neck tucked back in flight, upright when perched.
        if (bird.isPerched()) {
            this.neck.xRot = 0.15F;
            this.head.xRot = -0.15F + Mth.sin(age * 0.05F) * 0.05F;
            this.neck.yRot = Mth.sin(age * 0.03F) * 0.35F;
            this.rightWing.zRot = 1.45F;
            this.leftWing.zRot = -1.45F;
            this.rightWing.y += 1.0F;
            this.leftWing.y += 1.0F;
            return;
        }
        this.neck.xRot = 0.9F;
        this.head.xRot = -0.9F;
        this.rightLeg.xRot = 1.3F;
        this.leftLeg.xRot = 1.3F;
        float flap;
        if (bird.isDiving()) {
            flap = -1.1F; // wings swept back for the plunge
        } else {
            // Pelicans mostly glide, with a few slow deep beats now and then.
            float burst = Mth.clamp(Mth.sin(age * 0.03F) * 3F - 1.8F, 0F, 1F);
            flap = Mth.sin(age * 0.35F) * 0.55F * burst + Mth.sin(age * 0.1F) * 0.05F;
        }
        this.rightWing.zRot = flap;
        this.leftWing.zRot = -flap;
    }
}
