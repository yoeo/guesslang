package com.guesslang.cli;

import java.util.ArrayList;
import java.util.List;

/**
 * Parses and holds CLI arguments. No external CLI libs.
 */
public final class CliArgs {

    public static final String HELP = "--help";
    public static final String FILE = "--file";
    public static final String MODELS = "--models";
    public static final String TOPK = "--topk";
    public static final String SORT = "--sort";
    public static final String SELFTEST = "--selftest";
    public static final String PRINT_IO = "--print-io";

    private boolean help;
    private String filePath;
    private String modelsDir = "models";
    private Integer topK;
    private boolean sort;
    private String selftestPath;
    private boolean printIo;

    public static CliArgs parse(String[] args) {
        CliArgs a = new CliArgs();
        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            switch (arg) {
                case HELP:
                    a.help = true;
                    break;
                case FILE:
                    if (i + 1 < args.length) {
                        a.filePath = args[++i];
                    } else {
                        throw new IllegalArgumentException("--file requires a path argument");
                    }
                    break;
                case MODELS:
                    if (i + 1 < args.length) {
                        a.modelsDir = args[++i];
                    } else {
                        throw new IllegalArgumentException("--models requires a directory argument");
                    }
                    break;
                case TOPK:
                    if (i + 1 < args.length) {
                        try {
                            a.topK = Integer.parseInt(args[++i]);
                            if (a.topK < 1) throw new IllegalArgumentException("--topk must be >= 1");
                        } catch (NumberFormatException e) {
                            throw new IllegalArgumentException("--topk requires an integer: " + args[i]);
                        }
                    } else {
                        throw new IllegalArgumentException("--topk requires an integer argument");
                    }
                    break;
                case SORT:
                    a.sort = true;
                    break;
                case SELFTEST:
                    if (i + 1 < args.length) {
                        a.selftestPath = args[++i];
                    } else {
                        throw new IllegalArgumentException("--selftest requires a path argument");
                    }
                    break;
                case PRINT_IO:
                    a.printIo = true;
                    break;
                default:
                    if (arg.startsWith("-")) {
                        throw new IllegalArgumentException("Unknown option: " + arg);
                    }
                    // positional args ignored for now
                    break;
            }
        }
        return a;
    }

    public boolean isHelp() { return help; }
    public String getFilePath() { return filePath; }
    public String getModelsDir() { return modelsDir; }
    public Integer getTopK() { return topK; }
    public boolean isSort() { return sort; }
    public String getSelftestPath() { return selftestPath; }
    public boolean isPrintIo() { return printIo; }

    public static void printHelp() {
        System.out.println("Guesslang ONNX CLI — language detection from text using an ONNX model.");
        System.out.println();
        System.out.println("Usage:");
        System.out.println("  java -jar guesslang-onnx-cli.jar [options]");
        System.out.println("  java -cp ... com.guesslang.Main [options]");
        System.out.println();
        System.out.println("Input:");
        System.out.println("  --file <path>     Read entire file as UTF-8. If omitted, read stdin.");
        System.out.println();
        System.out.println("Output:");
        System.out.println("  JSON to stdout: { \"Python\": 0.71, \"Java\": 0.12, ... }");
        System.out.println("  --topk <k>       Output only top-k labels by probability.");
        System.out.println("  --sort           Sort entries by probability descending (default: label order).");
        System.out.println();
        System.out.println("Model and behavior:");
        System.out.println("  --models <dir>   Model directory (default: models).");
        System.out.println("  --print-io       Print model input/output names and shapes at startup.");
        System.out.println();
        System.out.println("Testing:");
        System.out.println("  --selftest <path>  Run golden tests from JSON file; exit 1 on failure.");
        System.out.println();
        System.out.println("Examples:");
        System.out.println("  echo 'def foo(): pass' | java -jar guesslang-onnx-cli.jar");
        System.out.println("  java -jar guesslang-onnx-cli.jar --file src/main.py");
        System.out.println("  java -jar guesslang-onnx-cli.jar --topk 3 --sort");
        System.out.println("  java -jar guesslang-onnx-cli.jar --selftest models/golden_tests.json");
    }
}
