package com.plusgeodes.block;

import net.minecraft.block.AmethystBlock;
import net.minecraft.block.AmethystClusterBlock;
import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.BuddingAmethystBlock;
import net.minecraft.fluid.Fluids;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.random.Random;

/**
 * Behaves like budding amethyst, but grows this geode's own buds and cluster.
 */
public class BuddingCrystalBlock extends AmethystBlock {
    private static final Direction[] DIRECTIONS = Direction.values();
    private static final int GROW_CHANCE = 5;

    private final Block smallBud;
    private final Block mediumBud;
    private final Block largeBud;
    private final Block cluster;

    public BuddingCrystalBlock(Block smallBud, Block mediumBud, Block largeBud, Block cluster, Settings settings) {
        super(settings);
        this.smallBud = smallBud;
        this.mediumBud = mediumBud;
        this.largeBud = largeBud;
        this.cluster = cluster;
    }

    @Override
    public void randomTick(BlockState state, ServerWorld world, BlockPos pos, Random random) {
        if (random.nextInt(GROW_CHANCE) != 0) {
            return;
        }
        Direction direction = DIRECTIONS[random.nextInt(DIRECTIONS.length)];
        BlockPos target = pos.offset(direction);
        BlockState targetState = world.getBlockState(target);

        Block next = null;
        if (BuddingAmethystBlock.canGrowIn(targetState)) {
            next = smallBud;
        } else if (isFacing(targetState, smallBud, direction)) {
            next = mediumBud;
        } else if (isFacing(targetState, mediumBud, direction)) {
            next = largeBud;
        } else if (isFacing(targetState, largeBud, direction)) {
            next = cluster;
        }

        if (next != null) {
            BlockState grown = next.getDefaultState()
                    .with(AmethystClusterBlock.FACING, direction)
                    .with(AmethystClusterBlock.WATERLOGGED, targetState.getFluidState().getFluid() == Fluids.WATER);
            world.setBlockState(target, grown);
        }
    }

    private static boolean isFacing(BlockState state, Block block, Direction direction) {
        return state.isOf(block) && state.get(AmethystClusterBlock.FACING) == direction;
    }
}
