"""
Shared helpers for the Revelio EasyOCR MCP server and standalone script.

Kept dependency-light on purpose: this module never imports EasyOCR (and thus
never pulls in PyTorch), so it can be imported cheaply and unit-tested without
the heavy OCR stack installed. EasyOCR is imported lazily by the callers that
actually run recognition.
"""

import io
import os

import numpy as np
from PIL import Image as PILImage

# Cap on remotely fetched images to avoid unbounded downloads (SSRF hardening).
MAX_IMAGE_BYTES = 25 * 1024 * 1024  # 25 MB


def get_default_languages() -> list[str]:
    """Read OCR languages from the EASYOCR_LANGUAGES environment variable.

    Comma-separated, e.g. ``ch_tra,en``. Defaults to ``ch_tra,en``.
    """
    env_languages = os.getenv("EASYOCR_LANGUAGES", "ch_tra,en")
    return [lang.strip() for lang in env_languages.split(",") if lang.strip()]


def get_gpu_flag() -> bool:
    """Whether EasyOCR should use the GPU, from the EASYOCR_GPU environment variable.

    Defaults to ``False`` (CPU) so behaviour is predictable across machines and
    consistent between the MCP server and the standalone script. Set
    ``EASYOCR_GPU=true`` to opt into GPU/MPS acceleration.
    """
    return os.getenv("EASYOCR_GPU", "false").strip().lower() in ("1", "true", "yes", "on")


def get_unload_timeout() -> int:
    """Idle seconds before cached OCR models are auto-unloaded.

    From ``EASYOCR_UNLOAD_TIMEOUT``. ``0`` (the default) disables auto-unload.
    """
    try:
        return max(0, int(os.getenv("EASYOCR_UNLOAD_TIMEOUT", "0")))
    except ValueError:
        return 0


def validate_image_bytes(image_bytes: bytes) -> None:
    """Validate that bytes decode to a supported image, raising ValueError otherwise."""
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
        if pil_image.format is None:
            raise ValueError("Unable to determine image format")
        # verify() detects truncated/corrupt files but consumes the image object.
        pil_image.verify()
    except (PILImage.UnidentifiedImageError, OSError) as e:
        raise ValueError(f"Invalid or unsupported image format: {e}")


def image_bytes_to_array(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes into an RGB numpy array suitable for EasyOCR."""
    pil_image = PILImage.open(io.BytesIO(image_bytes))
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    return np.array(pil_image)
