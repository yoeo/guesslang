import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List

import numpy as np
import onnxruntime as ort
import tensorflow as tf


def _softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(logits)
    return exp / np.sum(exp, axis=-1, keepdims=True)


def _load_snippets(path: Path) -> List[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(x, str) for x in payload):
        raise RuntimeError("Snippets file must be a JSON array of strings.")
    return payload


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_vectorizers(preprocess_config: Dict[str, Any], deep_vocab: List[str], tfidf_vocab: List[str], idf: List[float]):
    int_layer = tf.keras.layers.TextVectorization(
        standardize=preprocess_config["standardize"],
        split=preprocess_config["split"],
        max_tokens=preprocess_config["max_tokens"],
        output_mode="int",
        output_sequence_length=preprocess_config["output_sequence_length_for_int"],
    )
    int_layer.set_vocabulary(deep_vocab)

    tfidf_layer = tf.keras.layers.TextVectorization(
        standardize=preprocess_config["standardize"],
        split=preprocess_config["split"],
        max_tokens=preprocess_config["max_tokens"],
        ngrams=preprocess_config["ngrams"],
        output_mode="tf_idf",
    )
    tfidf_layer.set_vocabulary(tfidf_vocab, idf_weights=idf)
    return int_layer, tfidf_layer


def validate(saved_model_path: Path, artifacts_dir: Path, onnx_path: Path, snippets: List[str], atol: float) -> None:
    serving_obj = tf.saved_model.load(str(saved_model_path))
    serve_fn = serving_obj.signatures.get("serve") or serving_obj.signatures["serving_default"]

    preprocess_config = _load_json(artifacts_dir / "preprocess_config.json")
    deep_vocab_map = _load_json(artifacts_dir / "deep_vocab.json")
    tfidf_vocab_map = _load_json(artifacts_dir / "vocab.json")
    idf = _load_json(artifacts_dir / "idf.json")
    labels = _load_json(artifacts_dir / "labels.json")

    deep_vocab = [None] * len(deep_vocab_map)
    for token, idx in deep_vocab_map.items():
        deep_vocab[int(idx)] = token
    tfidf_vocab = [None] * len(tfidf_vocab_map)
    for token, idx in tfidf_vocab_map.items():
        tfidf_vocab[int(idx)] = token

    int_layer, tfidf_layer = _build_vectorizers(preprocess_config, deep_vocab, tfidf_vocab, idf)

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_names = {x.name for x in sess.get_inputs()}
    if "deep_input" not in input_names or "wide_input" not in input_names:
        raise RuntimeError(f"Unexpected ONNX input names: {sorted(input_names)}")

    max_abs_logit_diff = 0.0
    max_abs_prob_diff = 0.0

    for snippet in snippets:
        batch_text = tf.constant([[snippet]], dtype=tf.string)
        savedmodel_out = serve_fn(content=batch_text)
        out_tensor = next(iter(savedmodel_out.values()))
        keras_logits = out_tensor.numpy().astype(np.float32)

        deep_input = int_layer(batch_text).numpy().astype(np.int32)
        wide_input = tfidf_layer(batch_text).numpy().astype(np.float32)

        onnx_logits = sess.run(
            None,
            {
                "deep_input": deep_input,
                "wide_input": wide_input,
            },
        )[0].astype(np.float32)

        logit_diff = np.max(np.abs(keras_logits - onnx_logits))
        prob_diff = np.max(np.abs(_softmax(keras_logits) - _softmax(onnx_logits)))

        max_abs_logit_diff = max(max_abs_logit_diff, float(logit_diff))
        max_abs_prob_diff = max(max_abs_prob_diff, float(prob_diff))

    print(json.dumps(
        {
            "num_snippets": len(snippets),
            "num_labels": len(labels),
            "max_abs_logit_diff": max_abs_logit_diff,
            "max_abs_prob_diff": max_abs_prob_diff,
            "tolerance": atol,
            "passed": max_abs_logit_diff <= atol,
        },
        indent=2,
    ))

    if max_abs_logit_diff > atol:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SavedModel pipeline vs ONNX vectorized model.")
    parser.add_argument("--saved-model", default="new_model/saved_model", help="Path to trained SavedModel.")
    parser.add_argument("--artifacts", default="to_onnx/artifacts", help="Path to exported artifacts directory.")
    parser.add_argument("--onnx", default="to_onnx/artifacts/guesslang.onnx", help="Path to exported ONNX model.")
    parser.add_argument(
        "--snippets",
        default="to_onnx/snippets.json",
        help="JSON file containing source-code snippets array.",
    )
    parser.add_argument("--atol", type=float, default=1e-3, help="Absolute tolerance for max logit difference.")
    return parser.parse_args()


def main() -> None:
    if sys.flags.utf8_mode == 0 and os.environ.get("GUESSLANG_UTF8_REEXEC") != "1":
        env = dict(os.environ)
        env["GUESSLANG_UTF8_REEXEC"] = "1"
        cmd = [sys.executable, "-X", "utf8", __file__, *sys.argv[1:]]
        raise SystemExit(subprocess.call(cmd, env=env))

    args = parse_args()
    snippets = _load_snippets(Path(args.snippets))
    validate(Path(args.saved_model), Path(args.artifacts), Path(args.onnx), snippets, args.atol)


if __name__ == "__main__":
    main()
