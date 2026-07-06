# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.5.0] - 2026-04

### Added

- **PDF processing** via [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) — parses tables, headings and reading order, with optional hybrid OCR for scanned/CID-font PDFs
- `unload_ocr_models` MCP tool and `EASYOCR_UNLOAD_TIMEOUT` idle auto-unload to release EasyOCR/PyTorch memory (~2.6 GB) — see [ADR-002](docs/decisions/002-memory-management-strategy.md)
- `EASYOCR_GPU` environment variable to control GPU/MPS usage, shared by the MCP server and the standalone script (default CPU)
- Shared `ocr_common.py` module (language/GPU config, image validation) used by both `server.py` and `ocr_to_file.py`
- [ADR-003](docs/decisions/003-pdf-processing-architecture.md) documenting the dual-engine PDF architecture
- Unit tests, ruff config, and a GitHub Actions CI workflow

### Changed

- **Renamed** the skill `/ocr-local` → `/revelio` and the MCP server `easyocr` → `revelio`; the server is now referenced in place from `~/revelio/src/mcp-server/` (no copy into `~/.claude/`)
- Hybrid mode is now the default for PDF processing
- EasyOCR is imported lazily on first use instead of at server startup
- Deduplicated the three OCR tools in `server.py` behind a shared helper

### Fixed

- Hardened `ocr_image_url` against SSRF/oversized downloads (http/https only, size cap)
- Documentation (`architecture.md`, `setup.md`, component READMEs) updated to match the current dual-engine design and install paths
- Corrected changelog/ADR dates from 2025 to 2026

## [0.4.1] - 2026-02-02

### Fixed

- Correct skill installation path in README (`src/skill` instead of `skills/ocr-local`)
- Align Python version requirement (>=3.11) between pyproject.toml and documentation
- Update outdated `~/.claude/ocr_results/` paths to `~/revelio/ocr_results/` in docs

### Added

- LICENSE file (MIT)
- CONTRIBUTING.md with development guidelines
- Error handling in `ocr_to_file.py`:
  - Validate image file exists
  - Handle EasyOCR initialization errors
  - Handle file write errors

### Changed

- Update pyproject.toml metadata (name, version, description)
- Update minimum dependency versions (pillow, requests, numpy, mcp)

## [0.4.0] - 2026-02-02

### Added

- Source code now included in repository
  - `src/mcp-server/`: EasyOCR MCP Server implementation
  - `src/skill/`: Claude Code Skill definition
- README files for each source component with installation instructions
- Bilingual documentation (English + Traditional Chinese)
  - `README.md` / `README.zh-TW.md`
  - `CHANGELOG.md` / `CHANGELOG.zh-TW.md`

### Changed

- Updated project structure documentation

## [0.3.0] - 2026-02-02

### Changed

- OCR results now stored in `~/revelio/ocr_results/` instead of `~/.claude/ocr_results/`
- Output directory is configurable via `REVELIO_OUTPUT_DIR` environment variable
- Configuration priority: CLI argument > environment variable > default

### Added

- `ocr_results/` directory in project folder with `.gitkeep`
- `.gitignore` rules to exclude OCR result files (may contain sensitive data)

## [0.2.0] - 2026-02-02

### Added

- `/ocr-local` Skill for privacy-first OCR workflow
  - Results saved to local file instead of returning to Claude
  - User must explicitly consent before Claude reads the content
  - Located at `~/.claude/skills/ocr-local/SKILL.md`

### Changed

- Established dual-mode architecture: MCP (fast) vs Skill (private)

## [0.1.0] - 2026-02-02

### Added

- Initial EasyOCR MCP Server setup
  - `ocr_image_file`: OCR from local file path
  - `ocr_image_base64`: OCR from base64 encoded image
  - `ocr_image_url`: OCR from URL
- Support for Traditional Chinese (`ch_tra`) + English (`en`)
- Local Python script `ocr_to_file.py` for standalone usage
- Results directory at `~/.claude/ocr_results/`

### Technical Details

- MCP Server location: `~/.claude/easyocr-mcp/`
- Uses `uv` for Python dependency management
- EasyOCR runs locally, no cloud API calls

---

## Version History Summary

| Version | Date       | Highlights                        |
| ------- | ---------- | --------------------------------- |
| 0.5.0   | 2026-04    | PDF support, /revelio rebrand, memory mgmt |
| 0.4.1   | 2026-02-02 | Bug fixes & error handling        |
| 0.4.0   | 2026-02-02 | Source code & bilingual docs      |
| 0.3.0   | 2026-02-02 | Configurable output directory     |
| 0.2.0   | 2026-02-02 | Privacy-first Skill mode          |
| 0.1.0   | 2026-02-02 | Initial MCP Server                |
