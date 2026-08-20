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

使用者可透過參數覆寫預設路由：

- `--ocr` 加圖片 → EasyOCR
- `--ocr` 加 `.pdf` → 仍走 opendataloader-pdf hybrid，並強制 `--force-ocr`（EasyOCR 不能讀 PDF）
- `--pdf` → opendataloader-pdf

## 隱私說明

- 所有處理都在本機完成，不上傳至雲端
- **預設不會讓 Claude 讀取結果**，除非使用者明確同意

## 工作流程

### 步驟 1：取得檔案路徑

詢問使用者要處理的檔案路徑（如未提供）。

先把 `~` 展開成絕對路徑（Python `Path(...).expanduser()` 或 shell 的 `$HOME`），再傳給後續指令。路徑以獨立參數傳遞，**不要把檔名插進 `python3 -c` 的字串裡**。

### 步驟 2：判斷工具

依以下優先順序判斷：

1. `--ocr` 且副檔名為 `.pdf` → 路徑 B，略過 B-0，直接以 `--force-ocr` 啟動
2. `--ocr` 且為圖片 → 路徑 A
3. `--pdf` → 路徑 B
4. 副檔名為 `.pdf` → 路徑 B
5. 副檔名為圖片格式 → 路徑 A
6. 無法判斷 → 詢問使用者

### 步驟 3：執行處理

#### 路徑 A：EasyOCR（圖片）

MCP server 目錄：`REVELIO_MCP_DIR` 若有設就用它，否則預設 `$HOME/revelio/src/mcp-server`。若該目錄不存在，從 Claude MCP 設定裡 revelio 的 `--directory` 參數取得實際路徑，或詢問使用者。不要假設一定是 `~/revelio`。

```bash
MCP_DIR="${REVELIO_MCP_DIR:-$HOME/revelio/src/mcp-server}"
cd "$MCP_DIR" && uv run python ocr_to_file.py "$image_path"
```

結果存放：`~/revelio/ocr_results/ocr_<檔名>_<時間戳>.txt`（腳本會印出實際路徑，回報時用 stdout，不要自己拼檔名）。

#### 路徑 B：opendataloader-pdf（PDF）

**步驟 B-0：前置偵測（pdf-inspector）**

在啟動 hybrid server **之前**，先用 [pdf-inspector](https://github.com/firecrawl/pdf-inspector) 判斷這份 PDF 是否需要 force-OCR（毫秒級、純本地結構分析，不渲染、不上傳）。路徑用 `sys.argv` 傳入，不要做字串插值：

```bash
source ~/odl-env/bin/activate && python3 -c '
import json, pdf_inspector, sys
r = pdf_inspector.detect_pdf(sys.argv[1])
print(json.dumps({
    "pdf_type": r.pdf_type,
    "page_count": r.page_count,
    "pages_needing_ocr": r.pages_needing_ocr,
    "ocr_reasons": {p.page: p.reasons for p in r.ocr_reasons_by_page},
    "confidence": r.confidence,
    "has_encoding_issues": getattr(r, "has_encoding_issues", False),
}, ensure_ascii=False))
' "$pdf_path"
```

（注意：`python3 -c` 之後不要加 `--`，它會被收進 `sys.argv[1]` 造成參數位移，實測驗證於 2026-08-20。）

依偵測結果決定 server 啟動旗標：

| 偵測結果                                                            | 判斷                                      | 啟動旗標                             |
| ------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| `pages_needing_ocr` 為空，且 `has_encoding_issues` 不為 true        | 文字層可用                                | 標準模式（不加 `--force-ocr`）       |
| `has_encoding_issues` 為 true                                       | 字型編碼損壞，文字層可能是亂碼            | `--force-ocr --ocr-lang "ch_tra,en"` |
| 原因含 `suspected_garbled_text` 或 `vector_text`                    | 文字層不可解碼（如 CID 字型缺 ToUnicode） | `--force-ocr --ocr-lang "ch_tra,en"` |
| `pdf_type` 為 `scanned`/`image_based`，或原因含 `scanned`/`no_text` | 掃描件／純圖片                            | `--force-ocr --ocr-lang "ch_tra,en"` |

> `ocr_lang` 依文件語言調整：純英文文件用 `"en"` 即可，中文或中英混合用 `"ch_tra,en"`。
>
> 不要只憑 `pages_needing_ocr` 為空就判定文字層可用。CJK CID 字型有時抽得出數字與代碼，但 `has_encoding_issues` 為 true。
>
> 若 pdf-inspector 未安裝或執行失敗，退回舊的啟發式判斷：檔名或內容明顯為中文 → 直接用 force-ocr 版本；不確定 → 先標準模式試轉，若輸出缺少中文字（只有數字和代碼）或出現「glyph can not be mapped to Unicode」警告，改用 force-ocr 版本重試。

**步驟 B-1：啟動 hybrid server（若尚未以正確模式運行）**

需要的模式寫成 `standard` 或 `force-ocr`。

若 port 5002 已在聽，先檢查這個 process 的啟動參數，不要只因為 port 有人聽就沿用：

```bash
PID=$(lsof -nP -iTCP:5002 -sTCP:LISTEN -t | head -1)
ps -p "$PID" -o args=
```

- 參數含 `--force-ocr` → 目前是 force-ocr
- 否則 → 目前是 standard
- 目前模式與需要的模式不同 → `kill "$PID"`，等 port 釋放後再以正確旗標啟動
- 模式相同 → 沿用，不要重啟

文字層可用（B-0 判定標準模式）：

```bash
source ~/odl-env/bin/activate && opendataloader-pdf-hybrid --host 127.0.0.1 --port 5002 &
```

需要 force-OCR（B-0 偵測到亂碼文字層、編碼問題或掃描件；或使用者對 PDF 下了 `--ocr`）：

```bash
source ~/odl-env/bin/activate && opendataloader-pdf-hybrid --host 127.0.0.1 --port 5002 --force-ocr --ocr-lang "ch_tra,en" &
```

等待 server 輸出 `Uvicorn running on http://127.0.0.1:5002` 後再繼續。
初次啟動約需 30-40 秒（載入 DocumentConverter）。

確認 server 已啟動：`lsof -nP -iTCP:5002 -sTCP:LISTEN`

**步驟 B-2：轉換 PDF（hybrid mode）**

路徑同樣用 argv，不要插進 Python 字面值：

```bash
source ~/odl-env/bin/activate && python3 -c '
import opendataloader_pdf, sys
opendataloader_pdf.convert(
    input_path=[sys.argv[1]],
    output_dir=sys.argv[2],
    format="markdown,json",
    hybrid="docling-fast",
    hybrid_mode="full",
    hybrid_url="http://127.0.0.1:5002",
)
' "$pdf_path" "$output_dir"
```

輸出資料夾命名慣例：`~/odl-output/<公司名-代號>/<期間-類型>/`

若無法從檔名推斷公司與期間結構，直接以檔名建立子資料夾：`~/odl-output/<檔名>/`

**PDF 轉換注意事項：**

- **必須使用 hybrid mode** — 基本模式無法正確處理無邊框表格（如財務報表）
- 掃描件與亂碼文字層由步驟 B-0 前置偵測，以 `--force-ocr --ocr-lang` 旗標在 server 啟動時決定
- 處理完畢後可用 `kill %1` 或 `kill $(lsof -t -iTCP:5002 -sTCP:LISTEN)` 關閉 hybrid server

**步驟 B-3：表格數字驗證（選配，預設詢問）**

轉換完成後，若輸出含表格且文件屬於數字敏感場景（財報、報價、統計），詢問使用者是否執行表格驗證：

> 轉換完成。要不要跑表格數字驗證？（surya v2 本地模型獨立重讀 PDF 表格區域，
> 交叉比對轉換輸出的數字並標記不一致，約每頁 15 至 30 秒，全程本地）

使用者同意後執行（需要 `~/surya-env`，安裝方式見 `docs/research/surya-v2-local-test.md`）：

```bash
VERIFY_DIR="${REVELIO_MCP_DIR:-$HOME/revelio/src/mcp-server}/../table-verify"
source ~/surya-env/bin/activate && SURYA_GUIDED_LAYOUT=false \
  python3 "$VERIFY_DIR/verify_tables.py" "$pdf_path" "$converted_md" \
  -o "$converted_md.verify.md"
```

驗證報告只標記可疑數字（含「疑似小數點丟失」線索與信心分數），不會修改轉換輸出。報告本身不含文件全文，但含個別數字與所在列節錄，回報給使用者時同樣遵守步驟 4 的隱私規則：告知報告路徑與可疑筆數即可，內容待使用者同意才讀取。使用者婉拒驗證時，提醒重要數字建議人工抽查。

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
       結果已存至 ~/revelio/ocr_results/ocr_receipt_20240101_120000.txt
       是否要讓 Claude 讀取內容？

使用者：/revelio ~/reports/財報.pdf
Claude：[自動選擇 opendataloader-pdf] 正在轉換 PDF...
       結果已存至 ~/odl-output/財報/財報.md
       是否要讓 Claude 讀取內容？

使用者：/revelio --ocr ~/scanned.pdf
Claude：[PDF 強制 OCR] 走 hybrid --force-ocr，不用 EasyOCR 讀 PDF...
```

## 支援語言

- 繁體中文 (`ch_tra`)
- 英文 (`en`)
- EasyOCR 支援 80+ 語言，opendataloader-pdf hybrid mode 同樣支援

> 注意：EasyOCR 與 opendataloader-pdf 都使用 `ch_tra`（繁體中文）語言碼。
