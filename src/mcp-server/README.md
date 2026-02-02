# EasyOCR MCP Server

MCP (Model Context Protocol) server that provides OCR capabilities to Claude Code.

## Files

| File             | Description                             |
| ---------------- | --------------------------------------- |
| `server.py`      | Main MCP server implementation          |
| `ocr_to_file.py` | Standalone script for privacy-first OCR |
| `pyproject.toml` | Python dependencies                     |

## Installation

1. Copy to Claude's MCP directory:

```bash
cp -r . ~/.claude/easyocr-mcp/
```

2. Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "easyocr": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "~/.claude/easyocr-mcp",
        "python",
        "server.py"
      ]
    }
  }
}
```

3. Restart Claude Code.

## Tools Provided

- `ocr_image_file` — OCR from local file path
- `ocr_image_base64` — OCR from base64 encoded image
- `ocr_image_url` — OCR from URL

## Configuration

### Languages

Set `EASYOCR_LANGUAGES` environment variable (comma-separated):

```bash
export EASYOCR_LANGUAGES="ch_tra,en,ja"
```

Default: `ch_tra,en` (Traditional Chinese + English)

### Output Directory (for ocr_to_file.py)

Set `REVELIO_OUTPUT_DIR` environment variable:

```bash
export REVELIO_OUTPUT_DIR="/custom/path"
```

Default: `~/revelio/ocr_results/`
