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


@pytest.mark.parametrize("value", ["", " , , ", "   "])
def test_get_default_languages_empty_falls_back_to_default(monkeypatch, value):
    monkeypatch.setenv("EASYOCR_LANGUAGES", value)
    assert ocr_common.get_default_languages() == ["ch_tra", "en"]


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
    assert ocr_common.get_unload_timeout() == ocr_common.DEFAULT_UNLOAD_TIMEOUT == 300


def test_get_unload_timeout_parses(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "600")
    assert ocr_common.get_unload_timeout() == 600


def test_get_unload_timeout_zero_disables(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "0")
    assert ocr_common.get_unload_timeout() == 0


def test_get_unload_timeout_invalid_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "not-a-number")
    assert ocr_common.get_unload_timeout() == ocr_common.DEFAULT_UNLOAD_TIMEOUT


def test_get_unload_timeout_negative_clamped(monkeypatch):
    monkeypatch.setenv("EASYOCR_UNLOAD_TIMEOUT", "-5")
    assert ocr_common.get_unload_timeout() == 0


def test_get_unload_jobdone_default_off(monkeypatch):
    monkeypatch.delenv("EASYOCR_UNLOAD_JOBDONE", raising=False)
    assert ocr_common.get_unload_jobdone() is False


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on"])
def test_get_unload_jobdone_truthy(monkeypatch, value):
    monkeypatch.setenv("EASYOCR_UNLOAD_JOBDONE", value)
    assert ocr_common.get_unload_jobdone() is True


@pytest.mark.parametrize("value", ["false", "0", "no", "", "garbage"])
def test_get_unload_jobdone_falsy(monkeypatch, value):
    monkeypatch.setenv("EASYOCR_UNLOAD_JOBDONE", value)
    assert ocr_common.get_unload_jobdone() is False


def test_validate_image_bytes_accepts_valid_png():
    ocr_common.validate_image_bytes(_png_bytes())  # should not raise


def test_validate_image_bytes_rejects_garbage():
    with pytest.raises(ValueError):
        ocr_common.validate_image_bytes(b"this is not an image")


def test_image_bytes_to_array_returns_rgb_array():
    arr = ocr_common.image_bytes_to_array(_png_bytes(size=(4, 4)))
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (4, 4, 3)


def test_image_bytes_to_array_composites_alpha_onto_white():
    image = PILImage.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((1, 1), (255, 0, 0, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    arr = ocr_common.image_bytes_to_array(buf.getvalue())
    assert tuple(arr[1, 1]) == (255, 0, 0)
    assert tuple(arr[0, 0]) == (255, 255, 255)


def test_image_bytes_to_array_applies_exif_transpose():
    image = PILImage.new("RGB", (10, 4), (255, 0, 0))
    exif = PILImage.Exif()
    exif[0x0112] = 6
    buf = io.BytesIO()
    image.save(buf, format="JPEG", exif=exif)
    arr = ocr_common.image_bytes_to_array(buf.getvalue())
    assert arr.shape == (10, 4, 3)


def test_expand_user_path_expands_tilde(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ocr_common.expand_user_path("~/shot.png") == str(tmp_path / "shot.png")


def test_read_local_image_rejects_missing(tmp_path):
    missing = tmp_path / "nope.png"
    with pytest.raises(FileNotFoundError, match="was not found"):
        ocr_common.read_local_image(str(missing))


def test_read_local_image_rejects_directory(tmp_path):
    with pytest.raises(ValueError, match="is not a file"):
        ocr_common.read_local_image(str(tmp_path))


def test_read_local_image_rejects_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr_common, "MAX_IMAGE_BYTES", 8)
    path = tmp_path / "big.png"
    path.write_bytes(b"0123456789")
    with pytest.raises(ValueError, match="maximum allowed size"):
        ocr_common.read_local_image(str(path))


def test_read_local_image_reads_file(tmp_path):
    path = tmp_path / "ok.png"
    payload = _png_bytes()
    path.write_bytes(payload)
    assert ocr_common.read_local_image(str(path)) == payload


def test_decode_base64_image_accepts_wrapped_and_data_url():
    import base64

    raw = _png_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    wrapped = "\n".join(encoded[i : i + 16] for i in range(0, len(encoded), 16))
    assert ocr_common.decode_base64_image(wrapped) == raw
    assert ocr_common.decode_base64_image(f"data:image/png;base64,{encoded}") == raw


def test_decode_base64_image_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid base64"):
        ocr_common.decode_base64_image("@@@@")


def test_assert_public_http_url_rejects_file_scheme():
    with pytest.raises(ValueError, match="http and https"):
        ocr_common.assert_public_http_url("file:///tmp/a.png")


def test_assert_public_http_url_rejects_loopback():
    with pytest.raises(ValueError, match="not allowed"):
        ocr_common.assert_public_http_url("http://127.0.0.1/a.png")


def test_assert_public_http_url_rejects_link_local():
    with pytest.raises(ValueError, match="not allowed"):
        ocr_common.assert_public_http_url("http://169.254.169.254/latest")


def test_assert_public_http_url_rejects_resolved_loopback(monkeypatch):
    def fake_getaddrinfo(host, port):
        return [(0, 0, 0, "", ("127.0.0.1", 0))]

    monkeypatch.setattr(ocr_common.socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(ValueError, match="not allowed"):
        ocr_common.assert_public_http_url("http://localhost/a.png")


def test_assert_public_http_url_allows_public_host(monkeypatch):
    def fake_getaddrinfo(host, port):
        return [(0, 0, 0, "", ("1.1.1.1", 0))]

    monkeypatch.setattr(ocr_common.socket, "getaddrinfo", fake_getaddrinfo)
    ocr_common.assert_public_http_url("https://example.com/a.png")
