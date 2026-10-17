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
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.util.Identifier;
import net.minecraft.world.biome.Biome;
import net.minecraft.world.gen.GenerationStep;
import net.minecraft.world.gen.feature.PlacedFeature;

/**
 * Adds each geode's placed feature (defined in data/plus_geodes/worldgen) to its biomes.
 * Rarity, height and shape are data-driven, so datapacks can override them.
 */
public final class GeodeGeneration {
    private GeodeGeneration() {
    }

    public static void register() {
        for (GeodeType type : GeodeTypes.ALL) {
            RegistryKey<PlacedFeature> feature =
                    RegistryKey.of(RegistryKeys.PLACED_FEATURE, PlusGeodes.id(type.id() + "_geode"));
            BiomeModifications.addFeature(selector(type), GenerationStep.Feature.UNDERGROUND_STRUCTURES, feature);
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
                TagKey<Biome> tag =
                        TagKey.of(RegistryKeys.BIOME, Identifier.of(entry.substring(1)));
                matchers.add(context -> context.hasTag(tag));
            } else {
                RegistryKey<Biome> key =
                        RegistryKey.of(RegistryKeys.BIOME, Identifier.of(entry));
                matchers.add(context -> context.getBiomeKey().equals(key));
            }
        }
        return dimension.and(context -> matchers.stream().anyMatch(matcher -> matcher.test(context)));
    }
}
