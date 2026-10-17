package com.plusgeodes.client;

import com.plusgeodes.registry.GeodeSet;
import com.plusgeodes.registry.ModContent;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.minecraft.block.Block;
import net.minecraft.client.render.RenderLayer;

public class PlusGeodesClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        for (GeodeSet set : ModContent.sets()) {
            for (Block stage : set.growthStages()) {
                BlockRenderLayerMap.INSTANCE.putBlock(stage, RenderLayer.getCutout());
            }
        }
    }
}
