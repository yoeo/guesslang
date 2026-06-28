#!/usr/bin/env python3
"""Compare Guesslang Python and JVM predictions for the same snippets."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_snippets(path: Path) -> list[dict[str, str]]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list) and all(isinstance(item, str) for item in payload):
        return [{"name": f"snippet-{idx}", "text": item} for idx, item in enumerate(payload, start=1)]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("tests"), list):
        return payload["tests"]
    raise ValueError("Snippets must be a JSON string array, object array, or {\"tests\": [...]}.")


def load_extension_map(path: Path) -> dict[str, str]:
    languages: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
    return {extension: language for language, extension in languages.items()}


def python_top1(text: str) -> str | None:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from guesslang import Guess

    probabilities = Guess().probabilities(text)
    return probabilities[0][0] if probabilities else None


def jvm_top1(command: list[str], models_dir: Path, text: str) -> str:
    completed = subprocess.run(
        [*command, "--models", str(models_dir), "--topk", "1", "--sort"],
        input=text,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    probabilities = json.loads(completed.stdout)
    if not probabilities:
        raise RuntimeError("JVM runtime returned no probabilities")
    return next(iter(probabilities))


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    jvm_dir = repo_root / "jvm"
    if sys.platform.startswith("win"):
        default_command = jvm_dir / "build" / "install" / "guesslang-onnx-cli" / "bin" / "guesslang-onnx-cli.bat"
    else:
        default_command = jvm_dir / "build" / "install" / "guesslang-onnx-cli" / "bin" / "guesslang-onnx-cli"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snippets", type=Path, default=jvm_dir / "parity_snippets.json")
    parser.add_argument("--models", type=Path, default=jvm_dir / "models")
    parser.add_argument("--languages", type=Path, default=repo_root / "guesslang" / "data" / "languages.json")
    parser.add_argument("--jvm-command", nargs="+", default=[str(default_command)])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    extension_to_language = load_extension_map(args.languages)
    failures = 0
    for case in load_snippets(args.snippets):
        name = case.get("name", "snippet")
        text = case.get("text", "")
        py = python_top1(text)
        jvm_label = jvm_top1(args.jvm_command, args.models, text)
        jvm = extension_to_language.get(jvm_label, jvm_label)
        if py == jvm:
            print(f"PASS {name}: {py}")
        else:
            failures += 1
            print(f"FAIL {name}: python={py} jvm={jvm}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
