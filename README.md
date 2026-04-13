# Revelio

![License](https://img.shields.io/github/license/Clementtang/revelio)
![Top Language](https://img.shields.io/github/languages/top/Clementtang/revelio)
![Last Commit](https://img.shields.io/github/last-commit/Clementtang/revelio)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Java](https://img.shields.io/badge/java-11+-orange)

> _Revelio_ — the Revealing Charm from Harry Potter, used to reveal hidden things.

[繁體中文](README.zh-TW.md) | English

A privacy-first local document processing toolkit for Claude Code. Revelio extracts text from images via [EasyOCR](https://github.com/JaidedAI/EasyOCR) and parses PDFs (tables, headings, reading order) via [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf). All processing runs on your machine — sensitive content never leaves your device.

## Features

- **Privacy First** — All processing runs locally, no cloud uploads
- **Two Tools, One Entry Point** — The `/revelio` skill auto-selects based on file type:
  - Images (`.jpg`, `.png`, `.bmp`, `.tiff`, ...) → **EasyOCR**
  - PDFs (`.pdf`) → **opendataloader-pdf** (preserves tables, headings, reading order)
- **Manual Override** — Use `--ocr` or `--pdf` to force a specific tool
- **User Control** — In Skill mode, you decide if Claude can read the results
- **Multi-language** — Traditional Chinese + English by default; both tools support 80+ languages

## Background

Revelio started in early 2026 as a local EasyOCR wrapper for sensitive image OCR. In April 2026 it was extended to cover PDF processing after running into the limits of OCR on structured documents like financial reports, research papers, and contracts. OCR flattens tables into plain text and garbles numeric columns — opendataloader-pdf parses the PDF structure directly, preserving table layouts and numeric precision.

The two tools are complementary, not competing:

- **EasyOCR** (via `src/mcp-server/`) — image and screenshot text extraction
- **opendataloader-pdf** (external, invoked by the skill) — native PDF parsing with optional hybrid OCR for scanned PDFs

## Quick Start

### Prerequisites

- macOS or Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Claude Code](https://claude.ai/code) CLI
- **Java 11+** (required by opendataloader-pdf)

### Installation

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone Revelio**:

   ```bash
   git clone https://github.com/Clementtang/revelio.git ~/revelio
   cd ~/revelio
   ```

3. **Configure the EasyOCR MCP server** — Add to `~/.claude.json` under `mcpServers`:

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

4. **Install the skill**:

   ```bash
   cp -r src/skill ~/.claude/skills/revelio
   ```

5. **Install opendataloader-pdf** (for PDF support):

   ```bash
   python3 -m venv ~/odl-env
   source ~/odl-env/bin/activate
   pip install -U "opendataloader-pdf[hybrid]"
   ```

## Usage

### `/revelio` Skill — Unified Entry Point

Start in Claude Code and let the skill auto-detect:

```
You: /revelio ~/Documents/receipt.jpg
Claude: [auto-selects EasyOCR] Running local OCR...
        Results saved to ~/revelio/ocr_results/receipt_<timestamp>.txt
        Would you like me to read the content?

You: /revelio ~/reports/financial_report.pdf
Claude: [auto-selects opendataloader-pdf] Converting PDF...
        Results saved to ~/odl-output/financial_report/
        Would you like me to read the content?

You: /revelio --ocr ~/scanned_page.png
Claude: [forced to EasyOCR] Running local OCR...
```

Results are saved locally and Claude only reads them with your explicit consent.

### MCP Server — Direct OCR for Images

For non-sensitive image OCR, Claude can call the MCP tools directly without the privacy prompt. Just ask Claude to read text from an image.

## Configuration

### Output Directories

| Tool               | Default Output           |
| ------------------ | ------------------------ |
| EasyOCR            | `~/revelio/ocr_results/` |
| opendataloader-pdf | `~/odl-output/`          |

Customize EasyOCR output via `REVELIO_OUTPUT_DIR`:

```bash
export REVELIO_OUTPUT_DIR="/your/custom/path"
```

### Supported Languages

Default: Traditional Chinese (`ch_tra`) + English (`en`). EasyOCR supports 80+ languages — set `EASYOCR_LANGUAGES`:

```bash
export EASYOCR_LANGUAGES="ch_tra,en,ja"
```

opendataloader-pdf hybrid mode also supports 80+ OCR languages for scanned PDFs.

## Project Structure

```
revelio/
├── src/
│   ├── mcp-server/      # EasyOCR MCP server
│   │   ├── server.py
│   │   ├── ocr_to_file.py
│   │   └── pyproject.toml
│   └── skill/           # /revelio skill (routes to OCR or PDF tool)
│       └── SKILL.md
├── ocr_results/         # EasyOCR output (git-ignored)
└── docs/                # Documentation (architecture, ADRs)
```

## Installed Locations

| Component               | Installed Path                                       | Source                                   |
| ----------------------- | ---------------------------------------------------- | ---------------------------------------- |
| MCP server              | Referenced in-place from `~/revelio/src/mcp-server/` | `src/mcp-server/`                        |
| Skill                   | `~/.claude/skills/revelio/`                          | `src/skill/`                             |
| OCR results             | `~/revelio/ocr_results/`                             | —                                        |
| PDF output              | `~/odl-output/`                                      | —                                        |
| opendataloader-pdf venv | `~/odl-env/`                                         | `pip install opendataloader-pdf[hybrid]` |

## Documentation

- [Architecture](docs/architecture.md) — System design and data flow
- [Setup Guide](docs/setup.md) — Detailed installation instructions
- [Decision Records](docs/decisions/) — ADRs for major decisions
- [Changelog](CHANGELOG.md) — Version history

## Tech Stack

- **OCR engine**: [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **PDF parser**: [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) (Java 11+ required)
- **Python runtime**: [uv](https://github.com/astral-sh/uv)
- **Integration**: Claude Code (MCP Protocol + Skills)

## Example Output

Below is a real output from [TSMC's 2025 Q3 Consolidated Financial Statements](https://investor.tsmc.com/english/quarterly-results/2025/q3) (public filing), converted by opendataloader-pdf in **hybrid mode**.

**Income statement** — converted into a structured Markdown table with accurate numbers and proper column separation:

|                            | 2025 Q3 Amount | %   | 2024 Q3 Amount | %   | 2025 9M Amount  | %   | 2024 9M Amount  | %   |
| -------------------------- | -------------- | --- | -------------- | --- | --------------- | --- | --------------- | --- |
| NET REVENUE                | $ 989,918,318  | 100 | $ 759,692,143  | 100 | $ 2,762,963,851 | 100 | $ 2,025,846,521 | 100 |
| COST OF REVENUE            | 401,375,489    | 41  | 320,346,477    | 42  | 1,133,656,708   | 41  | 913,871,108     | 45  |
| GROSS PROFIT               | 588,542,829    | 59  | 439,345,666    | 58  | 1,629,307,143   | 59  | 1,111,975,413   | 55  |
| Research and development   | 63,742,245     | 6   | 52,783,826     | 7   | 181,569,457     | 7   | 146,950,466     | 7   |
| General and administrative | 20,048,234     | 2   | 22,890,591     | 3   | 63,887,355      | 2   | 58,317,959      | 3   |
| Marketing                  | 3,973,966      | -   | 3,404,487      | 1   | 12,002,028      | -   | 9,463,070       | 1   |
| Total operating expenses   | 87,764,445     | 8   | 79,078,904     | 11  | 257,458,840     | 9   | 214,731,495     | 11  |
| INCOME FROM OPERATIONS     | 500,684,818    | 51  | 360,766,289    | 47  | 1,371,189,264   | 50  | 896,340,137     | 44  |
| INCOME BEFORE INCOME TAX   | 525,369,023    | 53  | 384,186,852    | 51  | 1,449,299,639   | 52  | 957,040,631     | 47  |
| INCOME TAX EXPENSE         | 73,613,661     | 7   | 59,106,682     | 8   | 239,318,192     | 8   | 159,077,760     | 8   |
| NET INCOME                 | 451,755,362    | 46  | 325,080,170    | 43  | 1,209,981,447   | 44  | 797,962,871     | 39  |

> Note: Hybrid mode (`--hybrid docling-fast --hybrid-mode full`) is required for borderless financial tables. The basic mode flattens these into unstructured paragraph text.

## History

- **2026-04** — Merged PDF processing via opendataloader-pdf; renamed skill from `/ocr-local` to `/revelio` and MCP server from `easyocr` to `revelio`
- **2026-02** — Attempted upstream contribution to [WindoC/easyocr-mcp](https://github.com/WindoC/easyocr-mcp) (stalled). The [Clementtang/easyocr-mcp fork](https://github.com/Clementtang/easyocr-mcp) is now archived; Revelio maintains its own MCP server implementation. See [ADR-002](docs/decisions/002-memory-management-strategy.md) for context.

## Why "Revelio"?

In the Harry Potter universe, _Revelio_ is a charm that reveals hidden objects, secret messages, and invisible things. This project does the same — it reveals the hidden text and structure within documents, while keeping your sensitive content private.

## License

MIT

## Contributing

Contributions are welcome. Please read the [Architecture](docs/architecture.md) document first to understand the design philosophy.
