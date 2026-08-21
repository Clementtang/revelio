"""Tests for table-verify helpers. Does not import surya or pymupdf."""

from verify_tables import (
    build_report,
    decimal_loss_candidates,
    markdown_table_numbers,
    normalize,
    numeric_tokens,
    parse_page_range,
)


def test_normalize_should_keep_spaces_between_numbers():
    assert "70.484.9" not in normalize("70.4 84.9")
    assert numeric_tokens("70.4 84.9") == ["70.4", "84.9"]


def test_numeric_tokens_should_drop_single_digits_and_strip_thousands():
    assert "1,000" not in numeric_tokens("NET REVENUE 1,000")
    assert numeric_tokens("NET REVENUE 1,000") == ["1000"]
    assert numeric_tokens("rate 3") == []


def test_markdown_table_numbers_should_skip_separator_rows():
    md = "| Item | Amount |\n| --- | --- |\n| NET REVENUE | 1,000 |\n"
    entries = markdown_table_numbers(md)
    tokens = [e["token"] for e in entries]
    assert tokens == ["1000"]
    assert entries[0]["table"] == 0


def test_decimal_loss_candidates_should_match_restored_point():
    assert decimal_loss_candidates("357", {"3.57": 0.9, "21.75": 0.8}) == ["3.57"]
    assert decimal_loss_candidates("21.75", {"3.57": 0.9}) == []


def test_build_report_should_flag_decimal_loss_as_suspect():
    entries = [{"token": "357", "table": 0, "row": "| error rate | 357 |"}]
    report, count = build_report("a.pdf", "a.md", entries, {"3.57": 0.99}, tables_seen=1)
    assert count == 1
    assert "357" in report
    assert "小數點" in report


def test_build_report_should_collapse_unverifiable_tables():
    entries = [
        {"token": str(1000 + i), "table": 0, "row": f"| row {i} | {1000 + i} |"}
        for i in range(10)
    ]
    report, count = build_report("a.pdf", "a.md", entries, {}, tables_seen=0)
    assert count == 0
    assert "無法交叉驗證" in report


def test_parse_page_range_is_one_based_inclusive():
    assert parse_page_range("5") == [4]
    assert parse_page_range("4-6") == [3, 4, 5]
