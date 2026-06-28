package com.guesslang.infer;

import ai.djl.inference.Predictor;
import ai.djl.ndarray.NDArray;
import ai.djl.ndarray.NDList;
import ai.djl.ndarray.NDManager;
import ai.djl.ndarray.types.Shape;
import ai.djl.repository.zoo.Criteria;
import ai.djl.repository.zoo.ZooModel;
import ai.djl.translate.NoBatchifyTranslator;
import ai.djl.translate.TranslateException;
import ai.djl.translate.TranslatorContext;
import com.guesslang.io.ArtifactLoader;
import com.guesslang.post.Softmax;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * DJL + ONNX Runtime inference engine. Loads ONNX once and runs a forward pass.
 * Supports wide-and-deep models with two named inputs: deep_input (int32) and wide_input (float32).
 */
public final class DjlOnnxEngine implements AutoCloseable {

    private static final String ENGINE = "OnnxRuntime";

    private final ZooModel<ModelInput, float[]> model;
    private final ArtifactLoader.ModelIoConfig ioConfig;
    private final List<String> labels;

    public DjlOnnxEngine(Path modelsDir, List<String> labels, ArtifactLoader.ModelIoConfig ioConfig) throws IOException {
        this.labels = labels;
        this.ioConfig = ioConfig;

        Path onnxPath = modelsDir.resolve("guesslang.onnx");
        if (!onnxPath.toFile().isFile()) {
            throw new IOException("ONNX model not found: " + onnxPath.toAbsolutePath());
        }

        Criteria<ModelInput, float[]> criteria = Criteria.builder()
                .setTypes(ModelInput.class, float[].class)
                .optModelPath(modelsDir)
                .optModelName("guesslang")
                .optEngine(ENGINE)
                .optTranslator(new WideDeepTranslator())
                .build();

        try {
            this.model = criteria.loadModel();
        } catch (Exception e) {
            throw new IOException("Failed to load ONNX model from " + modelsDir + ": " + e.getMessage(), e);
        }
    }

    /**
     * Run inference. Accepts both deep (int32 token sequence) and wide (float32 TF-IDF) inputs.
     * Returns probabilities (softmax is applied if model_io.json declares output_is_logits=true).
     */
    public List<String> getLabels() {
        return labels;
    }

    public float[] predict(ModelInput input) throws TranslateException {
        try (Predictor<ModelInput, float[]> predictor = model.newPredictor()) {
            float[] raw = predictor.predict(input);
            if (raw.length != labels.size()) {
                throw new IllegalStateException(
                        "Model output length " + raw.length + " does not match labels length " + labels.size() +
                                ". Check labels.json and model output.");
            }
            if (ioConfig != null && ioConfig.isOutputIsLogits()) {
                Softmax.applyInPlace(raw);
            }
            return raw;
        }
    }

    /**
     * Best-effort: print model input/output names and shapes if available via DJL/ONNX metadata.
     */
    public void printModelIo() {
        try {
            ai.djl.nn.Block block = model.getBlock();
            Object inDesc = block.describeInput();
            Object outDesc = null;
            // Some DJL versions expose output description APIs differently.
            try {
                outDesc = block.getClass().getMethod("describeOutput").invoke(block);
            } catch (ReflectiveOperationException ignored) {
                // Keep best-effort behavior without hard dependency on a specific DJL method.
            }
            System.err.println("Model inputs (best-effort): " + (inDesc != null ? inDesc : "use model_io.json or inspect ONNX"));
            System.err.println("Model outputs (best-effort): " + (outDesc != null ? outDesc : "use model_io.json or inspect ONNX"));
        } catch (Exception e) {
            System.err.println("Could not infer model I/O from DJL (use model_io.json): " + e.getMessage());
        }
    }

    @Override
    public void close() {
        if (model != null) {
            model.close();
        }
    }

    private static final class WideDeepTranslator implements NoBatchifyTranslator<ModelInput, float[]> {
        @Override
        public NDList processInput(TranslatorContext ctx, ModelInput input) {
            NDManager manager = ctx.getNDManager();
            NDArray deepArray = manager.create(input.getDeepInput(), new Shape(1, input.getDeepInput().length));
            deepArray.setName("deep_input");
            NDArray wideArray = manager.create(input.getWideInput(), new Shape(1, input.getWideInput().length));
            wideArray.setName("wide_input");
            return new NDList(deepArray, wideArray);
        }

        @Override
        public float[] processOutput(TranslatorContext ctx, NDList list) {
            if (list.isEmpty()) throw new IllegalStateException("Model returned empty output");
            return list.get(0).toFloatArray();
        }
    }
}
