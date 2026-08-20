"""Handler-level tests for the MCP OCR tools.

EasyOCR is stubbed: these cover path/URL/base64 validation, size caps, and
SSRF checks without importing PyTorch.
"""

import base64
import io

import numpy as np
import pytest
from PIL import Image as PILImage

import ocr_common
import server


def _png_bytes(size=(4, 4), color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    PILImage.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def stub_ocr(monkeypatch):
    monkeypatch.setattr(server, "_run_ocr", lambda *args, **kwargs: ["ok"])


def test_ocr_image_file_rejects_missing(stub_ocr):
    with pytest.raises(ValueError, match="was not found"):
        server.ocr_image_file("/nonexistent/revelio-missing.png")


def test_ocr_image_file_rejects_directory(tmp_path, stub_ocr):
    with pytest.raises(ValueError, match="is not a file"):
        server.ocr_image_file(str(tmp_path))


def test_ocr_image_file_rejects_oversize(tmp_path, stub_ocr, monkeypatch):
    monkeypatch.setattr(ocr_common, "MAX_IMAGE_BYTES", 8)
    path = tmp_path / "big.bin"
    path.write_bytes(b"0123456789")
    with pytest.raises(ValueError, match="maximum allowed size"):
        server.ocr_image_file(str(path))


def test_ocr_image_file_expands_tilde_and_passes_array(tmp_path, monkeypatch):
    image_path = tmp_path / "shot.png"
    image_path.write_bytes(_png_bytes())
    monkeypatch.setenv("HOME", str(tmp_path))
    seen = {}

    def fake_run(image, *args, **kwargs):
        seen["image"] = image
        return ["ok"]

    monkeypatch.setattr(server, "_run_ocr", fake_run)
    assert server.ocr_image_file("~/shot.png") == ["ok"]
    assert isinstance(seen["image"], np.ndarray)
    assert seen["image"].shape == (4, 4, 3)


def test_ocr_image_base64_accepts_tiny_png(stub_ocr):
    encoded = base64.b64encode(_png_bytes()).decode("ascii")
    assert server.ocr_image_base64(encoded) == ["ok"]


def test_ocr_image_base64_accepts_data_url(stub_ocr):
    encoded = base64.b64encode(_png_bytes()).decode("ascii")
    assert server.ocr_image_base64(f"data:image/png;base64,{encoded}") == ["ok"]


def test_ocr_image_base64_rejects_garbage(stub_ocr):
    with pytest.raises(ValueError, match="Invalid base64"):
        server.ocr_image_base64("@@@@")


def test_ocr_image_url_rejects_file_scheme(stub_ocr):
    with pytest.raises(ValueError, match="http and https"):
        server.ocr_image_url("file:///tmp/a.png")


def test_ocr_image_url_rejects_loopback(stub_ocr):
    with pytest.raises(ValueError, match="not allowed"):
        server.ocr_image_url("http://127.0.0.1:5002/secret")


def test_ocr_image_url_rejects_oversize_content_length(stub_ocr, monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"Content-Length": str(ocr_common.MAX_IMAGE_BYTES + 1)}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=1):
            yield b""

    monkeypatch.setattr(ocr_common.socket, "getaddrinfo", lambda *a, **k: [
        (0, 0, 0, "", ("1.1.1.1", 0))
    ])
    monkeypatch.setattr(server.requests, "get", lambda *a, **k: FakeResponse())
    with pytest.raises(ValueError, match="maximum allowed size"):
        server.ocr_image_url("https://example.com/huge.png")


def test_ocr_image_url_rejects_redirect(stub_ocr, monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {"Location": "http://127.0.0.1/x"}

        def raise_for_status(self):
            raise AssertionError("should not follow redirect")

        def iter_content(self, chunk_size=1):
            yield b""

    monkeypatch.setattr(ocr_common.socket, "getaddrinfo", lambda *a, **k: [
        (0, 0, 0, "", ("1.1.1.1", 0))
    ])
    monkeypatch.setattr(server.requests, "get", lambda *a, **k: FakeResponse())
    with pytest.raises(ValueError, match="redirects are not followed"):
        server.ocr_image_url("https://example.com/a.png")
