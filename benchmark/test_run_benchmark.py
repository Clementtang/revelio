"""Tests for key-figure matching in the regression benchmark runner."""

from run_benchmark import value_in_row


def test_value_in_row_should_match_full_token():
    row = "| NET INCOME | 451,755,362 | 46 |"
    assert value_in_row("451755362", row)
    assert value_in_row("46", row)


def test_value_in_row_should_reject_digit_substring():
    row = "| NET INCOME | 451,755,362 | 46 |"
    assert not value_in_row("51", row)
    assert not value_in_row("100", "| 1000 |")


def test_value_in_row_should_reject_superstring_neighbor():
    row = "| Research and development | 146,950,466 |"
    assert not value_in_row("46", row)
    assert value_in_row("146950466", row)
