package com.plusgeodes.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.AmethystBlock;
import net.minecraft.world.level.block.AmethystClusterBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.BuddingAmethystBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;

/**
 * Behaves like budding amethyst, but grows this geode's own buds and cluster.
 */
public class BuddingCrystalBlock extends AmethystBlock {
    private static final Direction[] DIRECTIONS = Direction.values();

    private final Block smallBud;
    private final Block mediumBud;
    private final Block largeBud;
    private final Block cluster;

    public BuddingCrystalBlock(Block smallBud, Block mediumBud, Block largeBud, Block cluster, Properties properties) {
        super(properties);
        this.smallBud = smallBud;
        this.mediumBud = mediumBud;
        this.largeBud = largeBud;
        this.cluster = cluster;
    }

    @Override
    protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        if (random.nextInt(BuddingAmethystBlock.GROWTH_CHANCE) != 0) {
            return;
        }
        Direction direction = DIRECTIONS[random.nextInt(DIRECTIONS.length)];
        BlockPos target = pos.relative(direction);
        BlockState targetState = level.getBlockState(target);

        Block next = null;
        if (BuddingAmethystBlock.canClusterGrowAtState(targetState)) {
            next = smallBud;
        } else if (isFacing(targetState, smallBud, direction)) {
            next = mediumBud;
        } else if (isFacing(targetState, mediumBud, direction)) {
            next = largeBud;
        } else if (isFacing(targetState, largeBud, direction)) {
            next = cluster;
        }

        if (next != null) {
            BlockState grown = next.defaultBlockState()
                    .setValue(AmethystClusterBlock.FACING, direction)
                    .setValue(AmethystClusterBlock.WATERLOGGED, targetState.getFluidState().is(Fluids.WATER));
            level.setBlockAndUpdate(target, grown);
        }
    }

    private static boolean isFacing(BlockState state, Block block, Direction direction) {
        return state.is(block) && state.getValue(AmethystClusterBlock.FACING) == direction;
    }
}
