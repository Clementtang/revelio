# Table verification

Optional post-conversion check (PRD Feature 1). Independently re-reads table
regions of the source PDF with surya v2 and flags numbers that disagree with
the converted markdown. It never rewrites the conversion output.

Runs inside `~/surya-env` (see `docs/research/surya-v2-local-test.md`):

```bash
source ~/surya-env/bin/activate
SURYA_GUIDED_LAYOUT=false python3 verify_tables.py doc.pdf doc.md -o report.md
```

The `/revelio` skill offers this as step B-3 after a PDF conversion.
