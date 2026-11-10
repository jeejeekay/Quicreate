package IGoByJake.quicreate.worldgen;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * A winding crack with a flat lava surface some way below the ground. The lava is sealed in on every
 * side but the top, so it never spills. Thin rock bridges can cross the crack at ground level.
 */
public class FissureFeature extends ShapedFeature<FissureConfiguration> {

    private static final double STEP = 0.5;
    private static final int[][] LAVA_SIDES = {{1, 0, 0}, {-1, 0, 0}, {0, 0, 1}, {0, 0, -1}, {0, -1, 0}};
    private static final int[][] WALL_SIDES = {{1, 0, 0}, {-1, 0, 0}, {0, 0, 1}, {0, 0, -1}};

    public FissureFeature(Codec<FissureConfiguration> codec) {
        super(codec);
    }

    private static long key(int x, int z) {
        return ((long) x << 32) ^ (z & 0xFFFFFFFFL);
    }

    @Override
    protected void build(FissureConfiguration config, RandomSource random, Ground ground, Shape shape) {
        int length = config.length().sample(random);
        double maxWidth = config.width().sample(random);
        int drop = config.depth().sample(random);
        int pool = config.lavaDepth().sample(random);
        int lavaTop = ground.at(0, 0) - drop;

        // Walk a wandering path, then centre it on the origin.
        int points = (int) (length / STEP) + 1;
        double[] px = new double[points];
        double[] pz = new double[points];
        double[] heading = new double[points];
        double x = 0;
        double z = 0;
        double h = random.nextDouble() * Mth.TWO_PI;
        double turn = 0;
        for (int i = 0; i < points; i++) {
            px[i] = x;
            pz[i] = z;
            heading[i] = h;
            turn = turn * 0.8 + (random.nextDouble() - 0.5) * config.wander() * 0.3;
            h += turn;
            x += Math.cos(h) * STEP;
            z += Math.sin(h) * STEP;
        }
        double mx = px[points / 2];
        double mz = pz[points / 2];

        Map<Long, Double> columns = new HashMap<>(); // column -> how deep its lava is, 0..1 of the full pool
        Set<Long> bridges = new HashSet<>();
        for (int i = 0; i < points; i++) {
            double f = points == 1 ? 0.5 : i / (double) (points - 1);
            double half = Math.max(0.6, maxWidth * 0.5 * Math.pow(Math.sin(Math.PI * f), 0.7));
            double cx = px[i] - mx;
            double cz = pz[i] - mz;
            for (int ix = (int) Math.floor(cx - half); ix <= (int) Math.ceil(cx + half); ix++) {
                for (int iz = (int) Math.floor(cz - half); iz <= (int) Math.ceil(cz + half); iz++) {
                    double dist = Math.sqrt((ix - cx) * (ix - cx) + (iz - cz) * (iz - cz));
                    if (dist <= half) {
                        double profile = (half / (maxWidth * 0.5)) * (1.0 - 0.5 * dist / half);
                        columns.merge(key(ix, iz), profile, Math::max);
                    }
                }
            }
            if (f > 0.15 && f < 0.85 && random.nextFloat() < config.bridgeChance() * STEP) {
                double sx = -Math.sin(heading[i]);
                double sz = Math.cos(heading[i]);
                for (double t = -half - 1; t <= half + 1; t += 0.3) {
                    bridges.add(key((int) Math.round(cx + sx * t), (int) Math.round(cz + sz * t)));
                }
            }
        }

        List<BlockPos> lavaCells = new ArrayList<>();
        List<BlockPos> airCells = new ArrayList<>();
        for (Map.Entry<Long, Double> column : columns.entrySet()) {
            int cx = (int) (column.getKey() >> 32);
            int cz = (int) (long) column.getKey();
            int g = ground.at(cx, cz);
            if (g <= lavaTop) {
                continue; // ground dips below the lava here; leave it so the lava stays sealed
            }
            boolean bridge = bridges.contains(column.getKey());
            for (int y = lavaTop + 1; y <= g + 1; y++) {
                if (bridge && y >= g - 1 && y <= g) {
                    continue;
                }
                shape.set(cx, y, cz, Shape.AIR, Shape.Mode.FORCE);
                airCells.add(new BlockPos(cx, y, cz));
            }
            if (bridge) {
                shape.set(cx, g, cz, config.lining(), Shape.Mode.FORCE);
                shape.set(cx, g - 1, cz, config.lining(), Shape.Mode.FORCE);
            }
            int poolDepth = Math.max(1, (int) Math.round(pool * Math.min(1.0, column.getValue())));
            for (int y = lavaTop - poolDepth + 1; y <= lavaTop; y++) {
                shape.set(cx, y, cz, config.lava(), Shape.Mode.FORCE);
                lavaCells.add(new BlockPos(cx, y, cz));
            }
        }

        // Seal the lava: every side and the floor is lining unless it's more of the fissure.
        for (BlockPos cell : lavaCells) {
            for (int[] side : LAVA_SIDES) {
                int nx = cell.getX() + side[0];
                int ny = cell.getY() + side[1];
                int nz = cell.getZ() + side[2];
                if (!shape.has(nx, ny, nz)) {
                    shape.setIfAbsent(nx, ny, nz, config.lining(), Shape.Mode.FORCE);
                }
            }
        }
        // Line some of the walls below ground level.
        for (BlockPos cell : airCells) {
            for (int[] side : WALL_SIDES) {
                int nx = cell.getX() + side[0];
                int nz = cell.getZ() + side[2];
                if (!shape.has(nx, cell.getY(), nz) && cell.getY() <= ground.at(nx, nz) && random.nextFloat() < config.liningChance()) {
                    shape.setIfAbsent(nx, cell.getY(), nz, config.lining(), Shape.Mode.FORCE);
                }
            }
        }
    }
}
