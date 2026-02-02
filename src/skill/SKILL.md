---
name: ocr-local
description: 執行本地隱私 OCR，使用 EasyOCR 辨識圖片文字而不上傳至雲端。支援繁體中文與英文。
---

# 本地隱私 OCR

此 skill 使用本地 EasyOCR 進行圖片文字辨識，**所有處理都在本機完成**，不會將圖片內容上傳至任何雲端服務。

## 隱私說明

- 圖片由本機 EasyOCR 模型處理
- OCR 結果存放於 `~/revelio/ocr_results/`（可透過 `REVELIO_OUTPUT_DIR` 環境變數自訂）
- **預設不會讓 Claude 讀取結果**，除非使用者明確同意

## 工作流程

### 步驟 1：取得圖片路徑

詢問使用者要辨識的圖片檔案路徑。支援格式：PNG、JPG、JPEG、BMP、TIFF 等常見圖片格式。

### 步驟 2：執行本地 OCR

使用以下指令執行 OCR（繁體中文 + 英文）：

```bash
cd ~/.claude/easyocr-mcp && uv run python ocr_to_file.py "<image_path>"
```

### 步驟 3：回報結果位置

告知使用者：

- OCR 執行成功/失敗
- 結果檔案的完整路徑

### 步驟 4：詢問是否讀取（關鍵隱私步驟）

**必須明確詢問使用者**：

> OCR 結果已儲存至 `<output_path>`
>
> 是否要讓 Claude 讀取內容以協助後續處理？
>
> - **是** → 我會讀取檔案內容，可以協助整理、翻譯、分析
> - **否** → 您可自行開啟檔案查看，內容不會傳送給 Claude

**不可自動讀取結果檔案**，必須等待使用者明確同意。

## 使用範例

```
使用者：/ocr-local
Claude：請提供要辨識的圖片路徑。

使用者：~/Documents/receipt.jpg
Claude：正在執行本地 OCR...
       ✓ 辨識完成，結果已存至 ~/.claude/ocr_results/receipt_20240101_120000.txt

       是否要讓 Claude 讀取內容以協助後續處理？

使用者：好
Claude：[讀取檔案並協助處理]
```

## 支援語言

- 繁體中文 (ch_tra)
- 英文 (en)

## 結果存放位置

預設：`~/revelio/ocr_results/`

自訂方式：設定環境變數 `REVELIO_OUTPUT_DIR`

檔案命名格式：`ocr_<原檔名>_<時間戳記>.txt`
