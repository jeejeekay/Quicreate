package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * A tower of evenly spaced strands twisting around an empty centre line, like a double helix.
 * The same code places towers during world generation and from {@code /qshape helix}, so a shape
 * tested with the command is exactly what generates.
 */
public class HelixFeature extends Feature<HelixConfiguration> {

    private static final double STEP = 0.2;

    public HelixFeature(Codec<HelixConfiguration> codec) {
        super(codec);
    }

    @Override
    public boolean place(FeaturePlaceContext<HelixConfiguration> context) {
        HelixConfiguration config = context.config();
        RandomSource random = context.random();
        WorldGenLevel level = context.level();
        BlockPos base = context.origin().below(config.sink());

        Map<BlockPos, Boolean> shape = shape(config, random);
        boolean placed = false;
        for (Map.Entry<BlockPos, Boolean> entry : shape.entrySet()) {
            BlockPos pos = base.offset(entry.getKey());
            if (!level.ensureCanWrite(pos) || pos.getY() < level.getMinBuildHeight() || pos.getY() >= level.getMaxBuildHeight()) {
                continue;
            }
            BlockState existing = level.getBlockState(pos);
            if (!existing.isAir() && !existing.canBeReplaced() && !existing.is(BlockTags.SNOW) && entry.getKey().getY() >= config.sink()) {
                continue; // don't cut through terrain above the base
            }
            BlockState state = (entry.getValue() ? config.rungBlock() : config.blocks()).getState(random, pos);
            level.setBlock(pos, state, Block.UPDATE_CLIENTS);
            placed = true;
        }
        if (placed && !config.inhabitants().isEmpty()) {
            placeInhabitants(level, base, shape, config, random);
        }
        return placed;
    }

    /** Puts the tower's mobs on strand blocks in its top 40% that have two free blocks above them. */
    private static void placeInhabitants(WorldGenLevel level, BlockPos base, Map<BlockPos, Boolean> shape, HelixConfiguration config, RandomSource random) {
        int top = 0;
        for (BlockPos offset : shape.keySet()) {
            top = Math.max(top, offset.getY());
        }
        List<BlockPos> perches = new ArrayList<>();
        for (BlockPos offset : shape.keySet()) {
            if (offset.getY() >= top * 0.6 && !shape.containsKey(offset.above()) && !shape.containsKey(offset.above(2))) {
                perches.add(offset);
            }
        }
        if (perches.isEmpty()) {
            return;
        }
        for (HelixInhabitant inhabitant : config.inhabitants()) {
            if (random.nextFloat() >= inhabitant.chance()) {
                continue;
            }
            int count = inhabitant.count().sample(random);
            for (int i = 0; i < count; i++) {
                BlockPos stand = base.offset(perches.get(random.nextInt(perches.size()))).above();
                if (!level.ensureCanWrite(stand) || !level.getBlockState(stand).isAir() || !level.getBlockState(stand.above()).isAir()) {
                    continue;
                }
                Entity entity = inhabitant.entity().create(level.getLevel());
                if (!(entity instanceof Mob mob)) {
                    if (entity != null) {
                        entity.discard();
                    }
                    continue;
                }
                mob.moveTo(stand.getX() + 0.5, stand.getY(), stand.getZ() + 0.5, random.nextFloat() * 360.0F, 0.0F);
                if (inhabitant.finalizeSpawn()) {
                    mob.finalizeSpawn(level, level.getCurrentDifficultyAt(stand), MobSpawnType.STRUCTURE, null, null);
                }
                mob.setPersistenceRequired();
                level.addFreshEntityWithPassengers(mob);
            }
        }
    }

    /** Block offsets of one tower; the value is true for rung blocks. */
    public static Map<BlockPos, Boolean> shape(HelixConfiguration config, RandomSource random) {
        int height = config.height().sample(random);
        float radius = config.radius().sample(random);
        float turns = config.turns().sample(random);
        int strands = config.strands();
        double phase = random.nextDouble() * Mth.TWO_PI;
        double direction = random.nextBoolean() ? 1 : -1;
        double half = config.strandThickness() / 2.0;

        Map<BlockPos, Boolean> blocks = new HashMap<>();
        for (int s = 0; s < strands; s++) {
            for (double y = 0; y < height; y += STEP) {
                double[] c = centre(y, s, height, radius, turns, strands, config.taper(), phase, direction);
                disk(blocks, c[0], y, c[1], half, false);
            }
        }
        if (config.rungSpacing() > 0 && strands > 1) {
            for (int y = config.rungSpacing(); y < height; y += config.rungSpacing()) {
                for (int s = 0; s < strands; s++) {
                    double[] a = centre(y, s, height, radius, turns, strands, config.taper(), phase, direction);
                    double[] b = centre(y, (s + 1) % strands, height, radius, turns, strands, config.taper(), phase, direction);
                    for (double t = 0; t <= 1.0; t += 0.05) {
                        disk(blocks, a[0] + (b[0] - a[0]) * t, y, a[1] + (b[1] - a[1]) * t, 0.5, true);
                    }
                    if (strands == 2) {
                        break; // one rung already joins both strands
                    }
                }
            }
        }
        return blocks;
    }

    private static double[] centre(double y, int strand, int height, float radius, float turns, int strands, float taper, double phase, double direction) {
        double f = y / height;
        double r = radius * (1.0 - taper * f);
        double angle = direction * Mth.TWO_PI * turns * f + strand * Mth.TWO_PI / strands + phase;
        return new double[]{r * Math.cos(angle), r * Math.sin(angle)};
    }

    private static void disk(Map<BlockPos, Boolean> blocks, double cx, double y, double cz, double half, boolean rung) {
        int reach = (int) Math.ceil(half + 1);
        int bx = (int) Math.round(cx);
        int bz = (int) Math.round(cz);
        int by = (int) Math.round(y);
        double limit = (half + 0.2) * (half + 0.2);
        for (int dx = -reach; dx <= reach; dx++) {
            for (int dz = -reach; dz <= reach; dz++) {
                int x = bx + dx;
                int z = bz + dz;
                if ((x - cx) * (x - cx) + (z - cz) * (z - cz) <= limit) {
                    // Strands win over rungs where they overlap.
                    blocks.merge(new BlockPos(x, by, z), rung, (old, now) -> old && now);
                }
            }
        }
    }
}
