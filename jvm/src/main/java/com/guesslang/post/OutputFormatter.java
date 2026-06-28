package com.guesslang.post;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Formats model output (label -> probability) as JSON with optional top-k and sort.
 */
public final class OutputFormatter {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .enable(JsonGenerator.Feature.WRITE_BIGDECIMAL_AS_PLAIN)
            .disable(SerializationFeature.WRITE_DATE_KEYS_AS_TIMESTAMPS);

    /**
     * Builds label->probability and writes JSON to the given writer.
     * If topK is non-null, only the top-k entries by probability are included.
     * If sort is true, entries are sorted by probability descending; otherwise label order is preserved.
     */
    public static void format(float[] probabilities, List<String> labels,
                              Integer topK, boolean sort, Writer out) throws IOException {
        if (probabilities.length != labels.size()) {
            throw new IllegalArgumentException(
                    "Probabilities length " + probabilities.length + " != labels length " + labels.size());
        }

        List<Integer> indices = new ArrayList<>(labels.size());
        for (int i = 0; i < labels.size(); i++) indices.add(i);

        // Top-k by probability (if set)
        if (topK != null && topK < indices.size()) {
            indices.sort(Comparator.comparingDouble(i -> -probabilities[i]));
            indices = indices.subList(0, topK);
            if (!sort) indices.sort(Comparator.naturalOrder()); // preserve label order for output
        } else if (sort) {
            indices.sort(Comparator.comparingDouble(i -> -probabilities[i]));
        }

        Map<String, Float> map = new LinkedHashMap<>();
        for (Integer i : indices) {
            map.put(labels.get(i), probabilities[i]);
        }
        MAPPER.writeValue(out, map);
    }

    /**
     * Returns JSON string.
     */
    public static String format(float[] probabilities, List<String> labels, Integer topK, boolean sort) {
        StringWriter w = new StringWriter();
        try {
            format(probabilities, labels, topK, sort, w);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return w.toString();
    }
}
