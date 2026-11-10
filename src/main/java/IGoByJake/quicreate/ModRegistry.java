package IGoByJake.quicreate;

import IGoByJake.quicreate.item.GildedSwordItem;
import IGoByJake.quicreate.item.KelpyBallItem;
import IGoByJake.quicreate.item.MasterSwordItem;
import IGoByJake.quicreate.item.RazorSwordItem;
import IGoByJake.quicreate.item.TieredFishingRodItem;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import static net.minecraft.world.item.Items.DIAMOND;
import static net.minecraft.world.item.Items.registerItem;

@Mod.EventBusSubscriber(bus = Mod.EventBusSubscriber.Bus.MOD)
public class ModRegistry {
  public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, Quicreate.MODID);

  public static final RegistryObject<Block> CREATIVE_CASING = BLOCKS.register("creative_casing", () ->
          new Block(BlockBehaviour.Properties.copy(Blocks.NETHERITE_BLOCK)
                  .mapColor(MapColor.TERRACOTTA_PINK)
                  .strength(30.0F, 1200.0F)));

  public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, Quicreate.MODID);

  public static final RegistryObject<Item> CREATIVE_ALLOY =
          ITEMS.register("creative_alloy", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> CREATIVE_SHEET =
          ITEMS.register("creative_sheet", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> ENDERITE_INGOT =
          ITEMS.register("enderite_ingot", () -> new Item(new Item.Properties()));

  public static final RegistryObject<Item> EMERALD_CIRCUIT =
          ITEMS.register("emerald_circuit", () -> new Item(new Item.Properties()));
  /*public static final RegistryObject<Item> ETRIUM_CIRCUIT =
          ITEMS.register("etrium_circuit", () -> new Item(new Item.Properties()));*/
  public static final RegistryObject<Item> ANCIENT_METAL_CIRCUIT =
          ITEMS.register("ancient_metal_circuit", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> AMETHYST_CIRCUIT =
          ITEMS.register("amethyst_circuit", () -> new Item(new Item.Properties()));


  public static final RegistryObject<Item> EMERALD_WAFER =
          ITEMS.register("emerald_wafer", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> ANCIENT_METAL_WAFER =
          ITEMS.register("ancient_metal_wafer", () -> new Item(new Item.Properties()));
  /*public static final RegistryObject<Item> ETRIUM_WAFER =
          ITEMS.register("etrium_wafer", () -> new Item(new Item.Properties()));*/
  public static final RegistryObject<Item> AMETHYST_WAFER =
          ITEMS.register("amethyst_wafer", () -> new Item(new Item.Properties()));

  public static final RegistryObject<Item> INCOMPLETE_EMERALD_WAFER =
          ITEMS.register("incomplete_emerald_wafer", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_ANCIENT_METAL_WAFER =
          ITEMS.register("incomplete_ancient_metal_wafer", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_ETRIUM_WAFER =
          ITEMS.register("incomplete_etrium_wafer", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_AMETHYST_WAFER =
          ITEMS.register("incomplete_amethyst_wafer", () -> new Item(new Item.Properties()));

  public static final RegistryObject<Item> INCOMPLETE_CREATIVE_SHEET =
          ITEMS.register("incomplete_creative_sheet", () -> new Item(new Item.Properties()));

  public static final RegistryObject<Item> INCOMPLETE_BLANK_CIRCUIT =
          ITEMS.register("incomplete_blank_circuit", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_COPPER_CIRCUIT =
          ITEMS.register("incomplete_copper_circuit", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_EMERALD_CIRCUIT =
          ITEMS.register("incomplete_emerald_circuit", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_AMETHYST_CIRCUIT =
          ITEMS.register("incomplete_amethyst_circuit", () -> new Item(new Item.Properties()));
  public static final RegistryObject<Item> INCOMPLETE_ANCIENT_METAL_CIRCUIT =
          ITEMS.register("incomplete_ancient_metal_circuit", () -> new Item(new Item.Properties()));

  // Unbreakable special swords
  public static final RegistryObject<Item> MAPTERA_RAZOR_SWORD =
          ITEMS.register("maptera_razor_sword", () -> new RazorSwordItem(Tiers.DIAMOND,3,-1.8f, new Item.Properties()));
  public static final RegistryObject<Item> ANCIENT_GILDED_SWORD =
          ITEMS.register("ancient_gilded_sword", () -> new GildedSwordItem(Tiers.NETHERITE,5,-2.4f, new Item.Properties()));
  public static final RegistryObject<Item> PLATINUM_MASTER_SWORD =
          ITEMS.register("platinum_master_sword", () -> new MasterSwordItem(Tiers.NETHERITE,6,-1.8f, new Item.Properties()));

  // Fishing: kelpy balls (open with right-click or a deployer) and tiered rods
  public static final RegistryObject<Item> LIGHT_KELPY_BALL =
          ITEMS.register("light_kelpy_ball", () -> new KelpyBallItem(new ResourceLocation(Quicreate.MODID, "kelpy_ball_light"), new Item.Properties()));
  public static final RegistryObject<Item> MEDIUM_KELPY_BALL =
          ITEMS.register("medium_kelpy_ball", () -> new KelpyBallItem(new ResourceLocation(Quicreate.MODID, "kelpy_ball_medium"), new Item.Properties()));
  public static final RegistryObject<Item> HEAVY_KELPY_BALL =
          ITEMS.register("heavy_kelpy_ball", () -> new KelpyBallItem(new ResourceLocation(Quicreate.MODID, "kelpy_ball_heavy"), new Item.Properties().rarity(Rarity.UNCOMMON)));
  public static final RegistryObject<Item> BRASS_FISHING_ROD =
          ITEMS.register("brass_fishing_rod", () -> new TieredFishingRodItem(1, new Item.Properties().durability(128)));
  public static final RegistryObject<Item> DESH_FISHING_ROD =
          ITEMS.register("desh_fishing_rod", () -> new TieredFishingRodItem(2, new Item.Properties().durability(256)));
  public static final RegistryObject<Item> OSTRUM_FISHING_ROD =
          ITEMS.register("ostrum_fishing_rod", () -> new TieredFishingRodItem(3, new Item.Properties().durability(512)));

  public static final RegistryObject<Item> CREATIVE_CASING_ITEM = ITEMS.register("creative_casing", () -> new BlockItem(CREATIVE_CASING.get(), new Item.Properties()));

  public static void register(IEventBus eventbus){
  ITEMS.register(eventbus);
  BLOCKS.register(eventbus);
}
  public static final DeferredRegister<BlockEntityType<?>> TILE_ENTITIES = DeferredRegister.create(ForgeRegistries.BLOCK_ENTITY_TYPES, Quicreate.MODID);

}
