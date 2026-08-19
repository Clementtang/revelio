"""
Shared helpers for the Revelio EasyOCR MCP server and standalone script.

Kept dependency-light on purpose: this module never imports EasyOCR (and thus
never pulls in PyTorch), so it can be imported cheaply and unit-tested without
the heavy OCR stack installed. EasyOCR is imported lazily by the callers that
actually run recognition.
"""

import base64
import io
import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from PIL import Image as PILImage
from PIL import ImageOps

# Cap on image payloads (remote fetch and local read) so a huge file cannot OOM
# the long-lived MCP process that already holds ~2.6 GB of OCR models.
MAX_IMAGE_BYTES = 25 * 1024 * 1024  # 25 MB

DEFAULT_LANGUAGES = ["ch_tra", "en"]


def get_default_languages() -> list[str]:
    """Read OCR languages from the EASYOCR_LANGUAGES environment variable.

    Comma-separated, e.g. ``ch_tra,en``. Defaults to ``ch_tra,en``.
    An empty or punctuation-only value falls back to the default rather than
    handing EasyOCR an empty language list (which fails at Reader init).
    """
    env_languages = os.getenv("EASYOCR_LANGUAGES", "ch_tra,en")
    languages = [lang.strip() for lang in env_languages.split(",") if lang.strip()]
    return languages or list(DEFAULT_LANGUAGES)


def get_gpu_flag() -> bool:
    """Whether EasyOCR should use the GPU, from the EASYOCR_GPU environment variable.

    Defaults to ``False`` (CPU) so behaviour is predictable across machines and
    consistent between the MCP server and the standalone script. Set
    ``EASYOCR_GPU=true`` to opt into GPU/MPS acceleration.
    """
    return os.getenv("EASYOCR_GPU", "false").strip().lower() in ("1", "true", "yes", "on")


DEFAULT_UNLOAD_TIMEOUT = 300


def get_unload_timeout() -> int:
    """Idle seconds before cached OCR models are auto-unloaded.

    From ``EASYOCR_UNLOAD_TIMEOUT``. Defaults to 300; ``0`` disables auto-unload.
    A malformed value falls back to the default rather than silently disabling.
    """
    try:
        return max(0, int(os.getenv("EASYOCR_UNLOAD_TIMEOUT", str(DEFAULT_UNLOAD_TIMEOUT))))
    except ValueError:
        return DEFAULT_UNLOAD_TIMEOUT


def get_unload_jobdone() -> bool:
    """Whether to unload models right after every OCR call, from ``EASYOCR_UNLOAD_JOBDONE``.

    Defaults to ``False``; more aggressive than the idle timeout, useful when OCR
    is a one-off in an otherwise long-lived session.
    """
    return os.getenv("EASYOCR_UNLOAD_JOBDONE", "false").strip().lower() in ("1", "true", "yes", "on")


def expand_user_path(path: str) -> str:
    """Expand a leading ``~`` so quoted home-relative paths resolve."""
    return str(Path(path).expanduser())


def read_local_image(path: str) -> bytes:
    """Expand ``~``, require a regular file within the size cap, and return bytes."""
    resolved = expand_user_path(path)
    if not os.path.isfile(resolved):
        if os.path.exists(resolved):
            raise ValueError(f"The path '{resolved}' is not a file.")
        raise FileNotFoundError(f"The file '{resolved}' was not found.")
    size = os.path.getsize(resolved)
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the maximum allowed size")
    with open(resolved, "rb") as handle:
        return handle.read()


def decode_base64_image(payload: str) -> bytes:
    """Decode a raw, whitespace-wrapped, or ``data:*;base64,`` image payload."""
    text = payload.strip()
    header, separator, rest = text.partition(",")
    if separator and header.lower().startswith("data:") and ";base64" in header.lower():
        text = rest
    text = "".join(text.split())
    if not text:
        raise ValueError("Invalid base64 string: empty payload")
    text = text + "=" * (-len(text) % 4)
    try:
        return base64.b64decode(text, validate=True)
    except Exception as exc:
        raise ValueError(f"Invalid base64 string: {exc}") from exc


def _is_blocked_ip(ip: str) -> bool:
    address = ipaddress.ip_address(ip)
    candidates = [address]
    mapped = getattr(address, "ipv4_mapped", None)
    if mapped is not None:
        candidates.append(mapped)
    return any(
        item.is_private
        or item.is_loopback
        or item.is_link_local
        or item.is_multicast
        or item.is_reserved
        or item.is_unspecified
        for item in candidates
    )


def _resolve_host_ips(hostname: str) -> list[str]:
    try:
        return [str(ipaddress.ip_address(hostname))]
    except ValueError:
        pass
    if hostname.isdigit():
        number = int(hostname)
        if 0 <= number <= 0xFFFFFFFF:
            return [str(ipaddress.IPv4Address(number))]
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Failed to resolve URL host: {exc}") from exc
    return [info[4][0] for info in infos]


def assert_public_http_url(url: str) -> None:
    """Reject non-http(s) URLs and hosts that resolve to private or loopback IPs."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are supported")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL is missing a hostname")
    for ip in _resolve_host_ips(hostname):
        if _is_blocked_ip(ip):
            raise ValueError("URL host is not allowed")


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
    """Decode image bytes into an upright RGB numpy array suitable for EasyOCR.

    Applies EXIF orientation and composites alpha onto white. Flattening RGBA
    onto black (PIL's default ``convert("RGB")``) turns light text on a
    transparent background into black-on-black.
    """
    pil_image = PILImage.open(io.BytesIO(image_bytes))
    transposed = ImageOps.exif_transpose(pil_image)
    if transposed is not None:
        pil_image = transposed
    has_alpha = pil_image.mode in ("RGBA", "LA") or (
        pil_image.mode == "P" and "transparency" in pil_image.info
    )
    if has_alpha:
        rgba = pil_image.convert("RGBA")
        background = PILImage.new("RGBA", rgba.size, (255, 255, 255, 255))
        pil_image = PILImage.alpha_composite(background, rgba).convert("RGB")
    elif pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    return np.array(pil_image)
