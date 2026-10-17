package com.plusgeodes.registry;

import java.util.List;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

/** Every block and item registered for one geode type. */
public record GeodeSet(
        GeodeType type,
        Block block,
        Block budding,
        Block smallBud,
        Block mediumBud,
        Block largeBud,
        Block cluster,
        Item shard) {

    public List<Block> growthStages() {
        return List.of(smallBud, mediumBud, largeBud, cluster);
    }
}
