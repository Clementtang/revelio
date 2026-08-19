"""Revelio EasyOCR MCP server.

Exposes local OCR to Claude Code over the Model Context Protocol. Results are
returned directly to the conversation, so this server is intended for
non-sensitive images; the privacy-preserving flow lives in the /revelio skill.

EasyOCR (and PyTorch) are imported lazily on first use and can be released again
via idle auto-unload or the ``unload_ocr_models`` tool — see ADR-002.
"""

import threading

import requests
from mcp.server.fastmcp import FastMCP

from ocr_common import (
    MAX_IMAGE_BYTES,
    assert_public_http_url,
    decode_base64_image,
    get_default_languages,
    get_gpu_flag,
    get_unload_jobdone,
    get_unload_timeout,
    image_bytes_to_array,
    read_local_image,
    validate_image_bytes,
)

# Create an MCP server
mcp = FastMCP("Revelio")

# Reader cache, idle timer, in-flight count, and deferred-unload flag share
# this lock so a background Timer cannot collect mid-inference.
_reader_cache = {}
_reader_lock = threading.Lock()
_unload_timer: threading.Timer | None = None
_in_flight = 0
_unload_when_idle = False


def _cancel_unload_timer() -> None:
    global _unload_timer
    with _reader_lock:
        timer = _unload_timer
        _unload_timer = None
    if timer is not None:
        timer.cancel()


def _schedule_unload() -> None:
    """(Re)arm the idle auto-unload timer if EASYOCR_UNLOAD_TIMEOUT is set."""
    global _unload_timer
    timeout = get_unload_timeout()
    with _reader_lock:
        if _unload_timer is not None:
            _unload_timer.cancel()
            _unload_timer = None
        if timeout > 0:
            _unload_timer = threading.Timer(timeout, _unload_readers)
            _unload_timer.daemon = True
            _unload_timer.start()


def _unload_readers() -> int:
    """Drop cached readers and force garbage collection. Returns count freed.

    No-op while an OCR call is in flight: a stale timer must not trigger
    gc.collect() underneath a running inference.
    """
    import gc

    with _reader_lock:
        if _in_flight > 0:
            return 0
        freed = len(_reader_cache)
        _reader_cache.clear()
    gc.collect()
    return freed


def _job_start() -> None:
    """Mark an OCR call in flight and disarm any pending unload timer."""
    global _in_flight
    with _reader_lock:
        _in_flight += 1
    _cancel_unload_timer()


def _job_done() -> None:
    """Mark an OCR call finished (success or failure) and re-arm unloading."""
    global _in_flight, _unload_when_idle
    with _reader_lock:
        _in_flight = max(0, _in_flight - 1)
        idle = _in_flight == 0
        pending = _unload_when_idle
        if idle and pending:
            _unload_when_idle = False
    if not idle:
        return
    if pending or get_unload_jobdone():
        _unload_readers()
    else:
        _schedule_unload()


def get_reader(languages: list[str]):
    """Get or create a cached EasyOCR reader for the given languages.

    EasyOCR is imported here (not at module load) so the heavy PyTorch stack is
    only paid for when OCR is actually requested.
    """
    cache_key = tuple(sorted(languages))
    with _reader_lock:
        reader = _reader_cache.get(cache_key)
        if reader is None:
            try:
                import easyocr

                reader = easyocr.Reader(languages, gpu=get_gpu_flag())
                _reader_cache[cache_key] = reader
            except Exception as e:
                raise ValueError(
                    f"Failed to create EasyOCR reader for languages {languages}: {e}"
                )
    return reader


def _run_ocr(
    image,
    detail: int,
    paragraph: bool,
    width_ths: float,
    height_ths: float,
) -> list:
    """Run EasyOCR on an RGB numpy array under in-flight protection."""
    _job_start()
    try:
        reader = get_reader(get_default_languages())
        return reader.readtext(
            image,
            detail=detail,
            paragraph=paragraph,
            width_ths=width_ths,
            height_ths=height_ths,
        )
    finally:
        _job_done()


@mcp.tool(title="OCR Image from Base64")
def ocr_image_base64(
    base64_image: str,
    detail: int = 1,
    paragraph: bool = False,
    width_ths: float = 0.7,
    height_ths: float = 0.7,
) -> list:
    """
    Performs OCR on a base64 encoded image using EasyOCR.

    Args:
        base64_image: Base64 encoded image string
        detail: 0 for text only, 1 for full details with coordinates and confidence
        paragraph: Enable paragraph detection
        width_ths: Text width threshold for merging
        height_ths: Text height threshold for merging

    Returns:
        EasyOCR native output format:
        - detail=1: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], 'text', confidence), ...]
        - detail=0: ['text1', 'text2', ...]
    """
    try:
        image_bytes = decode_base64_image(base64_image)
        validate_image_bytes(image_bytes)
        image_array = image_bytes_to_array(image_bytes)
        return _run_ocr(image_array, detail, paragraph, width_ths, height_ths)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error performing OCR: {e}")


@mcp.tool(title="OCR Image from File")
def ocr_image_file(
    image_path: str,
    detail: int = 1,
    paragraph: bool = False,
    width_ths: float = 0.7,
    height_ths: float = 0.7,
) -> list:
    """
    Performs OCR on an image file using EasyOCR.

    Args:
        image_path: Path to the image file (full path; ``~`` is expanded)
        detail: 0 for text only, 1 for full details with coordinates and confidence
        paragraph: Enable paragraph detection
        width_ths: Text width threshold for merging
        height_ths: Text height threshold for merging

    Returns:
        EasyOCR native output format:
        - detail=1: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], 'text', confidence), ...]
        - detail=0: ['text1', 'text2', ...]
    """
    try:
        image_bytes = read_local_image(image_path)
        validate_image_bytes(image_bytes)
        image_array = image_bytes_to_array(image_bytes)
        return _run_ocr(image_array, detail, paragraph, width_ths, height_ths)
    except FileNotFoundError as e:
        raise ValueError(str(e))
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error performing OCR: {e}")


@mcp.tool(title="OCR Image from URL")
def ocr_image_url(
    image_url: str,
    detail: int = 1,
    paragraph: bool = False,
    width_ths: float = 0.7,
    height_ths: float = 0.7,
) -> list:
    """
    Performs OCR on an image from a URL using EasyOCR.

    Args:
        image_url: Public http/https URL of the image. Redirects and private
            or loopback hosts are rejected.
        detail: 0 for text only, 1 for full details with coordinates and confidence
        paragraph: Enable paragraph detection
        width_ths: Text width threshold for merging
        height_ths: Text height threshold for merging

    Returns:
        EasyOCR native output format:
        - detail=1: [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], 'text', confidence), ...]
        - detail=0: ['text1', 'text2', ...]
    """
    try:
        assert_public_http_url(image_url)

        try:
            response = requests.get(
                image_url, timeout=30, stream=True, allow_redirects=False
            )
            if 300 <= response.status_code < 400:
                raise ValueError("URL redirects are not followed")
            response.raise_for_status()

            # Reject oversized payloads up front when the server advertises a size.
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) > MAX_IMAGE_BYTES:
                raise ValueError("Image exceeds the maximum allowed size")

            # Stream with a hard cap so a missing/incorrect Content-Length can't
            # be used to force an unbounded download.
            image_bytes = b""
            for chunk in response.iter_content(chunk_size=64 * 1024):
                image_bytes += chunk
                if len(image_bytes) > MAX_IMAGE_BYTES:
                    raise ValueError("Image exceeds the maximum allowed size")
        except requests.RequestException as e:
            raise ValueError(f"Failed to download image from URL: {e}")

        validate_image_bytes(image_bytes)
        image_array = image_bytes_to_array(image_bytes)
        return _run_ocr(image_array, detail, paragraph, width_ths, height_ths)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error performing OCR: {e}")


@mcp.tool(title="Unload OCR Models")
def unload_ocr_models() -> str:
    """Release cached EasyOCR models to free memory (~2.6 GB RAM per language set).

    Models reload automatically on the next OCR request. If a recognition is
    in flight, unload is deferred until that call finishes. See ADR-002.
    """
    global _unload_when_idle
    _cancel_unload_timer()
    with _reader_lock:
        in_flight = _in_flight
        if in_flight > 0:
            _unload_when_idle = True
    freed = _unload_readers()
    if freed == 0 and in_flight > 0:
        return "OCR in progress; models will unload when the current job finishes."
    return f"Unloaded {freed} cached OCR reader(s)."


if __name__ == "__main__":
    mcp.run()
