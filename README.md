# Revelio

> _Revelio_ — the Revealing Charm from Harry Potter, used to reveal hidden things.

[繁體中文](README.zh-TW.md) | English

A privacy-first local OCR solution powered by EasyOCR. All text recognition happens on your machine — sensitive content never leaves your device.

## Features

- **Privacy First** — All OCR processing runs locally, no cloud uploads
- **Multi-language** — Supports Traditional Chinese (`ch_tra`) and English (`en`)
- **Claude Code Integration** — Dual-mode: MCP Server (fast) and Skill (private)
- **User Control** — In Skill mode, you decide if Claude can read the results

## Quick Start

### Prerequisites

- macOS or Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Claude Code](https://claude.ai/code) CLI

### Installation

1. **Install uv** (if not installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:

```bash
git clone https://github.com/user/revelio.git ~/revelio
cd ~/revelio
```

3. **Configure Claude Code** — Add the MCP server to `~/.claude/settings.json`:

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

4. **Install the Skill** — Copy to skills directory:

```bash
cp -r skills/ocr-local ~/.claude/skills/
```

## Usage

### Mode 1: `/ocr-local` Skill (Privacy Mode)

Best for sensitive documents. Results are saved locally; Claude only reads them with your explicit consent.

```
You: /ocr-local
Claude: Please provide the image path.
You: ~/Documents/contract.jpg
Claude: ✓ OCR complete. Results saved to ~/revelio/ocr_results/...
        Would you like me to read the content?
You: Yes / No
```

### Mode 2: MCP Server (Fast Mode)

Best for general use. Claude directly receives OCR results for immediate processing.

Claude will automatically use the MCP tools when you ask it to read text from images.

## Configuration

### Output Directory

Default: `~/revelio/ocr_results/`

Customize via environment variable:

```bash
export REVELIO_OUTPUT_DIR="/your/custom/path"
```

Priority: CLI argument > Environment variable > Default

### Supported Languages

Currently configured for:

- Traditional Chinese (`ch_tra`)
- English (`en`)

EasyOCR supports 80+ languages. To add more, modify the `EASYOCR_LANGUAGES` environment variable:

```bash
export EASYOCR_LANGUAGES="ch_tra,en,ja"  # Add Japanese
```

## File Locations

| Component   | Path                          |
| ----------- | ----------------------------- |
| MCP Server  | `~/.claude/easyocr-mcp/`      |
| Skill       | `~/.claude/skills/ocr-local/` |
| OCR Results | `~/revelio/ocr_results/`      |

## Documentation

- [Architecture](docs/architecture.md) — System design and data flow
- [Setup Guide](docs/setup.md) — Detailed installation instructions
- [Decision Records](docs/decisions/) — ADRs for major decisions
- [Changelog](CHANGELOG.md) — Version history

## Tech Stack

- **OCR Engine**: [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **Python Runtime**: [uv](https://github.com/astral-sh/uv)
- **Integration**: Claude Code (MCP Protocol + Skills)

## Why "Revelio"?

In the Harry Potter universe, _Revelio_ is a charm that reveals hidden objects, secret messages, and invisible things. This project does the same — it reveals the hidden text within images, while keeping your sensitive content private.

## License

MIT

## Contributing

Contributions are welcome! Please read the [Architecture](docs/architecture.md) document first to understand the dual-mode design philosophy.
