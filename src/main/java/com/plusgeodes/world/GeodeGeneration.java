package com.plusgeodes.world;

import com.plusgeodes.PlusGeodes;
import com.plusgeodes.registry.GeodeType;
import com.plusgeodes.registry.GeodeTypes;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectionContext;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;

/**
 * Adds each geode's placed feature (defined in data/plus_geodes/worldgen) to its biomes.
 * Rarity, height and shape are data-driven, so datapacks can override them.
 */
public final class GeodeGeneration {
    private GeodeGeneration() {
    }

    public static void register() {
        for (GeodeType type : GeodeTypes.ALL) {
            ResourceKey<PlacedFeature> feature =
                    ResourceKey.create(Registries.PLACED_FEATURE, PlusGeodes.id(type.id() + "_geode"));
            BiomeModifications.addFeature(selector(type), GenerationStep.Decoration.UNDERGROUND_STRUCTURES, feature);
        }
    }

    private static Predicate<BiomeSelectionContext> selector(GeodeType type) {
        Predicate<BiomeSelectionContext> dimension = switch (type.dimension()) {
            case OVERWORLD -> BiomeSelectors.foundInOverworld();
            case NETHER -> BiomeSelectors.foundInTheNether();
            case END -> BiomeSelectors.foundInTheEnd();
        };
        if (type.biomes().isEmpty()) {
            return dimension;
        }

        List<Predicate<BiomeSelectionContext>> matchers = new ArrayList<>();
        for (String entry : type.biomes()) {
            if (entry.startsWith("#")) {
                TagKey<Biome> tag = TagKey.create(Registries.BIOME, Identifier.parse(entry.substring(1)));
                matchers.add(context -> context.hasTag(tag));
            } else {
                ResourceKey<Biome> key = ResourceKey.create(Registries.BIOME, Identifier.parse(entry));
                matchers.add(context -> context.getBiomeKey().equals(key));
            }
        }
        return dimension.and(context -> matchers.stream().anyMatch(matcher -> matcher.test(context)));
    }
}
