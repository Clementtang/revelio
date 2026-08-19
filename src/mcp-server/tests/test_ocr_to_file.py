"""Tests for ocr_to_file.py error handling.

These drive the script as a subprocess and only exercise paths that fail before
EasyOCR is imported, so they run without the heavy OCR stack.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "ocr_to_file.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_no_args_prints_usage_and_exits_nonzero():
    result = _run()
    assert result.returncode != 0
    assert "Usage:" in result.stderr


def test_missing_file_exits_nonzero_with_message():
    result = _run("/nonexistent/path/does-not-exist.png")
    assert result.returncode != 0
    assert "找不到檔案" in result.stderr


def test_missing_tilde_path_is_expanded_in_error():
    result = _run("~/revelio-missing-ocr-probe.png")
    assert result.returncode != 0
    assert "找不到檔案" in result.stderr
    assert str(Path.home()) in result.stderr
    assert "~/revelio-missing-ocr-probe.png" not in result.stderr


def test_directory_path_is_rejected(tmp_path):
    result = _run(str(tmp_path))
    assert result.returncode != 0
    assert "is not a file" in result.stderr
