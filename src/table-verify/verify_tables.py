#!/usr/bin/env python3
"""Table verification layer: flag suspect numbers in a converted document.

Cross-checks the numeric cells of a conversion output (markdown) against
an independent read of the source PDF by surya v2 (layout detection to
find tables, recognition on the cropped regions). Numbers the two
engines disagree on are flagged for manual review; nothing is corrected
automatically (PRD Feature 1, rulings of 2026-08-20).

Runs inside the surya venv (needs surya-ocr, pymupdf, Pillow), for
example:

    source ~/surya-env/bin/activate
    SURYA_GUIDED_LAYOUT=false python3 verify_tables.py doc.pdf doc.md -o report.md

SURYA_GUIDED_LAYOUT=false works around a grammar bug between surya's
guided decoding and brew-installed llama.cpp (see
docs/research/surya-v2-local-test.md).
"""

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

NUMBER_TOKEN = re.compile(r"-?\d+(?:\.\d+)?")
THOUSANDS_COMMA = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
TAG = re.compile(r"<[^>]+>")


def normalize(text: str) -> str:
    """Numeric normalization: drop $ and thousands commas; () becomes leading minus.

    Unlike run_benchmark.normalize this keeps spaces: stripping them here
    would glue adjacent numbers ("70.4 84.9" -> "70.484.9") and produce
    tokens that exist in neither engine's output.
    """
    text = THOUSANDS_COMMA.sub("", text.replace("$", ""))
    return re.sub(r"\((\d+(?:\.\d+)?)\)", r"-\1", text)


def numeric_tokens(text: str) -> list[str]:
    """Numeric tokens worth verifying; single digits are dropped as noise."""
    return [t for t in NUMBER_TOKEN.findall(normalize(text)) if not re.fullmatch(r"-?\d", t)]


def markdown_table_numbers(md_text: str) -> list[dict]:
    """Numeric tokens from pipe-table rows, with enough context to report on."""
    entries = []
    table_idx = -1
    in_table = False
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            if re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", stripped):
                continue
            if not in_table:
                in_table = True
                table_idx += 1
            for token in numeric_tokens(stripped):
                entries.append({"token": token, "table": table_idx, "row": stripped})
        else:
            in_table = False
    return entries


def surya_read_pdf(pdf_path: str, dpi: int, pages: list[int] | None) -> tuple[dict[str, float], int]:
    """Independent read: numeric tokens found in table regions, with min confidence seen."""
    import pymupdf
    from PIL import Image

    from surya.inference import SuryaInferenceManager
    from surya.layout import LayoutPredictor
    from surya.recognition import RecognitionPredictor

    doc = pymupdf.open(pdf_path)
    page_indexes = pages if pages is not None else list(range(doc.page_count))

    manager = SuryaInferenceManager()
    layout = LayoutPredictor(manager)
    recognize = RecognitionPredictor(manager)

    tokens: dict[str, float] = {}
    tables_seen = 0
    for index in page_indexes:
        pix = doc[index].get_pixmap(dpi=dpi)
        page_image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        boxes = [b for b in layout([page_image])[0].bboxes if b.label == "Table"]
        if not boxes:
            continue
        crops = [page_image.crop([int(v) for v in b.bbox]) for b in boxes]
        for result in recognize(crops):
            tables_seen += 1
            blocks = getattr(result, "blocks", None) or getattr(result, "text_lines", [])
            for block in blocks:
                text = getattr(block, "html", None) or getattr(block, "text", "") or ""
                confidence = getattr(block, "confidence", None)
                for token in numeric_tokens(html.unescape(TAG.sub(" ", text))):
                    known = tokens.get(token)
                    score = confidence if confidence is not None else 1.0
                    tokens[token] = score if known is None else min(known, score)
        print(f"  page {index + 1}: {len(boxes)} table(s)", file=sys.stderr, flush=True)
    return tokens, tables_seen


def decimal_loss_candidates(token: str, surya_tokens: dict[str, float]) -> list[str]:
    """Surya numbers whose digits match the token with a decimal point restored."""
    return [
        other
        for other in surya_tokens
        if "." in other and other.replace(".", "") == token and other != token
    ]


UNVERIFIABLE_RATIO = 0.5
UNVERIFIABLE_MIN_NUMBERS = 10


def build_report(
    pdf_path: str, md_path: str, entries: list[dict], surya_tokens: dict[str, float], tables_seen: int
) -> tuple[str, int]:
    per_table: dict[int, list[dict]] = {}
    for entry in entries:
        per_table.setdefault(entry["table"], []).append(entry)

    # A table surya mostly could not confirm was probably never read (layout
    # miss, or a layout too dense for the model). Listing every number there
    # would drown the precise signals, so collapse it to one table-level flag.
    unverifiable = []
    suspects = []
    for table_idx, table_entries in per_table.items():
        unconfirmed = [e for e in table_entries if e["token"] not in surya_tokens]
        ratio = len(unconfirmed) / len(table_entries)
        if len(table_entries) >= UNVERIFIABLE_MIN_NUMBERS and ratio >= UNVERIFIABLE_RATIO:
            unverifiable.append(
                {
                    "table": table_idx,
                    "total": len(table_entries),
                    "unconfirmed": len(unconfirmed),
                    "row": table_entries[0]["row"],
                }
            )
            continue
        for entry in unconfirmed:
            hints = [
                f"{c}（信心 {surya_tokens[c]:.2f}）"
                for c in decimal_loss_candidates(entry["token"], surya_tokens)
            ]
            suspects.append({**entry, "hint": hints})

    unmatched_surya = sorted(
        token for token in surya_tokens if all(e["token"] != token for e in entries)
    )

    lines = [
        "# 表格數字驗證報告",
        "",
        f"來源 PDF：`{pdf_path}`",
        f"轉換輸出：`{md_path}`",
        f"驗證引擎：surya v2（獨立辨識 {tables_seen} 個表格區域，讀到 {len(surya_tokens)} 個相異數字）",
        f"轉換輸出的表格數字：{len(entries)} 個（相異值 {len({e['token'] for e in entries})} 個）",
        "",
        "此報告只標記可疑數字，不修改轉換輸出。可疑代表兩個引擎讀出的結果不一致，",
        "需要人工對照原始 PDF 判定哪邊正確。",
        "",
    ]
    if suspects:
        lines += [
            f"## 可疑數字（{len(suspects)} 筆）",
            "",
            "| 數字 | 表格 # | 所在列（節錄） | 線索 |",
            "| --- | --- | --- | --- |",
        ]
        for s in suspects:
            row = s["row"][:80].replace("|", "\\|")
            hint = f"疑似小數點丟失，surya 讀到 {', '.join(s['hint'])}" if s["hint"] else ""
            lines.append(f"| `{s['token']}` | {s['table']} | {row} | {hint} |")
    else:
        lines.append("## 可疑數字：無")
    if unverifiable:
        lines += [
            "",
            f"## 無法交叉驗證的表格（{len(unverifiable)} 個）",
            "",
            "以下表格過半數字無法被 surya 確認，通常代表版面偵測沒有讀到對應區域，",
            "或表格密度超出驗證模型能力。整表需人工抽查，逐筆列出無意義故收斂為表級標記。",
            "",
            "| 表格 # | 數字總數 | 未確認 | 首列（節錄） |",
            "| --- | --- | --- | --- |",
        ]
        for u in unverifiable:
            row = u["row"][:60].replace("|", "\\|")
            lines.append(f"| {u['table']} | {u['total']} | {u['unconfirmed']} | {row} |")
    if unmatched_surya:
        lines += [
            "",
            f"## surya 讀到但轉換輸出沒有的數字（{len(unmatched_surya)} 個，可能為漏抽或 surya 誤讀）",
            "",
            "、".join(f"`{t}`" for t in unmatched_surya[:60])
            + ("（僅列前 60 個）" if len(unmatched_surya) > 60 else ""),
        ]
    return "\n".join(lines) + "\n", len(suspects)


def parse_page_range(spec: str) -> list[int]:
    """'4-9' or '5' as 1-based inclusive; returns 0-based indexes."""
    if "-" in spec:
        start, end = spec.split("-", 1)
        return list(range(int(start) - 1, int(end)))
    return [int(spec) - 1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf", help="source PDF path")
    parser.add_argument("markdown", help="converted markdown path")
    parser.add_argument("-o", "--output", help="report path (default: <markdown>.verify.md)")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--pages", help="1-based page range to verify, e.g. 4-9 (default: all)")
    parser.add_argument(
        "--dump-tokens", help="also dump surya tokens with confidences to this JSON path"
    )
    args = parser.parse_args()

    md_text = Path(args.markdown).read_text()
    entries = markdown_table_numbers(md_text)
    if not entries:
        print("轉換輸出中沒有表格數字，無事可驗。", file=sys.stderr)
        return 0

    started = time.time()
    pages = parse_page_range(args.pages) if args.pages else None
    surya_tokens, tables_seen = surya_read_pdf(args.pdf, args.dpi, pages)
    print(f"surya read: {time.time() - started:.0f}s", file=sys.stderr)

    report, suspect_count = build_report(args.pdf, args.markdown, entries, surya_tokens, tables_seen)
    output = Path(args.output) if args.output else Path(args.markdown + ".verify.md")
    output.write_text(report)
    if args.dump_tokens:
        Path(args.dump_tokens).write_text(json.dumps(surya_tokens, indent=1))
    print(f"report: {output} ({suspect_count} suspect(s))", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
