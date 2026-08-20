#!/usr/bin/env python3
"""Fixture acceptance suite: sha256-gate PDFs, score converted markdown vs baseline.

Usage:
    python3 run_suite.py
    python3 run_suite.py --converted-dir ~/odl-output/benchmark
    python3 run_suite.py --convert --converted-dir benchmark/output

PDFs live in benchmark/fixtures/ (gitignored). Each ground-truth JSON records
the expected sha256. Conversion is optional and needs a running
opendataloader-pdf hybrid server plus ~/odl-env.

Exit codes:
    0  every scored document meets its baseline
    1  a fixture hash mismatches, a score regresses, or conversion fails
    2  nothing was scored (fixtures or converted markdown missing)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from run_benchmark import evaluate

HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURES = HERE / "fixtures"
DEFAULT_SUITE = HERE / "suite.json"
HYBRID_URL = "http://127.0.0.1:5002"
HYBRID_PORT = "5002"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_suite(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError(f"{path} has no documents list")
    return documents


def expected_sha256(ground_truth_path: Path) -> str:
    truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    digest = truth.get("source", {}).get("sha256")
    if not digest:
        raise ValueError(f"{ground_truth_path} is missing source.sha256")
    return digest


def find_converted(converted_dir: Path | None, doc_id: str) -> Path | None:
    if converted_dir is None:
        return None
    direct = converted_dir / f"{doc_id}.md"
    if direct.is_file():
        return direct
    nested = converted_dir / doc_id
    if nested.is_dir():
        matches = sorted(nested.glob("*.md"))
        if len(matches) == 1:
            return matches[0]
        for candidate in matches:
            if candidate.stem == doc_id or doc_id in candidate.stem:
                return candidate
    return None


def hybrid_listening() -> bool:
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{HYBRID_PORT}", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "LISTEN" in result.stdout


def convert_pdf(pdf_path: Path, output_dir: Path, odl_python: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    script = (
        "import opendataloader_pdf, sys\n"
        "opendataloader_pdf.convert(\n"
        "    input_path=[sys.argv[1]],\n"
        "    output_dir=sys.argv[2],\n"
        "    format='markdown,json',\n"
        "    hybrid='docling-fast',\n"
        "    hybrid_mode='full',\n"
        f"    hybrid_url='{HYBRID_URL}',\n"
        ")\n"
    )
    completed = subprocess.run(
        [str(odl_python), "-c", script, str(pdf_path), str(output_dir)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"conversion failed for {pdf_path.name}: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    markdown = list(output_dir.glob("*.md"))
    if not markdown:
        raise RuntimeError(f"conversion produced no markdown in {output_dir}")
    return markdown[0]


def meets_baseline(passed: int, checks: int, baseline_passed: int, baseline_checks: int) -> bool:
    """True when the score did not regress. Extra passes are allowed."""
    return checks == baseline_checks and passed >= baseline_passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument(
        "--converted-dir",
        type=Path,
        help="Directory of already-converted markdown (id.md or id/*.md)",
    )
    parser.add_argument(
        "--convert",
        action="store_true",
        help="Run hybrid conversion when converted markdown is missing",
    )
    parser.add_argument(
        "--odl-python",
        type=Path,
        default=Path.home() / "odl-env" / "bin" / "python3",
        help="Python from the opendataloader-pdf venv",
    )
    args = parser.parse_args()

    documents = load_suite(args.suite)
    scored = 0
    failed = 0

    for spec in documents:
        doc_id = spec["id"]
        gt_path = HERE / spec["ground_truth"]
        fixture = args.fixtures_dir / spec["fixture"]
        print(f"== {doc_id}")

        if not fixture.is_file():
            print(f"  SKIP missing fixture {fixture}")
            continue
        digest = sha256_file(fixture)
        expected = expected_sha256(gt_path)
        if digest != expected:
            print(f"  FAIL sha256 mismatch: got {digest}, expected {expected}")
            failed += 1
            continue
        print(f"  sha256 ok ({digest[:16]}…)")

        converted = find_converted(args.converted_dir, doc_id)
        if converted is None and args.convert:
            if not hybrid_listening():
                print(
                    f"  FAIL hybrid server is not listening on {HYBRID_URL}; "
                    f"start it in {spec['mode']} mode first"
                )
                failed += 1
                continue
            if not args.odl_python.is_file():
                print(f"  FAIL odl python not found: {args.odl_python}")
                failed += 1
                continue
            target = (args.converted_dir or (HERE / "output")) / doc_id
            started = time.time()
            try:
                converted = convert_pdf(fixture, target, args.odl_python)
            except RuntimeError as exc:
                print(f"  FAIL {exc}")
                failed += 1
                continue
            print(f"  converted in {time.time() - started:.0f}s -> {converted}")
        if converted is None:
            print("  SKIP no converted markdown (pass --converted-dir or --convert)")
            continue

        result = evaluate(str(gt_path), str(converted))
        print(f"  score {result.passed}/{result.checks} (baseline {spec['baseline_passed']}/{spec['baseline_checks']})")
        for item in result.failures:
            print(f"    FAIL {item}")
        scored += 1
        if not meets_baseline(
            result.passed,
            result.checks,
            spec["baseline_passed"],
            spec["baseline_checks"],
        ):
            print("  FAIL regression against frozen baseline")
            failed += 1
        else:
            print("  PASS baseline held")

    if scored == 0:
        print("no documents scored")
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
