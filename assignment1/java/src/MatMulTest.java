import java.util.Arrays;
import java.util.Random;

/** Correctness tests for the Java implementation (no external libraries needed). */
public class MatMulTest {
    private static int failures = 0;

    private static void check(String name, boolean ok) {
        System.out.println((ok ? "PASS  " : "FAIL  ") + name);
        if (!ok) failures++;
    }

    private static double[][] identity(int n) {
        double[][] m = new double[n][n];
        for (int i = 0; i < n; i++) m[i][i] = 1.0;
        return m;
    }

    private static double[][] random(int n, long seed) {
        Random rnd = new Random(seed);
        double[][] m = new double[n][n];
        for (double[] row : m) for (int j = 0; j < n; j++) row[j] = rnd.nextDouble();
        return m;
    }

    public static void main(String[] args) {
        double[][] a = {{1, 2}, {3, 4}};
        double[][] b = {{5, 6}, {7, 8}};
        check("known 2x2", Arrays.deepEquals(MatMul.multiply(a, b), new double[][]{{19, 22}, {43, 50}}));

        double[][] a3 = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        double[][] b3 = {{9, 8, 7}, {6, 5, 4}, {3, 2, 1}};
        double[][] e3 = {{30, 24, 18}, {84, 69, 54}, {138, 114, 90}};
        check("known 3x3", Arrays.deepEquals(MatMul.multiply(a3, b3), e3));

        double[][] r = random(7, 1);
        check("A x I = A", Arrays.deepEquals(MatMul.multiply(r, identity(7)), r));
        check("I x A = A", Arrays.deepEquals(MatMul.multiply(identity(7), r), r));

        double[][] z = new double[5][5];
        check("A x 0 = 0", Arrays.deepEquals(MatMul.multiply(random(5, 2), z), z));
        check("1x1", MatMul.multiply(new double[][]{{3}}, new double[][]{{4}})[0][0] == 12.0);
        check("checksum", MatMul.checksum(a) == 10.0);

        if (failures > 0) {
            System.out.println(failures + " test(s) failed");
            System.exit(1);
        }
        System.out.println("All Java tests passed");
    }
}
