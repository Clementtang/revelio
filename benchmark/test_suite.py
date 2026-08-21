"""Tests for the fixture suite helpers. No OCR stack required."""

import hashlib
import json
from pathlib import Path

import pytest

from run_benchmark import evaluate
from run_suite import (
    expected_sha256,
    find_converted,
    load_suite,
    meets_baseline,
    sha256_file,
)

HERE = Path(__file__).resolve().parent
TESTDATA = HERE / "testdata"


def test_load_suite_lists_four_frozen_documents():
    documents = load_suite(HERE / "suite.json")
    ids = [item["id"] for item in documents]
    assert ids == [
        "tsmc-2025q3-consolidated-en",
        "tsmc-2025q3-consolidated-zh",
        "resnet-multicolumn-en",
        "resnet-scanned-en",
    ]
    for item in documents:
        assert (HERE / item["ground_truth"]).is_file()
        assert item["baseline_checks"] >= item["baseline_passed"]


def test_sha256_file_matches_expected(tmp_path):
    payload = b"revelio-fixture-probe"
    path = tmp_path / "a.bin"
    path.write_bytes(payload)
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_expected_sha256_reads_ground_truth():
    digest = expected_sha256(TESTDATA / "simple.json")
    assert len(digest) == 64


def test_find_converted_prefers_id_markdown(tmp_path):
    converted = tmp_path / "simple-table.md"
    converted.write_text("x")
    assert find_converted(tmp_path, "simple-table") == converted


def test_find_converted_nested_directory(tmp_path):
    nested = tmp_path / "simple-table"
    nested.mkdir()
    markdown = nested / "simple-table.md"
    markdown.write_text("x")
    assert find_converted(tmp_path, "simple-table") == markdown


def test_meets_baseline_allows_improvement_not_regression():
    assert meets_baseline(26, 27, 26, 27)
    assert meets_baseline(27, 27, 26, 27)
    assert not meets_baseline(25, 27, 26, 27)
    assert not meets_baseline(26, 26, 26, 27)


def test_evaluate_synthetic_document_is_a_full_pass():
    result = evaluate(str(TESTDATA / "simple.json"), str(TESTDATA / "simple.md"))
    assert result.failures == []
    assert result.passed == result.checks


def test_evaluate_detects_lost_key_figure(tmp_path):
    broken = tmp_path / "broken.md"
    broken.write_text("# Income statement\n\n| Item | Amount | % |\n| --- | --- | --- |\n| OTHER | 2 | 100 |\n")
    result = evaluate(str(TESTDATA / "simple.json"), str(broken))
    assert result.failures
    assert any("NET REVENUE" in item for item in result.failures)


def test_suite_ground_truth_sha256_matches_fixture_when_present():
    fixtures = HERE / "fixtures"
    if not fixtures.is_dir():
        pytest.skip("benchmark/fixtures not present")
    for spec in json.loads((HERE / "suite.json").read_text())["documents"]:
        pdf = fixtures / spec["fixture"]
        if not pdf.is_file():
            pytest.skip(f"missing {spec['fixture']}")
        assert sha256_file(pdf) == expected_sha256(HERE / spec["ground_truth"])
