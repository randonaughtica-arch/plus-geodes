package com.plusgeodes;

import com.plusgeodes.registry.GeodeTypes;
import com.plusgeodes.registry.ModContent;
import com.plusgeodes.world.GeodeGeneration;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PlusGeodes implements ModInitializer {
    public static final String MOD_ID = "plus_geodes";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        ModContent.register();
        GeodeGeneration.register();
        LOGGER.info("Plus Geodes loaded {} geode types", GeodeTypes.ALL.size());
    }
}
