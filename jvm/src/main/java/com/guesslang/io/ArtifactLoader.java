package com.guesslang.io;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.guesslang.preprocess.PreprocessConfig;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Loads all required artifacts from the models directory.
 */
public final class ArtifactLoader {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final String ONNX_FILE = "guesslang.onnx";
    private static final String LABELS_JSON = "labels.json";
    private static final String VOCAB_JSON = "vocab.json";
    private static final String IDF_JSON = "idf.json";
    private static final String PREPROCESS_CONFIG_JSON = "preprocess_config.json";
    private static final String MODEL_IO_JSON = "model_io.json";
    private static final String GOLDEN_TESTS_JSON = "golden_tests.json";
    private static final String DEEP_VOCAB_JSON = "deep_vocab.json";

    private final Path modelsDir;

    public ArtifactLoader(Path modelsDir) {
        this.modelsDir = modelsDir;
    }

    public Path getModelsDir() {
        return modelsDir;
    }

    public Path getOnnxPath() {
        Path p = modelsDir.resolve(ONNX_FILE);
        if (!Files.isRegularFile(p)) {
            throw new IllegalStateException("Missing model file: " + p.toAbsolutePath() + " (expected " + ONNX_FILE + ")");
        }
        return p;
    }

    public List<String> loadLabels() throws IOException {
        Path p = modelsDir.resolve(LABELS_JSON);
        if (!Files.isRegularFile(p)) {
            throw new IOException("Missing labels file: " + p.toAbsolutePath());
        }
        return MAPPER.readValue(Files.readString(p), new TypeReference<List<String>>() {});
    }

    public List<String> loadVocab() throws IOException {
        Path p = modelsDir.resolve(VOCAB_JSON);
        if (!Files.isRegularFile(p)) {
            throw new IOException("Missing vocab file: " + p.toAbsolutePath());
        }
        return MAPPER.readValue(Files.readString(p), new TypeReference<List<String>>() {});
    }

    public float[] loadIdf() throws IOException {
        Path p = modelsDir.resolve(IDF_JSON);
        if (!Files.isRegularFile(p)) {
            throw new IOException("Missing idf file: " + p.toAbsolutePath());
        }
        List<Number> list = MAPPER.readValue(Files.readString(p), new TypeReference<List<Number>>() {});
        float[] idf = new float[list.size()];
        for (int i = 0; i < list.size(); i++) {
            idf[i] = list.get(i).floatValue();
        }
        return idf;
    }

    public PreprocessConfig loadPreprocessConfig() throws IOException {
        Path p = modelsDir.resolve(PREPROCESS_CONFIG_JSON);
        if (!Files.isRegularFile(p)) {
            throw new IOException("Missing preprocess config: " + p.toAbsolutePath());
        }
        return PreprocessConfig.fromJson(MAPPER.readTree(Files.readString(p)));
    }

    /**
     * Load model I/O config if present; returns null if file missing.
     */
    public ModelIoConfig loadModelIoConfig() {
        Path p = modelsDir.resolve(MODEL_IO_JSON);
        if (!Files.isRegularFile(p)) {
            return null;
        }
        try {
            JsonNode root = MAPPER.readTree(Files.readString(p));
            String inputName = root.has("input_name") ? root.get("input_name").asText() : null;
            String outputName = root.has("output_name") ? root.get("output_name").asText() : null;
            boolean outputIsLogits = root.has("output_is_logits") && root.get("output_is_logits").asBoolean();
            return new ModelIoConfig(inputName, outputName, outputIsLogits);
        } catch (IOException e) {
            throw new UncheckedIOException("Failed to read " + MODEL_IO_JSON, e);
        }
    }

    /**
     * Loads deep_vocab.json as a token-to-index map. The file may be either:
     *   - a JSON object { "token": index, ... }
     *   - a JSON array [ "token0", "token1", ... ] (index = position)
     */
    public Map<String, Integer> loadDeepVocab() throws IOException {
        Path p = modelsDir.resolve(DEEP_VOCAB_JSON);
        if (!Files.isRegularFile(p)) {
            throw new IOException("Missing deep vocab file: " + p.toAbsolutePath());
        }
        String content = Files.readString(p);
        JsonNode root = MAPPER.readTree(content);
        Map<String, Integer> map = new java.util.LinkedHashMap<>();
        if (root.isObject()) {
            root.fields().forEachRemaining(e -> map.put(e.getKey(), e.getValue().asInt()));
        } else if (root.isArray()) {
            for (int i = 0; i < root.size(); i++) {
                map.put(root.get(i).asText(), i);
            }
        } else {
            throw new IOException("deep_vocab.json must be a JSON object or array");
        }
        return map;
    }

    public Path getGoldenTestsPath() {
        return modelsDir.resolve(GOLDEN_TESTS_JSON);
    }

    /**
     * Resolve selftest path: if absolute or relative path given, use it; otherwise treat as filename in models dir.
     */
    public Path resolveSelftestPath(String selftestPath) {
        Path p = Path.of(selftestPath);
        if (p.isAbsolute() || selftestPath.contains("/") || selftestPath.contains("\\")) {
            return p;
        }
        return modelsDir.resolve(selftestPath);
    }

    public static final class ModelIoConfig {
        private final String inputName;
        private final String outputName;
        private final boolean outputIsLogits;

        public ModelIoConfig(String inputName, String outputName, boolean outputIsLogits) {
            this.inputName = inputName;
            this.outputName = outputName;
            this.outputIsLogits = outputIsLogits;
        }

        public String getInputName() { return inputName; }
        public String getOutputName() { return outputName; }
        public boolean isOutputIsLogits() { return outputIsLogits; }
    }
}
