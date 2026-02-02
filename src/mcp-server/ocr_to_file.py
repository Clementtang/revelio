#!/usr/bin/env python3
"""
Local OCR script - saves results to file, returns only file path.
No sensitive data sent to cloud.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: ocr_to_file.py <image_path> [output_dir]")
        sys.exit(1)

    image_path = sys.argv[1]

    # Output directory priority: CLI arg > env var > default
    default_output_dir = os.path.expanduser("~/revelio/ocr_results")
    output_dir = (
        sys.argv[2] if len(sys.argv) > 2
        else os.environ.get("REVELIO_OUTPUT_DIR", default_output_dir)
    )

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Import EasyOCR (lazy load to show progress)
    print("載入 EasyOCR...", file=sys.stderr)
    import easyocr

    # Initialize reader
    languages = os.environ.get("EASYOCR_LANGUAGES", "ch_tra,en").split(",")
    reader = easyocr.Reader(languages, gpu=False, verbose=False)

    # Perform OCR
    print(f"辨識中: {image_path}", file=sys.stderr)
    results = reader.readtext(image_path)

    # Prepare output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = Path(image_path).stem
    output_filename = f"ocr_{image_name}_{timestamp}.txt"
    output_path = Path(output_dir) / output_filename

    # Write results to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# OCR 結果\n")
        f.write(f"# 來源: {image_path}\n")
        f.write(f"# 時間: {datetime.now().isoformat()}\n")
        f.write(f"# 語言: {', '.join(languages)}\n")
        f.write(f"#\n\n")

        for bbox, text, confidence in results:
            f.write(f"{text}\n")

        f.write(f"\n\n# === 詳細資訊 (含信心度) ===\n")
        for bbox, text, confidence in results:
            f.write(f"# [{confidence:.1%}] {text}\n")

    # Only output the file path (this is what gets sent to Claude)
    print(f"OCR 完成，結果已儲存至: {output_path}")

if __name__ == "__main__":
    main()
