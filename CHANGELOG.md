# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `benchmark/`: regression benchmark runner with ground truth for the TSMC 2025 Q3 English consolidated statements (0.6.0 baseline: 26/27)
- `benchmark/`: Chinese (CID-font) ground truth for the same filing; force-OCR baseline 12/26 quantifies the visual-OCR fallback quality gap
- `benchmark/`: two-column academic paper (ResNet) and its rasterized scanned-equivalent ground truths; baselines 16/16 vs 12/16 isolate the pure OCR quality loss from layout effects

- `EASYOCR_UNLOAD_JOBDONE` mode: unload OCR models immediately after every call (default off)

### Changed

- Idle auto-unload is now on by default (`EASYOCR_UNLOAD_TIMEOUT` defaults to 300s instead of 0/disabled); malformed values fall back to the default instead of silently disabling
- In-flight guard: models are never unloaded while a recognition is running (a stale idle timer could previously fire mid-call)
- `/revelio --ocr` on a `.pdf` now routes through hybrid `--force-ocr` instead of EasyOCR (which cannot read PDFs)
- Hybrid server is bound to `127.0.0.1`; skill reuses a running server only when its `--force-ocr` flag matches the needed mode
- Skill pre-flight treats `has_encoding_issues` as force-OCR and passes PDF paths via `sys.argv` (no string interpolation into `python3 -c`)
- Image decode applies EXIF orientation and composites alpha onto white before OCR
- Benchmark key-figure checks match full numeric tokens, not substrings
- `ocr_image_url` rejects private/loopback/link-local hosts and HTTP redirects
- Empty `EASYOCR_LANGUAGES` falls back to `ch_tra,en`
- `unload_ocr_models` during an in-flight job now unloads when that job finishes
- Skill Path A resolves the MCP server dir from `REVELIO_MCP_DIR` (default `$HOME/revelio/src/mcp-server`)

### Fixed

- Quoted `~/...` image paths and `REVELIO_OUTPUT_DIR` are expanded instead of treated as a literal `~` directory
- Local image reads share the 25 MB size cap used for URL fetches
- Base64 tool accepts wrapped payloads and `data:*;base64,` data URLs

## [0.6.0] - 2026-08

### Added

- **Pre-flight PDF detection** via [pdf-inspector](https://github.com/firecrawl/pdf-inspector) — before starting the hybrid server, the `/revelio` skill now runs a millisecond structural analysis that detects scanned pages and undecodable text layers (CID fonts without ToUnicode CMap, vector-outlined text) and picks the `--force-ocr` mode up front, replacing the old filename-guess / trial-and-error flow and its 30–40 s server restarts — see [ADR-004](docs/decisions/004-pdf-preflight-detection.md)

### Changed

- The heuristic force-OCR decision (guess from filename, retry after garbled output) is now only a fallback for when pdf-inspector is unavailable

### Fixed

- Pinned ruff in CI to the version locked in `uv.lock` — an unpinned install pulled ruff 0.16.x, whose new rules turned CI red on every PR with no code change

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
| 0.6.0   | 2026-08    | Pre-flight PDF detection (pdf-inspector) |
| 0.5.0   | 2026-04    | PDF support, /revelio rebrand, memory mgmt |
| 0.4.1   | 2026-02-02 | Bug fixes & error handling        |
| 0.4.0   | 2026-02-02 | Source code & bilingual docs      |
| 0.3.0   | 2026-02-02 | Configurable output directory     |
| 0.2.0   | 2026-02-02 | Privacy-first Skill mode          |
| 0.1.0   | 2026-02-02 | Initial MCP Server                |
