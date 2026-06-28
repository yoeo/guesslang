# Guesslang JVM ONNX Runtime

An alternative JVM runtime for Guesslang language detection. It runs an ONNX export of the Guesslang model and outputs JSON probabilities per language label. Works on **Windows** and **Linux x86_64** with **JDK 17**. Uses **DJL + ONNX Runtime**; the JAR is a thin jar and does **not** bundle native ONNX Runtime binaries. DJL resolves and caches them at runtime.

The Python package remains the reference runtime for the public Python API, training, and the existing `guesslang` CLI. Use this JVM runtime when you need language detection inside Java/Kotlin applications, IDE plugins, or services where the Python TensorFlow dependency is hard to deploy.

## What it does

- Reads source code or text from a file (`--file <path>`) or from **stdin** (UTF-8).
- Preprocesses text with configurable TF-IDF (from `preprocess_config.json`): lowercase, tokenization, n-grams, IDF weighting, optional L2 normalization.
- Runs one forward pass with the ONNX model (input shape `[1, vocabSize]`).
- Outputs **JSON to stdout**: `{ "Python": 0.71, "Java": 0.12, ... }` (or top-k / sorted if requested).

## Required model artifacts

Place these in the **models** directory (or pass `--models <dir>`):

| File | Format | Description |
|------|--------|-------------|
| `guesslang.onnx` | ONNX model | Main model; input `[1, vocabSize]`, output logits or probabilities. |
| `labels.json` | JSON array of strings | Label names in **output order** (same order as model output). |
| `vocab.json` | JSON array of strings | Vocabulary in **index order** (index = position in array). |
| `idf.json` | JSON array of numbers | IDF values aligned with `vocab.json` indices. |
| `preprocess_config.json` | JSON object | Preprocessing options (see below). |
| `model_io.json` | JSON object (optional) | `input_name`, `output_name`, `output_is_logits` (boolean). If missing, defaults are used and I/O is inferred from DJL where possible. |
| `golden_tests.json` | JSON array or `{ "tests": [ ... ] }` | For `--selftest`; each item: `name`, `text`, `expected_top1`. |

### preprocess_config.json (supported keys)

- `lowercase` (boolean, default true)
- `strip_punctuation` (boolean, default false) — removes `\p{Punct}` but **keeps** `_`, `#`, `+`
- `collapse_whitespace` (boolean, default true)
- `split`: `"whitespace"` (default) or `"regex"`
- `split_regex` (string) — used when `split` is `"regex"`
- `ngrams` (int, default 1) — 1, 2, or 3
- `include_all_ngrams` (boolean, default true) — if true, include 1..n grams; if false, only n-grams
- `oov_behavior`: `"ignore"` (default) or `"bucket"` (use `oov_token` from config)
- `oov_token` (string) — used when `oov_behavior` is `"bucket"`
- `tf_mode`: `"raw"` (default) or `"normalized"` (count/total_tokens)
- `l2_normalize` (boolean, default false)

## Build

**Prerequisites:** JDK 17.

Build with the included Gradle wrapper:

**Windows (PowerShell):**

```powershell
.\gradlew.bat build
```

**Linux / macOS (bash):**

```bash
chmod +x gradlew
./gradlew build
```

The runnable **thin** JAR is at `build/libs/guesslang-onnx-cli-1.0.0.jar`. Because it does not bundle dependencies, run via the **application distribution** (recommended): run `gradlew installDist`; then use the script under `build/install/guesslang-onnx-cli/bin/` which puts the thin JAR and all dependency JARs on the classpath.

## Run

First, install the distribution so the startup script and `lib/` are created:

```bash
.\gradlew.bat installDist   # Windows
./gradlew installDist       # Linux/macOS
```

Then run (examples use the distribution script, which adds all JARs to the classpath):

- **Stdin:** pipe or type text; output is JSON to stdout.

  **Windows (PowerShell):**
  ```powershell
  echo "def foo(): pass" | build\install\guesslang-onnx-cli\bin\guesslang-onnx-cli.bat
  ```

  **Linux / macOS:**
  ```bash
  echo 'def foo(): pass' | build/install/guesslang-onnx-cli/bin/guesslang-onnx-cli
  ```

- **From file:**

  **Windows:** `build\install\guesslang-onnx-cli\bin\guesslang-onnx-cli.bat --file path\to\source.py`  
  **Linux/macOS:** `build/install/guesslang-onnx-cli/bin/guesslang-onnx-cli --file path/to/source.py`

- **Selftest (golden tests):**
  ```bash
  build/install/guesslang-onnx-cli/bin/guesslang-onnx-cli --selftest models/golden_tests.json
  ```
  Exit code is 1 if any test fails.

- **Top-k and sort:**
  ```bash
  build/install/guesslang-onnx-cli/bin/guesslang-onnx-cli --topk 3 --sort
  ```

- **Print model I/O (best-effort):** `--print-io`  
- **Help:** `--help`

## Python/JVM parity testing

Use `scripts/parity_test.py` to compare Python and JVM top-1 language predictions for the same snippets. Run it from the repository root after installing the Python dependencies and building the JVM distribution:

```bash
cd jvm
./gradlew installDist
cd ..
python jvm/scripts/parity_test.py --snippets jvm/parity_snippets.json
```

The script fails if the Python `Guess().probabilities(...)` top prediction differs from the JVM CLI top prediction. This is intended as the maintainer-facing equivalence check for changes to ONNX export, preprocessing, or runtime behavior.

## Jar size and thin jar

The project is built as a **thin JAR**: the main JAR does **not** include DJL/ONNX Runtime dependencies or native binaries. This keeps the JAR well under 100MB. Dependencies are resolved by Gradle and placed in `lib/` when using the application distribution. Native ONNX Runtime libraries are **not** bundled; DJL downloads/caches them on first use (see below).

## DJL ONNX Runtime native caching

- On first run, DJL may download the appropriate ONNX Runtime native library for your OS (Windows/Linux x86_64) and cache it (e.g. in the user home directory).
- If native loading fails, ensure you have a compatible JDK (17) and OS (Windows or Linux x86_64). Check DJL/ONNX Runtime documentation for required native artifacts.
- You can set `DJL_CACHE_DIR` to control where natives are cached.

## Troubleshooting

| Error | What to do |
|-------|-------------|
| `Missing model file: ... guesslang.onnx` | Add `guesslang.onnx` to the `models` directory (or the path given by `--models`). |
| `Missing labels file` / `Missing vocab file` / etc. | Add the required JSON artifacts to the models directory; see table above. |
| `Model output length X does not match labels length Y` | Ensure `labels.json` has the same length and order as the model’s output dimension. |
| `Failed to load ONNX model` | Check that the ONNX file is valid and that the ONNX Runtime engine (and natives) can load it; run with `--print-io` to see I/O info. |
| Native library / UnsatisfiedLinkError | Ensure JDK 17 and Windows or Linux x86_64; let DJL download natives on first run or check DJL/ONNX Runtime docs for manual native setup. |
| `vocab size != idf length` | Ensure `vocab.json` and `idf.json` have the same length. |
| Selftest fails | Check `golden_tests.json` format and that `expected_top1` matches the model’s top prediction for the given text. |

## License

Use and adapt as needed for your project. Fully Open Source, no restrictions.
