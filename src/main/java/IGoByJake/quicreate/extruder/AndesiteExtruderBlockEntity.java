package IGoByJake.quicreate.extruder;

import IGoByJake.quicreate.Quicreate;
import com.oierbravo.createmechanicalextruder.components.extruder.ExtruderBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.items.ItemHandlerHelper;
import net.minecraftforge.items.ItemStackHandler;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.List;

import static net.minecraft.world.level.block.state.properties.BlockStateProperties.HORIZONTAL_FACING;

/**
 * The Andesite Extruder: a Mechanical Extruder that makes a random natural stone instead of one fixed block.
 *
 * <p>Like the normal extruder it needs lava on one side and water on the other. The block underneath picks the
 * loot table that is rolled each cycle: {@code quicreate:andesite_extruder/<namespace>/<block path>}, for example
 * {@code quicreate:andesite_extruder/ad_astra/moon_stone}. Blocks without a table use
 * {@code quicreate:andesite_extruder/default}. Adding a catalyst is one loot table JSON, no code.
 *
 * <p>Output goes into a 9-slot buffer (mixed stones would jam the original single slot). Everything else, the
 * pole animation, goggles, right-click to empty and automation pulling, comes from the original extruder.
 */
public class AndesiteExtruderBlockEntity extends ExtruderBlockEntity {
    public static final int SLOTS = 9;
    public static final int BONKS_PER_ROLL = 1;

    public AndesiteExtruderBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state);
        // replace the single output slot; the inherited item capability is created lazily and picks this up
        outputInv = new ItemStackHandler(SLOTS) {
            @Override
            protected void onContentsChanged(int slot) {
                setChanged();
            }
        };
    }

    public static ResourceLocation tableFor(Block below) {
        ResourceLocation id = ForgeRegistries.BLOCKS.getKey(below);
        if (id == null) {
            return defaultTable();
        }
        return new ResourceLocation(Quicreate.MODID, "andesite_extruder/" + id.getNamespace() + "/" + id.getPath());
    }

    public static ResourceLocation defaultTable() {
        return new ResourceLocation(Quicreate.MODID, "andesite_extruder/default");
    }

    private boolean hasFluids() {
        if (level == null) {
            return false;
        }
        Direction facing = getBlockState().getValue(HORIZONTAL_FACING);
        FluidState a = level.getFluidState(worldPosition.relative(facing.getClockWise()));
        FluidState b = level.getFluidState(worldPosition.relative(facing.getCounterClockWise()));
        boolean lava = (a.is(FluidTags.LAVA) && a.isSource()) || (b.is(FluidTags.LAVA) && b.isSource());
        boolean water = (a.is(FluidTags.WATER) && a.isSource()) || (b.is(FluidTags.WATER) && b.isSource());
        return lava && water;
    }

    @Override
    public boolean hasEnoughOutputSpace() {
        for (int i = 0; i < outputInv.getSlots(); i++) {
            ItemStack s = outputInv.getStackInSlot(i);
            if (s.isEmpty() || s.getCount() < s.getMaxStackSize()) {
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean tryProcess(boolean simulate) {
        if (level == null || level.isClientSide || !hasFluids() || !hasEnoughOutputSpace()) {
            return false;
        }
        if (simulate) {
            return true;
        }
        if (getExtrudingBehaviour().addBonk() < BONKS_PER_ROLL) {
            setChanged();
            return true;
        }
        getExtrudingBehaviour().resetBonks();

        ServerLevel server = (ServerLevel) level;
        Block below = level.getBlockState(worldPosition.below()).getBlock();
        LootTable table = server.getServer().getLootData().getLootTable(tableFor(below));
        if (table == LootTable.EMPTY) {
            table = server.getServer().getLootData().getLootTable(defaultTable());
        }
        LootParams params = new LootParams.Builder(server)
                .withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(worldPosition))
                .create(LootContextParamSets.CHEST);
        List<ItemStack> drops = table.getRandomItems(params);
        for (ItemStack drop : drops) {
            ItemHandlerHelper.insertItemStacked(outputInv, drop, false);   // overflow is lost, like a full extruder
        }
        setChanged();
        return true;
    }
}
