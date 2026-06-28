package com.guesslang.selftest;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.guesslang.infer.DjlOnnxEngine;
import com.guesslang.infer.ModelInput;
import com.guesslang.post.OutputFormatter;
import com.guesslang.preprocess.TfidfVectorizer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Runs golden tests from a JSON file. Each test has name, text, expected_top1.
 * Exits with non-zero on any failure.
 */
public final class SelfTester {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    public static class TestCase {
        final String name;
        final String text;
        final String expectedTop1;

        TestCase(String name, String text, String expectedTop1) {
            this.name = name;
            this.text = text;
            this.expectedTop1 = expectedTop1;
        }
    }

    /**
     * Load test cases from JSON. Supports either { "tests": [ { "name", "text", "expected_top1" }, ... ] }
     * or a bare array [ { "name", "text", "expected_top1" }, ... ].
     */
    public static List<TestCase> loadTests(Path path) throws IOException {
        String content = Files.readString(path);
        JsonNode root = MAPPER.readTree(content);
        JsonNode array = root.has("tests") ? root.get("tests") : root;
        if (!array.isArray()) {
            throw new IOException("golden_tests.json must be an array or { \"tests\": [ ... ] }");
        }
        List<TestCase> out = new ArrayList<>();
        for (JsonNode obj : array) {
            String name = obj.has("name") ? obj.get("name").asText() : ("test-" + out.size());
            String text = obj.has("text") ? obj.get("text").asText() : "";
            String expectedTop1 = obj.has("expected_top1") ? obj.get("expected_top1").asText() : null;
            if (expectedTop1 == null) {
                throw new IOException("Each test must have expected_top1: " + name);
            }
            out.add(new TestCase(name, text, expectedTop1));
        }
        return out;
    }

    /**
     * Run all tests using the given vectorizer, deep vocab, and engine. Returns number of failures.
     */
    public static int run(TfidfVectorizer vectorizer, Map<String, Integer> deepVocab,
                          DjlOnnxEngine engine, List<TestCase> tests) {
        int unkIdx = deepVocab.getOrDefault("[UNK]", 1);
        int failed = 0;
        for (TestCase t : tests) {
            try {
                float[] vec = vectorizer.vectorize(t.text);
                int[] deepSeq = buildDeepInput(t.text, deepVocab, unkIdx, 512);
                float[] probs = engine.predict(new ModelInput(deepSeq, vec));
                List<String> labels = engine.getLabels();
                String top1 = getTop1(probs, labels);
                boolean pass = t.expectedTop1.equals(top1);
                if (pass) {
                    System.out.println("PASS " + t.name + " -> " + top1);
                } else {
                    System.err.println("FAIL " + t.name + " expected_top1=" + t.expectedTop1 + " got " + top1);
                    failed++;
                }
            } catch (Exception e) {
                System.err.println("FAIL " + t.name + " " + e.getMessage());
                failed++;
            }
        }
        return failed;
    }

    private static String getTop1(float[] probs, List<String> labels) {
        int best = 0;
        for (int i = 1; i < probs.length; i++) {
            if (probs[i] > probs[best]) best = i;
        }
        return labels.get(best);
    }

    private static int[] buildDeepInput(String text, Map<String, Integer> deepVocab, int unkIdx, int maxLen) {
        String normalized = text.toLowerCase().replaceAll("[\\p{Punct}&&[^_#+]]", "").replaceAll("\\s+", " ").trim();
        String[] tokens = normalized.isEmpty() ? new String[0] : normalized.split("\\s+");
        int[] seq = new int[maxLen];
        for (int i = 0; i < Math.min(tokens.length, maxLen); i++) {
            seq[i] = deepVocab.getOrDefault(tokens[i], unkIdx);
        }
        return seq;
    }
}
