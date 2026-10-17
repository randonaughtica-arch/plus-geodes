package com.plusgeodes.registry;

import com.plusgeodes.PlusGeodes;
import com.plusgeodes.block.BuddingCrystalBlock;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.AmethystBlock;
import net.minecraft.block.AmethystClusterBlock;
import net.minecraft.block.Block;
import net.minecraft.block.MapColor;
import net.minecraft.block.piston.PistonBehavior;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.text.Text;

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

        ItemGroup group = FabricItemGroup.builder()
                .icon(() -> new ItemStack(SETS.get(0).cluster()))
                .displayName(Text.translatable("itemGroup." + PlusGeodes.MOD_ID))
                .entries((context, entries) -> {
                    for (GeodeSet set : SETS) {
                        entries.add(set.shard());
                        entries.add(set.block());
                        entries.add(set.budding());
                        for (Block stage : set.growthStages()) {
                            entries.add(stage);
                        }
                    }
                })
                .build();
        Registry.register(Registries.ITEM_GROUP, PlusGeodes.id("geodes"), group);
    }

    private static GeodeSet registerSet(GeodeType type) {
        String id = type.id();
        MapColor color = type.mapColor();
        int light = type.blockLight();

        Block block = registerBlock(id + "_block", new AmethystBlock(AbstractBlock.Settings.create()
                .mapColor(color)
                .strength(1.5F)
                .sounds(BlockSoundGroup.AMETHYST_BLOCK)
                .requiresTool()
                .luminance(state -> light)));

        // Same heights, offsets and light levels as the vanilla amethyst stages.
        Block cluster = registerBlock(id + "_cluster",
                new AmethystClusterBlock(7.0F, 3.0F, clusterSettings(color, BlockSoundGroup.AMETHYST_CLUSTER, 5)));
        Block largeBud = registerBlock("large_" + id + "_bud",
                new AmethystClusterBlock(5.0F, 3.0F, clusterSettings(color, BlockSoundGroup.LARGE_AMETHYST_BUD, 4)));
        Block mediumBud = registerBlock("medium_" + id + "_bud",
                new AmethystClusterBlock(4.0F, 3.0F, clusterSettings(color, BlockSoundGroup.MEDIUM_AMETHYST_BUD, 2)));
        Block smallBud = registerBlock("small_" + id + "_bud",
                new AmethystClusterBlock(3.0F, 4.0F, clusterSettings(color, BlockSoundGroup.SMALL_AMETHYST_BUD, 1)));

        Block budding = registerBlock("budding_" + id, new BuddingCrystalBlock(smallBud, mediumBud, largeBud, cluster,
                AbstractBlock.Settings.create()
                        .mapColor(color)
                        .ticksRandomly()
                        .strength(1.5F)
                        .sounds(BlockSoundGroup.AMETHYST_BLOCK)
                        .requiresTool()
                        .luminance(state -> light)
                        .pistonBehavior(PistonBehavior.DESTROY)));

        Item shard = Registry.register(Registries.ITEM, PlusGeodes.id(id + "_shard"), new Item(new Item.Settings()));

        return new GeodeSet(type, block, budding, smallBud, mediumBud, largeBud, cluster, shard);
    }

    private static AbstractBlock.Settings clusterSettings(MapColor color, BlockSoundGroup sounds, int light) {
        return AbstractBlock.Settings.create()
                .mapColor(color)
                .solid()
                .nonOpaque()
                .sounds(sounds)
                .strength(1.5F)
                .luminance(state -> light)
                .pistonBehavior(PistonBehavior.DESTROY);
    }

    private static Block registerBlock(String path, Block block) {
        Registry.register(Registries.BLOCK, PlusGeodes.id(path), block);
        Registry.register(Registries.ITEM, PlusGeodes.id(path), new BlockItem(block, new Item.Settings()));
        return block;
    }
}
