#!/usr/bin/env python3
"""Regression benchmark runner: compare a converted markdown file against ground truth.

Usage:
    python3 run_benchmark.py <ground-truth.json> <converted.md>

Ground truth JSON schema (one file per document):
    {
      "document": "<slug>",
      "source": {"title": "...", "url": "...", "notes": "..."},
      "structure": {
        "headings": ["<heading text that must appear>", ...],
        "tables": [{"name": "...", "min_rows": N, "columns": N}, ...]
      },
      "key_figures": [
        {"label": "<row label substring>", "values": ["<number>", ...]},
        ...
      ]
    }

Checks (full structural comparison, per PRD decision 2026-08-15):
    - every expected heading appears in the output
    - table count, column count, and minimum row count (guards against truncation)
    - every key-figure row is present and contains all expected values

Exit code 0 when everything passes, 1 otherwise. Stdlib only.
"""

import json
import re
import sys


def normalize(text: str) -> str:
    """Normalize for numeric matching: drop $, commas, spaces; () becomes leading minus."""
    text = text.replace("$", "").replace(",", "").replace(" ", "")
    return re.sub(r"\((\d+)\)", r"-\1", text)


def parse_tables(markdown: str) -> list[list[str]]:
    """Extract pipe tables as lists of row strings (separator rows excluded)."""
    tables = []
    current = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            if re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", stripped):
                continue
            current.append(stripped)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def column_count(row: str) -> int:
    return len(row.strip("|").split("|"))


def run(ground_truth_path: str, converted_path: str) -> int:
    with open(ground_truth_path, encoding="utf-8") as f:
        truth = json.load(f)
    with open(converted_path, encoding="utf-8") as f:
        markdown = f.read()

    failures = []
    checks = 0

    for heading in truth["structure"]["headings"]:
        checks += 1
        if heading not in markdown:
            failures.append(f"heading missing: {heading!r}")

    tables = parse_tables(markdown)
    expected_tables = truth["structure"]["tables"]
    checks += 1
    if len(tables) != len(expected_tables):
        failures.append(f"table count: expected {len(expected_tables)}, found {len(tables)}")

    for table, spec in zip(tables, expected_tables):
        checks += 2
        if len(table) < spec["min_rows"]:
            failures.append(
                f"table {spec['name']}: {len(table)} rows, expected at least {spec['min_rows']}"
            )
        cols = column_count(table[0])
        if cols != spec["columns"]:
            failures.append(f"table {spec['name']}: {cols} columns, expected {spec['columns']}")

    # Rows are matched on normalized text so split/garbled labels still resolve
    # when the label substring survives; a truly lost row fails as label-missing.
    all_rows = [row for table in tables for row in table]
    for figure in truth["key_figures"]:
        checks += 1
        label_norm = normalize(figure["label"]).lower()
        matches = [row for row in all_rows if label_norm in normalize(row).lower()]
        if not matches:
            failures.append(f"key figure label missing: {figure['label']!r}")
            continue
        missing = [
            value
            for value in figure["values"]
            if not any(normalize(value) in normalize(row) for row in matches)
        ]
        if missing:
            failures.append(f"key figure {figure['label']!r}: values not in row: {missing}")

    passed = checks - len(failures)
    print(f"{truth['document']}: {passed}/{checks} checks passed")
    for failure in failures:
        print(f"  FAIL {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(run(sys.argv[1], sys.argv[2]))
