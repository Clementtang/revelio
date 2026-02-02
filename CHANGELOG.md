# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.3.0] - 2025-02-02

### Changed

- OCR results now stored in `~/revelio/ocr_results/` instead of `~/.claude/ocr_results/`
- Output directory is configurable via `REVELIO_OUTPUT_DIR` environment variable
- Configuration priority: CLI argument > environment variable > default

### Added

- `ocr_results/` directory in project folder with `.gitkeep`
- `.gitignore` rules to exclude OCR result files (may contain sensitive data)

## [0.2.0] - 2025-02-02

### Added

- `/ocr-local` Skill for privacy-first OCR workflow
  - Results saved to local file instead of returning to Claude
  - User must explicitly consent before Claude reads the content
  - Located at `~/.claude/skills/ocr-local/SKILL.md`

### Changed

- Established dual-mode architecture: MCP (fast) vs Skill (private)

## [0.1.0] - 2025-02-02

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

| Version | Date       | Highlights                    |
| ------- | ---------- | ----------------------------- |
| 0.3.0   | 2025-02-02 | Configurable output directory |
| 0.2.0   | 2025-02-02 | Privacy-first Skill mode      |
| 0.1.0   | 2025-02-02 | Initial MCP Server            |
