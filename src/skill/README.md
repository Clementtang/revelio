# OCR Local Skill

Privacy-first OCR skill for Claude Code. Results are saved locally and Claude only reads them with explicit user consent.

## Files

| File       | Description                                  |
| ---------- | -------------------------------------------- |
| `SKILL.md` | Skill definition (workflow and instructions) |

## Installation

Copy to Claude's skills directory:

```bash
cp -r . ~/.claude/skills/ocr-local/
```

Claude Code will automatically detect the skill on next session.

## Usage

In Claude Code, type:

```
/ocr-local
```

Then follow the prompts to:

1. Provide an image path
2. Wait for OCR to complete
3. Choose whether to let Claude read the results

## Privacy Guarantee

- OCR runs locally via EasyOCR
- Results saved to `~/revelio/ocr_results/`
- Claude **does not** read results automatically
- User must explicitly consent before Claude accesses the content
