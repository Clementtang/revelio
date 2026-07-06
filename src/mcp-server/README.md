# Revelio MCP Server

MCP (Model Context Protocol) server that provides local image OCR (via EasyOCR)
to Claude Code. Results are returned directly to the conversation — for the
privacy-preserving, save-to-file flow use the `/revelio` skill instead.

## Files

| File             | Description                                              |
| ---------------- | ------------------------------------------------------- |
| `server.py`      | Main MCP server implementation                          |
| `ocr_to_file.py` | Standalone script for the privacy-first (save-to-file) flow |
| `ocr_common.py`  | Shared helpers (language/GPU config, image validation)  |
| `pyproject.toml` | Python dependencies                                     |

## Installation

The server is referenced **in place** — no copying required. Add it to
`~/.claude.json` under `mcpServers` (replace `<you>` with your username):

```json
{
  "mcpServers": {
    "revelio": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/<you>/revelio/src/mcp-server",
        "run",
        "server.py"
      ],
      "env": {
        "EASYOCR_LANGUAGES": "ch_tra,en"
      }
    }
  }
}
```

Then restart Claude Code.

## Tools Provided

- `ocr_image_file` — OCR from local file path
- `ocr_image_base64` — OCR from base64 encoded image
- `ocr_image_url` — OCR from URL (http/https only, size-capped)
- `unload_ocr_models` — release cached models to free memory

## Configuration

All configuration is via environment variables (set them in the `env` block above
or in your shell):

| Variable                 | Purpose                                        | Default        |
| ------------------------ | ---------------------------------------------- | -------------- |
| `EASYOCR_LANGUAGES`      | OCR languages (comma-separated)                | `ch_tra,en`    |
| `EASYOCR_GPU`            | Use GPU/MPS acceleration (`true`/`false`)      | `false` (CPU)  |
| `EASYOCR_UNLOAD_TIMEOUT` | Seconds idle before models auto-unload (`0` off) | `0`          |
| `REVELIO_OUTPUT_DIR`     | Output dir for `ocr_to_file.py`                | `~/revelio/ocr_results/` |

Default language: `ch_tra,en` (Traditional Chinese + English). EasyOCR supports
80+ languages — e.g. `EASYOCR_LANGUAGES="ch_tra,en,ja"`.

## Memory Management

EasyOCR/PyTorch are imported lazily on first OCR request and cached. To release
the ~2.6 GB they hold: set `EASYOCR_UNLOAD_TIMEOUT` for automatic idle unload, or
call the `unload_ocr_models` tool. See
[ADR-002](../../docs/decisions/002-memory-management-strategy.md).

## Development

```bash
cd src/mcp-server
uv sync
uv run pytest        # unit tests (do not require EasyOCR)
uv run ruff check .  # lint
```
