package IGoByJake.quicreate.item;

import net.minecraft.world.item.FishingRodItem;

/**
 * Brass (1), desh (2) and ostrum (3) fishing rods. The tier decides which kelpy balls and extra
 * catches can be fished up (see {@code KelpyFishingModifier}); vanilla and other rods count as 0.
 */
public class TieredFishingRodItem extends FishingRodItem {

    private final int tier;

    public TieredFishingRodItem(int tier, Properties properties) {
        super(properties);
        this.tier = tier;
    }

    public int tier() {
        return this.tier;
    }
}
