package com.guesslang.preprocess;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * TF-IDF vectorizer matching preprocess_config.json. Deterministic and avoids heavy allocations.
 * Output is a dense float[] of length vocabSize.
 */
public final class TfidfVectorizer {

    // Punctuation to remove: \p{Punct} minus keep _ # +
    private static final Pattern PUNCT_TO_STRIP = Pattern.compile("[\\p{Punct}&&[^_#+]]");

    private final PreprocessConfig config;
    private final List<String> vocab;
    private final float[] idf;
    private final Map<String, Integer> vocabIndex;
    private final int oovIndex; // -1 if no bucket, else index of oov_token

    public TfidfVectorizer(PreprocessConfig config, List<String> vocab, float[] idf) {
        if (vocab.size() != idf.length) {
            throw new IllegalArgumentException("vocab size " + vocab.size() + " != idf length " + idf.length);
        }
        this.config = config;
        this.vocab = vocab;
        this.idf = idf;
        this.vocabIndex = new HashMap<>(vocab.size());
        for (int i = 0; i < vocab.size(); i++) {
            vocabIndex.put(vocab.get(i), i);
        }
        int oov = -1;
        if ("bucket".equals(config.getOovBehavior()) && config.getOovToken() != null) {
            Integer idx = vocabIndex.get(config.getOovToken());
            if (idx != null) oov = idx;
        }
        this.oovIndex = oov;
    }

    public int getVocabSize() {
        return vocab.size();
    }

    /**
     * Returns a new dense float[] of length vocabSize. Caller can reuse by passing existing array (same length).
     */
    public float[] vectorize(String text) {
        return vectorize(text, new float[vocab.size()]);
    }

    public float[] vectorize(String text, float[] out) {
        if (out.length != vocab.size()) {
            throw new IllegalArgumentException("output array length must equal vocab size");
        }
        java.util.Arrays.fill(out, 0f);

        String normalized = normalize(text);
        List<String> tokens = tokenize(normalized);
        List<String> ngramTokens = buildNgrams(tokens);

        int totalTokens = ngramTokens.size();
        Map<Integer, Integer> counts = new HashMap<>();
        for (String t : ngramTokens) {
            int idx = tokenToIndex(t);
            if (idx >= 0) {
                counts.merge(idx, 1, Integer::sum);
            }
        }

        boolean normalizedTf = "normalized".equals(config.getTfMode()) && totalTokens > 0;
        for (Map.Entry<Integer, Integer> e : counts.entrySet()) {
            int idx = e.getKey();
            float tf = e.getValue();
            if (normalizedTf) tf /= totalTokens;
            out[idx] = tf * idf[idx];
        }

        if (config.isL2Normalize()) {
            float norm = 0f;
            for (float v : out) norm += v * v;
            norm = (float) Math.sqrt(norm);
            if (norm > 0f) {
                for (int i = 0; i < out.length; i++) out[i] /= norm;
            }
        }
        return out;
    }

    private String normalize(String text) {
        if (text == null) return "";
        if (config.isLowercase()) text = text.toLowerCase();
        if (config.isStripPunctuation()) text = PUNCT_TO_STRIP.matcher(text).replaceAll("");
        if (config.isCollapseWhitespace()) text = text.replaceAll("\\s+", " ").trim();
        return text;
    }

    private List<String> tokenize(String text) {
        String[] parts;
        if ("regex".equals(config.getSplit()) && config.getSplitRegex() != null) {
            parts = text.split(config.getSplitRegex());
        } else {
            parts = text.trim().isEmpty() ? new String[0] : text.split("\\s+");
        }
        List<String> list = new ArrayList<>(parts.length);
        for (String s : parts) {
            String t = s.trim();
            if (!t.isEmpty()) list.add(t);
        }
        return list;
    }

    private List<String> buildNgrams(List<String> tokens) {
        int n = config.getNgrams();
        boolean includeAll = config.isIncludeAllNgrams();
        List<String> result = new ArrayList<>();
        if (n <= 1) {
            result.addAll(tokens);
            return result;
        }
        for (int len = includeAll ? 1 : n; len <= n; len++) {
            for (int i = 0; i <= tokens.size() - len; i++) {
                StringBuilder sb = new StringBuilder();
                for (int j = 0; j < len; j++) {
                    if (j > 0) sb.append(' ');
                    sb.append(tokens.get(i + j));
                }
                result.add(sb.toString());
            }
        }
        return result;
    }

    private int tokenToIndex(String token) {
        Integer idx = vocabIndex.get(token);
        if (idx != null) return idx;
        return oovIndex;
    }
}
