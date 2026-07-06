# Revelio Skill

Privacy-first document processing skill for Claude Code. A single entry point
(`/revelio`) that auto-routes by file type — images to EasyOCR, PDFs to
opendataloader-pdf. Results are saved locally and Claude only reads them with
explicit user consent.

## Files

| File       | Description                                  |
| ---------- | -------------------------------------------- |
| `SKILL.md` | Skill definition (workflow and instructions) |

## Installation

Copy to Claude's skills directory:

```bash
cp -r . ~/.claude/skills/revelio
```

Claude Code will automatically detect the skill on next session.

## Usage

In Claude Code, type `/revelio` with a file path:

```
/revelio ~/Documents/receipt.jpg     # image → EasyOCR
/revelio ~/reports/financial.pdf     # PDF   → opendataloader-pdf
/revelio --ocr ~/scanned_page.png    # force EasyOCR
/revelio --pdf ~/document.pdf        # force opendataloader-pdf
```

Then:

1. The skill routes to the right engine and runs it locally.
2. Results are saved to disk (`~/revelio/ocr_results/` for images,
   `~/odl-output/` for PDFs).
3. You choose whether to let Claude read the results.

## Privacy Guarantee

- All processing runs locally (EasyOCR / opendataloader-pdf)
- Claude **does not** read results automatically
- User must explicitly consent before Claude accesses the content

See the [architecture doc](../../docs/architecture.md) for how routing and the
two engines fit together.
