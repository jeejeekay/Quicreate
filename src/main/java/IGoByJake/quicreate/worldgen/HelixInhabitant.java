package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.valueproviders.ConstantInt;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.entity.EntityType;

/**
 * A mob a helix tower may start with, placed on its upper strands when the tower generates.
 * These mobs don't despawn, so the population stays exactly what the chances give.
 *
 * @param entity        mob to place
 * @param chance        chance per tower (0-1)
 * @param count         how many when it happens
 * @param finalizeSpawn run the mob's normal spawn setup. Off for the Elokosa howler, whose
 *                      spawn setup summons a pack of 3-4 followers.
 */
public record HelixInhabitant(EntityType<?> entity, float chance, IntProvider count, boolean finalizeSpawn) {

    public static final Codec<HelixInhabitant> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            BuiltInRegistries.ENTITY_TYPE.byNameCodec().fieldOf("entity").forGetter(HelixInhabitant::entity),
            Codec.floatRange(0.0F, 1.0F).fieldOf("chance").forGetter(HelixInhabitant::chance),
            IntProvider.codec(1, 16).optionalFieldOf("count", ConstantInt.of(1)).forGetter(HelixInhabitant::count),
            Codec.BOOL.optionalFieldOf("finalize_spawn", true).forGetter(HelixInhabitant::finalizeSpawn)
    ).apply(instance, HelixInhabitant::new));
}
