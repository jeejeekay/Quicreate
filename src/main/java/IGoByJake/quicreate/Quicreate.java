package IGoByJake.quicreate;

import IGoByJake.quicreate.command.ShapeCommand;
import IGoByJake.quicreate.worldgen.QuicreateWorldgen;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(Quicreate.MODID)
public class Quicreate {

  public static final String MODID = "quicreate";
  public static final Logger LOGGER = LogManager.getLogger();


  public Quicreate() {
    IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();
    ModRegistry.register(modEventBus);
    QuicreateWorldgen.register(modEventBus);
    QuicreateContent.register(modEventBus);
    MinecraftForge.EVENT_BUS.addListener((RegisterCommandsEvent event) -> ShapeCommand.register(event.getDispatcher()));
    new ConfigManager();
    modEventBus.addListener(this::addCreative);
    FMLJavaModLoadingContext.get().getModEventBus().addListener(this::setup);
    FMLJavaModLoadingContext.get().getModEventBus().addListener(this::setupClient);
  }

  private void addCreative(BuildCreativeModeTabContentsEvent event){
    if(event.getTabKey() == CreativeModeTabs.INGREDIENTS){
      event.accept(ModRegistry.CREATIVE_ALLOY);
      event.accept(ModRegistry.CREATIVE_SHEET);
      event.accept(ModRegistry.ENDERITE_INGOT);

      event.accept(ModRegistry.CREATIVE_CASING);

      event.accept(ModRegistry.EMERALD_CIRCUIT);
      //event.accept(ModRegistry.ETRIUM_CIRCUIT);
      event.accept(ModRegistry.AMETHYST_CIRCUIT);
      event.accept(ModRegistry.ANCIENT_METAL_CIRCUIT);

      event.accept(ModRegistry.INCOMPLETE_COPPER_CIRCUIT);
      event.accept(ModRegistry.INCOMPLETE_EMERALD_CIRCUIT);
      //event.accept(ModRegistry.INCOMPLETE_ETRIUM_CIRCUIT);
      event.accept(ModRegistry.INCOMPLETE_AMETHYST_CIRCUIT);
      event.accept(ModRegistry.INCOMPLETE_ANCIENT_METAL_CIRCUIT);

      //event.accept(ModRegistry.ETRIUM_WAFER);
      event.accept(ModRegistry.EMERALD_WAFER);
      event.accept(ModRegistry.AMETHYST_WAFER);
      event.accept(ModRegistry.ANCIENT_METAL_WAFER);

      event.accept(ModRegistry.MAPTERA_RAZOR_SWORD);
      event.accept(ModRegistry.ANCIENT_GILDED_SWORD);
      event.accept(ModRegistry.PLATINUM_MASTER_SWORD);
    }
    if(event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES){
      event.accept(ModRegistry.BRASS_FISHING_ROD);
      event.accept(ModRegistry.DESH_FISHING_ROD);
      event.accept(ModRegistry.OSTRUM_FISHING_ROD);
      event.accept(ModRegistry.LIGHT_KELPY_BALL);
      event.accept(ModRegistry.MEDIUM_KELPY_BALL);
      event.accept(ModRegistry.HEAVY_KELPY_BALL);
    }
  }

  private void setup(final FMLCommonSetupEvent event) {
    //    MinecraftForge.EVENT_BUS.register(new WhateverEvents()); 
  }

  private void setupClient(final FMLClientSetupEvent event) {
    //for client side only setup
  }
}
