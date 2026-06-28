package com.guesslang.preprocess;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * Preprocessing configuration parsed from preprocess_config.json.
 */
public final class PreprocessConfig {

    public static final boolean DEFAULT_LOWERCASE = true;
    public static final boolean DEFAULT_STRIP_PUNCTUATION = false;
    public static final boolean DEFAULT_COLLAPSE_WHITESPACE = true;
    public static final String DEFAULT_SPLIT = "whitespace";
    public static final int DEFAULT_NGRAMS = 1;
    public static final boolean DEFAULT_INCLUDE_ALL_NGRAMS = true;
    public static final String DEFAULT_OOV_BEHAVIOR = "ignore";
    public static final String DEFAULT_TF_MODE = "raw";
    public static final boolean DEFAULT_L2_NORMALIZE = false;

    private final boolean lowercase;
    private final boolean stripPunctuation;
    private final boolean collapseWhitespace;
    private final String split;       // "whitespace" | "regex"
    private final String splitRegex;
    private final int ngrams;
    private final boolean includeAllNgrams;
    private final String oovBehavior; // "ignore" | "bucket"
    private final String oovToken;   // token string when bucket
    private final String tfMode;     // "raw" | "normalized"
    private final boolean l2Normalize;

    public PreprocessConfig(boolean lowercase, boolean stripPunctuation, boolean collapseWhitespace,
                            String split, String splitRegex, int ngrams, boolean includeAllNgrams,
                            String oovBehavior, String oovToken, String tfMode, boolean l2Normalize) {
        this.lowercase = lowercase;
        this.stripPunctuation = stripPunctuation;
        this.collapseWhitespace = collapseWhitespace;
        this.split = split == null ? DEFAULT_SPLIT : split;
        this.splitRegex = splitRegex;
        this.ngrams = ngrams;
        this.includeAllNgrams = includeAllNgrams;
        this.oovBehavior = oovBehavior == null ? DEFAULT_OOV_BEHAVIOR : oovBehavior;
        this.oovToken = oovToken;
        this.tfMode = tfMode == null ? DEFAULT_TF_MODE : tfMode;
        this.l2Normalize = l2Normalize;
    }

    public static PreprocessConfig fromJson(JsonNode root) {
        // "standardize" is the Keras TextVectorization key; map it to our flags
        boolean lowercase = DEFAULT_LOWERCASE;
        boolean stripPunctuation = DEFAULT_STRIP_PUNCTUATION;
        if (root.has("standardize")) {
            String std = root.get("standardize").asText();
            lowercase = std.contains("lower");
            stripPunctuation = std.contains("strip_punctuation");
        }
        if (root.has("lowercase")) lowercase = root.get("lowercase").asBoolean();
        if (root.has("strip_punctuation")) stripPunctuation = root.get("strip_punctuation").asBoolean();
        boolean collapseWhitespace = root.has("collapse_whitespace") ? root.get("collapse_whitespace").asBoolean() : DEFAULT_COLLAPSE_WHITESPACE;
        String split = root.has("split") ? root.get("split").asText() : DEFAULT_SPLIT;
        String splitRegex = root.has("split_regex") ? root.get("split_regex").asText() : null;
        int ngrams = root.has("ngrams") ? root.get("ngrams").asInt(1) : DEFAULT_NGRAMS;
        boolean includeAllNgrams = root.has("include_all_ngrams") ? root.get("include_all_ngrams").asBoolean(true) : DEFAULT_INCLUDE_ALL_NGRAMS;
        // Support both custom keys and Keras special_tokens block
        String oovBehavior = root.has("oov_behavior") ? root.get("oov_behavior").asText() : DEFAULT_OOV_BEHAVIOR;
        String oovToken = root.has("oov_token") ? root.get("oov_token").asText() : null;
        if (root.has("special_tokens")) {
            JsonNode st = root.get("special_tokens");
            if (oovToken == null && st.has("oov_tfidf")) {
                oovToken = st.get("oov_tfidf").asText();
                oovBehavior = "bucket";
            }
        }
        String tfMode = root.has("tf_mode") ? root.get("tf_mode").asText() : DEFAULT_TF_MODE;
        boolean l2Normalize = root.has("l2_normalize") ? root.get("l2_normalize").asBoolean() : DEFAULT_L2_NORMALIZE;

        return new PreprocessConfig(lowercase, stripPunctuation, collapseWhitespace,
                split, splitRegex, ngrams, includeAllNgrams, oovBehavior, oovToken, tfMode, l2Normalize);
    }

    public boolean isLowercase() { return lowercase; }
    public boolean isStripPunctuation() { return stripPunctuation; }
    public boolean isCollapseWhitespace() { return collapseWhitespace; }
    public String getSplit() { return split; }
    public String getSplitRegex() { return splitRegex; }
    public int getNgrams() { return ngrams; }
    public boolean isIncludeAllNgrams() { return includeAllNgrams; }
    public String getOovBehavior() { return oovBehavior; }
    public String getOovToken() { return oovToken; }
    public String getTfMode() { return tfMode; }
    public boolean isL2Normalize() { return l2Normalize; }
}
