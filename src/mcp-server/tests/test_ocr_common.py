"""Tests for ocr_common — the shared, EasyOCR-free helper module."""

import io

import numpy as np
import pytest
from PIL import Image as PILImage

import ocr_common


def _png_bytes(size=(4, 4), color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    PILImage.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_get_default_languages_default(monkeypatch):
    monkeypatch.delenv("EASYOCR_LANGUAGES", raising=False)
    assert ocr_common.get_default_languages() == ["ch_tra", "en"]


def test_get_default_languages_parses_and_strips(monkeypatch):
    monkeypatch.setenv("EASYOCR_LANGUAGES", " ch_tra , en , ja ")
    assert ocr_common.get_default_languages() == ["ch_tra", "en", "ja"]


def test_get_gpu_flag_default_is_cpu(monkeypatch):
    monkeypatch.delenv("EASYOCR_GPU", raising=False)
    assert ocr_common.get_gpu_flag() is False


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on"])
def test_get_gpu_flag_truthy(monkeypatch, value):
    monkeypatch.setenv("EASYOCR_GPU", value)
    assert ocr_common.get_gpu_flag() is True


@pytest.mark.parametrize("value", ["false", "0", "no", "", "garbage"])
def test_get_gpu_flag_falsy(monkeypatch, value):
    monkeypatch.setenv("EASYOCR_GPU", value)
    assert ocr_common.get_gpu_flag() is False


def test_get_unload_timeout_default(monkeypatch):
    monkeypatch.delenv("EASYOCR_UNLOAD_TIMEOUT", raising=False)
    assert ocr_common.get_unload_timeout() == 0


def test_get_unload_timeout_parses(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "600")
    assert ocr_common.get_unload_timeout() == 600


def test_get_unload_timeout_invalid_falls_back_to_zero(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "not-a-number")
    assert ocr_common.get_unload_timeout() == 0


def test_get_unload_timeout_negative_clamped(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "-5")
    assert ocr_common.get_unload_timeout() == 0


def test_validate_image_bytes_accepts_valid_png():
    ocr_common.validate_image_bytes(_png_bytes())  # should not raise


def test_validate_image_bytes_rejects_garbage():
    with pytest.raises(ValueError):
        ocr_common.validate_image_bytes(b"this is not an image")


def test_image_bytes_to_array_returns_rgb_array():
    arr = ocr_common.image_bytes_to_array(_png_bytes(size=(4, 4)))
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (4, 4, 3)
