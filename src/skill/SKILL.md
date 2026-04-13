---
name: revelio
description: 本地文件處理 — 自動依副檔名選擇 EasyOCR（圖片）或 opendataloader-pdf（PDF），也可手動指定。支援繁體中文與英文。
---

# Revelio — 本地文件處理

統一入口，自動判斷工具：

| 輸入類型                                   | 工具               | 輸出位置                 |
| ------------------------------------------ | ------------------ | ------------------------ |
| 圖片（`.jpg`, `.png`, `.bmp`, `.tiff` 等） | EasyOCR            | `~/revelio/ocr_results/` |
| PDF（`.pdf`）                              | opendataloader-pdf | `~/odl-output/`          |

使用者可透過參數強制指定：`--ocr` 強制用 EasyOCR，`--pdf` 強制用 opendataloader-pdf。

## 隱私說明

- 所有處理都在本機完成，不上傳至雲端
- **預設不會讓 Claude 讀取結果**，除非使用者明確同意

## 工作流程

### 步驟 1：取得檔案路徑

詢問使用者要處理的檔案路徑（如未提供）。

### 步驟 2：判斷工具

依以下優先順序判斷：

1. 使用者指定 `--ocr` 或 `--pdf` → 依指定
2. 副檔名為 `.pdf` → opendataloader-pdf
3. 副檔名為圖片格式 → EasyOCR
4. 無法判斷 → 詢問使用者

### 步驟 3：執行處理

#### 路徑 A：EasyOCR（圖片）

```bash
cd ~/revelio/src/mcp-server && uv run python ocr_to_file.py "<image_path>"
```

結果存放：`~/revelio/ocr_results/`

#### 路徑 B：opendataloader-pdf（PDF）

**步驟 B-1：啟動 hybrid server（若尚未運行）**

```bash
source ~/odl-env/bin/activate && opendataloader-pdf-hybrid --port 5002 &
```

等待 server 輸出 `Uvicorn running on http://0.0.0.0:5002` 後再繼續。
初次啟動約需 30-40 秒（載入 DocumentConverter）。

確認 server 已啟動：`lsof -i :5002 | grep LISTEN`

**步驟 B-2：轉換 PDF（hybrid mode）**

```bash
source ~/odl-env/bin/activate && python3 -c "
import opendataloader_pdf
opendataloader_pdf.convert(
    input_path=['<pdf_path>'],
    output_dir='<output_dir>',
    format='markdown,json',
    hybrid='docling-fast',
    hybrid_mode='full',
    hybrid_url='http://localhost:5002'
)
"
```

輸出資料夾命名慣例：`~/odl-output/<公司名-代號>/<期間-類型>/`

若無法從檔名推斷公司與期間結構，直接以檔名建立子資料夾：`~/odl-output/<檔名>/`

**PDF 轉換注意事項：**

- **必須使用 hybrid mode** — 基本模式無法正確處理無邊框表格（如財務報表）
- 掃描件額外加 `force_ocr=True`
- 中文文件加 `ocr_lang="zh,en"`
- 轉換後建議人工抽查表格數字正確性
- 處理完畢後可用 `kill %1` 或 `kill $(lsof -t -i :5002)` 關閉 hybrid server

### 步驟 4：回報結果並詢問是否讀取（關鍵隱私步驟）

**必須明確詢問使用者**：

> 處理完成，結果已儲存至 `<output_path>`
>
> 是否要讓 Claude 讀取內容以協助後續處理？
>
> - **是** → 我會讀取檔案內容，可以協助整理、翻譯、分析
> - **否** → 您可自行開啟檔案查看，內容不會傳送給 Claude

**不可自動讀取結果檔案**，必須等待使用者明確同意。

## 使用範例

```
使用者：/revelio ~/Documents/receipt.jpg
Claude：[自動選擇 EasyOCR] 正在執行本地 OCR...
       結果已存至 ~/revelio/ocr_results/receipt_20240101_120000.txt
       是否要讓 Claude 讀取內容？

使用者：/revelio ~/reports/財報.pdf
Claude：[自動選擇 opendataloader-pdf] 正在轉換 PDF...
       結果已存至 ~/odl-output/財報/財報.md
       是否要讓 Claude 讀取內容？

使用者：/revelio --ocr ~/scanned.pdf
Claude：[強制使用 EasyOCR] 正在執行本地 OCR...
```

## 支援語言

- 繁體中文 (ch_tra / zh)
- 英文 (en)
- EasyOCR 支援 80+ 語言，opendataloader-pdf hybrid mode 同樣支援
