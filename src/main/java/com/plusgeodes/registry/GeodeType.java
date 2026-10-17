package com.plusgeodes.registry;

import java.util.List;
import net.minecraft.block.MapColor;

/**
 * The per-geode settings the game code needs at registration time. Everything else
 * (textures, worldgen shape, loot) lives in generated resources.
 *
 * @param id         base id, e.g. {@code "citrine"}
 * @param mapColor   map colour of every block in the set
 * @param blockLight light level emitted by the crystal block and budding block
 * @param dimension  dimension the geode generates in
 * @param biomes     biome ids or {@code #tag} ids it generates in; empty means the whole dimension
 */
public record GeodeType(String id, MapColor mapColor, int blockLight, Dimension dimension, List<String> biomes) {
    public enum Dimension {
        OVERWORLD,
        NETHER,
        END
    }
}
