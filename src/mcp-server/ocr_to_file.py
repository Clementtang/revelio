#!/usr/bin/env python3
"""
Local OCR script - saves results to file, returns only file path.
No sensitive data sent to cloud.
"""

import sys
import os
from datetime import datetime
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: ocr_to_file.py <image_path> [output_dir]", file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]

    # Validate image file exists
    if not Path(image_path).exists():
        print(f"錯誤: 找不到檔案 {image_path}", file=sys.stderr)
        sys.exit(1)

    # Output directory priority: CLI arg > env var > default
    default_output_dir = os.path.expanduser("~/revelio/ocr_results")
    output_dir = (
        sys.argv[2] if len(sys.argv) > 2
        else os.environ.get("REVELIO_OUTPUT_DIR", default_output_dir)
    )

    # Ensure output directory exists
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"錯誤: 無法建立輸出目錄 {output_dir}: {e}", file=sys.stderr)
        sys.exit(1)

    # Import EasyOCR (lazy load to show progress)
    print("載入 EasyOCR...", file=sys.stderr)
    try:
        import easyocr
    except ImportError as e:
        print(f"錯誤: 無法載入 EasyOCR: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize reader
    languages = os.environ.get("EASYOCR_LANGUAGES", "ch_tra,en").split(",")
    try:
        reader = easyocr.Reader(languages, gpu=False, verbose=False)
    except Exception as e:
        print(f"錯誤: 無法初始化 OCR 引擎: {e}", file=sys.stderr)
        sys.exit(1)

    # Perform OCR
    print(f"辨識中: {image_path}", file=sys.stderr)
    try:
        results = reader.readtext(image_path)
    except Exception as e:
        print(f"錯誤: OCR 辨識失敗: {e}", file=sys.stderr)
        sys.exit(1)

    # Prepare output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = Path(image_path).stem
    output_filename = f"ocr_{image_name}_{timestamp}.txt"
    output_path = Path(output_dir) / output_filename

    # Write results to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# OCR 結果\n")
            f.write(f"# 來源: {image_path}\n")
            f.write(f"# 時間: {datetime.now().isoformat()}\n")
            f.write(f"# 語言: {', '.join(languages)}\n")
            f.write("#\n\n")

            for bbox, text, confidence in results:
                f.write(f"{text}\n")

            f.write("\n\n# === 詳細資訊 (含信心度) ===\n")
            for bbox, text, confidence in results:
                f.write(f"# [{confidence:.1%}] {text}\n")
    except OSError as e:
        print(f"錯誤: 無法寫入檔案 {output_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Only output the file path (this is what gets sent to Claude)
    print(f"OCR 完成，結果已儲存至: {output_path}")


if __name__ == "__main__":
    main()
