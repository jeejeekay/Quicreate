package IGoByJake.quicreate.worldgen;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class QuicreateWorldgen {

    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(ForgeRegistries.FEATURES, Quicreate.MODID);

    /** {@code quicreate:helix}: twisted multi-strand towers (Glacio helix spires). */
    public static final RegistryObject<HelixFeature> HELIX = FEATURES.register("helix", () -> new HelixFeature(HelixConfiguration.CODEC));

    private QuicreateWorldgen() {
    }

    public static void register(IEventBus modBus) {
        FEATURES.register(modBus);
    }
}
