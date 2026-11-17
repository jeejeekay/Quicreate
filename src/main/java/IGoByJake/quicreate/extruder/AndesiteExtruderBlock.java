package IGoByJake.quicreate.extruder;

import com.oierbravo.createmechanicalextruder.components.extruder.ExtruderBlock;
import com.oierbravo.createmechanicalextruder.components.extruder.ExtruderBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;

/** Same block as the Mechanical Extruder, pointed at the Andesite Extruder's block entity. */
public class AndesiteExtruderBlock extends ExtruderBlock {
    public AndesiteExtruderBlock(Properties properties) {
        super(properties);
    }

    @Override
    public BlockEntityType<? extends ExtruderBlockEntity> getBlockEntityType() {
        return AndesiteExtruder.BLOCK_ENTITY.get();
    }
}
