package IGoByJake.quicreate.dive;

import IGoByJake.quicreate.Quicreate;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.Optional;
import java.util.function.Supplier;

/** Quicreate's network channel. One message so far: "I dived" (client → server). */
public final class DiveNetwork {

    private static final String VERSION = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(Quicreate.MODID, "main"), () -> VERSION, VERSION::equals, VERSION::equals);

    private DiveNetwork() {
    }

    public static void register() {
        CHANNEL.registerMessage(0, DivePacket.class, (msg, buf) -> { }, buf -> new DivePacket(), DiveNetwork::handle,
                Optional.of(NetworkDirection.PLAY_TO_SERVER));
    }

    private static void handle(DivePacket msg, Supplier<NetworkEvent.Context> ctx) {
        NetworkEvent.Context context = ctx.get();
        ServerPlayer player = context.getSender();
        if (player != null) {
            context.enqueueWork(() -> Dive.serverDive(player));
        }
        context.setPacketHandled(true);
    }

    /** Empty: the server works everything out from the player. */
    public static final class DivePacket {
    }

    static void sendDive() {
        CHANNEL.sendToServer(new DivePacket());
    }
}
