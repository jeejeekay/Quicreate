package IGoByJake.quicreate.loot;

import IGoByJake.quicreate.item.TieredFishingRodItem;
import com.google.common.base.Suppliers;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.common.loot.LootModifier;

import java.util.List;
import java.util.function.Supplier;

/**
 * Replaces a fishing catch with a kelpy ball (or a rare extra) depending on the rod's tier. The
 * chances live in {@code data/quicreate/loot_modifiers/fishing_kelpy_balls.json}, one entry per
 * tier: 0 = vanilla/other rods, 1 = brass, 2 = desh, 3 = ostrum. Heaviest rolls first.
 */
public class KelpyFishingModifier extends LootModifier {

    public record Extra(Item item, float chance) {
        public static final Codec<Extra> CODEC = RecordCodecBuilder.create(i -> i.group(
                BuiltInRegistries.ITEM.byNameCodec().fieldOf("item").forGetter(Extra::item),
                Codec.floatRange(0, 1).fieldOf("chance").forGetter(Extra::chance)
        ).apply(i, Extra::new));
    }

    public record Tier(Item light, Item medium, Item heavy, float lightChance, float mediumChance, float heavyChance, List<Extra> extras) {
        public static final Codec<Tier> CODEC = RecordCodecBuilder.create(i -> i.group(
                BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("light_item", net.minecraft.world.item.Items.AIR).forGetter(Tier::light),
                BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("medium_item", net.minecraft.world.item.Items.AIR).forGetter(Tier::medium),
                BuiltInRegistries.ITEM.byNameCodec().optionalFieldOf("heavy_item", net.minecraft.world.item.Items.AIR).forGetter(Tier::heavy),
                Codec.floatRange(0, 1).optionalFieldOf("light", 0F).forGetter(Tier::lightChance),
                Codec.floatRange(0, 1).optionalFieldOf("medium", 0F).forGetter(Tier::mediumChance),
                Codec.floatRange(0, 1).optionalFieldOf("heavy", 0F).forGetter(Tier::heavyChance),
                Extra.CODEC.listOf().optionalFieldOf("extras", List.of()).forGetter(Tier::extras)
        ).apply(i, Tier::new));
    }

    public static final Supplier<Codec<KelpyFishingModifier>> CODEC = Suppliers.memoize(() -> RecordCodecBuilder.create(i ->
            codecStart(i).and(Tier.CODEC.listOf().fieldOf("tiers").forGetter(m -> m.tiers)).apply(i, KelpyFishingModifier::new)));

    private final List<Tier> tiers;

    public KelpyFishingModifier(LootItemCondition[] conditions, List<Tier> tiers) {
        super(conditions);
        this.tiers = tiers;
    }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> generatedLoot, LootContext context) {
        if (this.tiers.isEmpty()) {
            return generatedLoot;
        }
        ItemStack rod = context.getParamOrNull(LootContextParams.TOOL);
        int index = rod != null && rod.getItem() instanceof TieredFishingRodItem tiered ? tiered.tier() : 0;
        Tier tier = this.tiers.get(Math.min(index, this.tiers.size() - 1));
        RandomSource random = context.getRandom();

        for (Extra extra : tier.extras()) {
            if (random.nextFloat() < extra.chance()) {
                return replace(generatedLoot, extra.item());
            }
        }
        if (tier.heavy() != net.minecraft.world.item.Items.AIR && random.nextFloat() < tier.heavyChance()) {
            return replace(generatedLoot, tier.heavy());
        }
        if (tier.medium() != net.minecraft.world.item.Items.AIR && random.nextFloat() < tier.mediumChance()) {
            return replace(generatedLoot, tier.medium());
        }
        if (tier.light() != net.minecraft.world.item.Items.AIR && random.nextFloat() < tier.lightChance()) {
            return replace(generatedLoot, tier.light());
        }
        return generatedLoot;
    }

    private static ObjectArrayList<ItemStack> replace(ObjectArrayList<ItemStack> loot, Item item) {
        loot.clear();
        loot.add(new ItemStack(item));
        return loot;
    }

    @Override
    public Codec<? extends IGlobalLootModifier> codec() {
        return CODEC.get();
    }
}
