package com.guesslang.infer;

/**
 * Holds both inputs required by the wide-and-deep ONNX model:
 *   deep_input  – int32 token-index sequence, length = deepSeqLen (e.g. 512), padded with 0
 *   wide_input  – float32 TF-IDF vector, length = vocabSize (e.g. 10000)
 */
public final class ModelInput {

    private final int[] deepInput;
    private final float[] wideInput;

    public ModelInput(int[] deepInput, float[] wideInput) {
        this.deepInput = deepInput;
        this.wideInput = wideInput;
    }

    public int[] getDeepInput() { return deepInput; }
    public float[] getWideInput() { return wideInput; }
}
