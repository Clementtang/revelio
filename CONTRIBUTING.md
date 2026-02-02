# Contributing to Revelio

Thank you for your interest in contributing to Revelio!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/revelio.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
cd revelio

# Install MCP server dependencies
cd src/mcp-server
uv sync

# Test the OCR script
uv run python ocr_to_file.py /path/to/test/image.png
```

## Project Structure

```
revelio/
├── src/
│   ├── mcp-server/    # EasyOCR MCP Server
│   └── skill/         # Claude Code Skill
├── docs/              # Documentation
└── ocr_results/       # OCR output (git-ignored)
```

## Guidelines

### Code Style

- Follow existing code patterns
- Add error handling for all external operations
- Use meaningful variable names
- Keep functions focused and small

### Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) format
- One logical change per commit
- Write clear commit messages

Examples:

- `feat: add Japanese language support`
- `fix: handle missing image file gracefully`
- `docs: update installation instructions`

### Documentation

- Update relevant docs when changing functionality
- Keep both English and Chinese versions in sync
- Update CHANGELOG.md for user-facing changes

## Submitting Changes

1. Ensure your code follows the guidelines above
2. Test your changes locally
3. Update documentation if needed
4. Push to your fork
5. Open a Pull Request with a clear description

## Architecture Decisions

Major changes should be documented in `docs/decisions/` using the ADR format.
See existing ADRs for examples.

## Questions?

Open an issue for discussion before starting major changes.
