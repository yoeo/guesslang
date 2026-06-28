package com.guesslang;

import com.guesslang.cli.CliArgs;
import com.guesslang.io.ArtifactLoader;
import com.guesslang.infer.DjlOnnxEngine;
import com.guesslang.infer.ModelInput;
import com.guesslang.post.OutputFormatter;
import com.guesslang.preprocess.PreprocessConfig;
import com.guesslang.preprocess.TfidfVectorizer;
import com.guesslang.selftest.SelfTester;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Guesslang-style ONNX CLI: read text from file or stdin, output JSON language probabilities.
 */
public final class Main {

    public static void main(String[] args) {
        try {
            CliArgs cli = CliArgs.parse(args);
            if (cli.isHelp()) {
                CliArgs.printHelp();
                return;
            }

            Path modelsDir = Path.of(cli.getModelsDir());
            if (!Files.isDirectory(modelsDir)) {
                System.err.println("Models directory not found: " + modelsDir.toAbsolutePath());
                System.exit(1);
            }

            ArtifactLoader loader = new ArtifactLoader(modelsDir);
            loader.getOnnxPath(); // fail fast if ONNX missing

            List<String> labels = loader.loadLabels();
            List<String> vocab = loader.loadVocab();
            float[] idf = loader.loadIdf();
            PreprocessConfig preprocessConfig = loader.loadPreprocessConfig();
            ArtifactLoader.ModelIoConfig modelIoConfig = loader.loadModelIoConfig();
            Map<String, Integer> deepVocab = loader.loadDeepVocab();

            if (vocab.size() != idf.length) {
                System.err.println("vocab size " + vocab.size() + " != idf length " + idf.length);
                System.exit(1);
            }

            TfidfVectorizer vectorizer = new TfidfVectorizer(preprocessConfig, vocab, idf);

            try (DjlOnnxEngine engine = new DjlOnnxEngine(modelsDir, labels, modelIoConfig)) {
                if (cli.isPrintIo()) {
                    engine.printModelIo();
                }

                if (cli.getSelftestPath() != null) {
                    Path testPath = loader.resolveSelftestPath(cli.getSelftestPath());
                    if (!Files.isRegularFile(testPath)) {
                        System.err.println("Selftest file not found: " + testPath.toAbsolutePath());
                        System.exit(1);
                    }
                    List<SelfTester.TestCase> tests = SelfTester.loadTests(testPath);
                    int failed = SelfTester.run(vectorizer, deepVocab, engine, tests);
                    System.out.println("Selftest: " + (tests.size() - failed) + " passed, " + failed + " failed");
                    System.exit(failed > 0 ? 1 : 0);
                }

                String text = readInput(cli.getFilePath());
                float[] vec = vectorizer.vectorize(text);
                int[] deepSeq = buildDeepInput(text, deepVocab, 512);
                float[] probs = engine.predict(new ModelInput(deepSeq, vec));
                String json = OutputFormatter.format(probs, labels, cli.getTopK(), cli.isSort());
                System.out.println(json);
            }
        } catch (IllegalArgumentException e) {
            System.err.println("Arguments: " + e.getMessage());
            System.exit(1);
        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }

    private static String readInput(String filePath) throws IOException {
        if (filePath != null) {
            return Files.readString(Path.of(filePath), StandardCharsets.UTF_8);
        }
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            return reader.lines().collect(Collectors.joining("\n"));
        }
    }

    /**
     * Tokenize text to a fixed-length int[] for the deep input.
     * Mirrors Keras TextVectorization(standardize="lower_and_strip_punctuation", split="whitespace", output_mode="int").
     * Pads with 0 (mask token), truncates at maxLen.
     */
    static int[] buildDeepInput(String text, Map<String, Integer> deepVocab, int maxLen) {
        int unkIdx = deepVocab.getOrDefault("[UNK]", 1);
        // lower_and_strip_punctuation: lowercase then remove all punctuation except _ # +
        String normalized = text.toLowerCase().replaceAll("[\\p{Punct}&&[^_#+]]", "").replaceAll("\\s+", " ").trim();
        String[] tokens = normalized.isEmpty() ? new String[0] : normalized.split("\\s+");
        int[] seq = new int[maxLen];
        for (int i = 0; i < Math.min(tokens.length, maxLen); i++) {
            seq[i] = deepVocab.getOrDefault(tokens[i], unkIdx);
        }
        return seq;
    }
}
