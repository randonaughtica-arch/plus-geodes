package com.plusgeodes.registry;

import com.plusgeodes.PlusGeodes;
import com.plusgeodes.block.BuddingCrystalBlock;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.AmethystBlock;
import net.minecraft.world.level.block.AmethystClusterBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

/** Registers the blocks, items and creative tab for every geode type. */
public final class ModContent {
    private static final List<GeodeSet> SETS = new ArrayList<>();

    private ModContent() {
    }

    public static List<GeodeSet> sets() {
        return Collections.unmodifiableList(SETS);
    }

    public static void register() {
        for (GeodeType type : GeodeTypes.ALL) {
            SETS.add(registerSet(type));
        }

        CreativeModeTab tab = FabricCreativeModeTab.builder()
                .icon(() -> new ItemStack(SETS.get(0).cluster()))
                .title(Component.translatable("itemGroup." + PlusGeodes.MOD_ID))
                .displayItems((parameters, output) -> {
                    for (GeodeSet set : SETS) {
                        output.accept(set.shard());
                        output.accept(set.block());
                        output.accept(set.budding());
                        for (Block stage : set.growthStages()) {
                            output.accept(stage);
                        }
                    }
                })
                .build();
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, PlusGeodes.id("geodes"), tab);
    }

    private static GeodeSet registerSet(GeodeType type) {
        String id = type.id();
        MapColor color = type.mapColor();
        int light = type.blockLight();

        Block block = registerBlock(id + "_block", AmethystBlock::new, BlockBehaviour.Properties.of()
                .mapColor(color)
                .strength(1.5F)
                .sound(SoundType.AMETHYST)
                .requiresCorrectToolForDrops()
                .lightLevel(state -> light));

        // Same heights, widths and light levels as the vanilla amethyst stages.
        Block cluster = registerBlock(id + "_cluster", p -> new AmethystClusterBlock(7.0F, 10.0F, p),
                clusterProperties(color, SoundType.AMETHYST_CLUSTER, 5));
        Block largeBud = registerBlock("large_" + id + "_bud", p -> new AmethystClusterBlock(5.0F, 10.0F, p),
                clusterProperties(color, SoundType.LARGE_AMETHYST_BUD, 4));
        Block mediumBud = registerBlock("medium_" + id + "_bud", p -> new AmethystClusterBlock(4.0F, 10.0F, p),
                clusterProperties(color, SoundType.MEDIUM_AMETHYST_BUD, 2));
        Block smallBud = registerBlock("small_" + id + "_bud", p -> new AmethystClusterBlock(3.0F, 8.0F, p),
                clusterProperties(color, SoundType.SMALL_AMETHYST_BUD, 1));

        Block budding = registerBlock("budding_" + id,
                p -> new BuddingCrystalBlock(smallBud, mediumBud, largeBud, cluster, p),
                BlockBehaviour.Properties.of()
                        .mapColor(color)
                        .randomTicks()
                        .strength(1.5F)
                        .sound(SoundType.AMETHYST)
                        .requiresCorrectToolForDrops()
                        .lightLevel(state -> light)
                        .pushReaction(PushReaction.DESTROY));

        ResourceKey<Item> shardKey = ResourceKey.create(Registries.ITEM, PlusGeodes.id(id + "_shard"));
        Item shard = Registry.register(BuiltInRegistries.ITEM, shardKey, new Item(new Item.Properties().setId(shardKey)));

        return new GeodeSet(type, block, budding, smallBud, mediumBud, largeBud, cluster, shard);
    }

    private static BlockBehaviour.Properties clusterProperties(MapColor color, SoundType sound, int light) {
        return BlockBehaviour.Properties.of()
                .mapColor(color)
                .forceSolidOn()
                .noOcclusion()
                .sound(sound)
                .strength(1.5F)
                .lightLevel(state -> light)
                .pushReaction(PushReaction.DESTROY);
    }

    private static Block registerBlock(String path, Function<BlockBehaviour.Properties, Block> factory,
            BlockBehaviour.Properties properties) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PlusGeodes.id(path));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, factory.apply(properties.setId(blockKey)));

        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, PlusGeodes.id(path));
        BlockItem item = new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix());
        item.registerBlocks(Item.BY_BLOCK, item);
        Registry.register(BuiltInRegistries.ITEM, itemKey, item);
        return block;
    }
}
