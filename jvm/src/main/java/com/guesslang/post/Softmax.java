package com.guesslang.post;

/**
 * Numerically stable softmax over a float array (in-place or copy).
 */
public final class Softmax {

    private Softmax() {}

    /**
     * Applies softmax in-place. Values are overwritten with probabilities that sum to 1.
     */
    public static void applyInPlace(float[] x) {
        if (x == null || x.length == 0) return;
        float max = x[0];
        for (int i = 1; i < x.length; i++) {
            if (x[i] > max) max = x[i];
        }
        double sum = 0;
        for (int i = 0; i < x.length; i++) {
            double exp = Math.exp(x[i] - max);
            x[i] = (float) exp;
            sum += exp;
        }
        if (sum > 0) {
            for (int i = 0; i < x.length; i++) {
                x[i] /= sum;
            }
        }
    }

    /**
     * Returns a new float[] with softmax applied (original unchanged).
     */
    public static float[] apply(float[] x) {
        if (x == null) return null;
        float[] out = x.clone();
        applyInPlace(out);
        return out;
    }
}
