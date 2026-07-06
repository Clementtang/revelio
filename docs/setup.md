# Setup Guide

詳細安裝說明。與 README 的快速開始一致，但補充驗證與疑難排解。

## Prerequisites

- macOS / Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) — Python 套件管理器
- [Claude Code](https://claude.ai/code) CLI
- **Java 11+** — opendataloader-pdf（PDF 功能）需要

## Installation

### 1. 安裝 uv（如尚未安裝）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 下載專案

```bash
git clone https://github.com/Clementtang/revelio.git ~/revelio
cd ~/revelio
```

### 3. 設定 Revelio MCP Server（圖片 OCR）

MCP server 由 Claude Code **就地引用**，不需複製到其他位置。在 `~/.claude.json` 的 `mcpServers` 中加入（把 `<you>` 換成你的使用者名稱）：

```json
{
  "mcpServers": {
    "revelio": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/<you>/revelio/src/mcp-server",
        "run",
        "server.py"
      ],
      "env": {
        "EASYOCR_LANGUAGES": "ch_tra,en"
      }
    }
  }
}
```

可選的環境變數：

| 變數                     | 作用                                | 預設值         |
| ------------------------ | ----------------------------------- | -------------- |
| `EASYOCR_LANGUAGES`      | OCR 語言（逗號分隔）                 | `ch_tra,en`    |
| `EASYOCR_GPU`            | 是否使用 GPU/MPS（`true`/`false`）   | `false`（CPU） |
| `EASYOCR_UNLOAD_TIMEOUT` | 閒置多少秒後自動卸載模型（`0` 停用） | `0`            |

### 4. 安裝 Skill

```bash
cp -r src/skill ~/.claude/skills/revelio
```

Claude Code 會在下次啟動時自動偵測 `~/.claude/skills/revelio/SKILL.md`。

### 5. 安裝 opendataloader-pdf（PDF 功能）

```bash
python3 -m venv ~/odl-env
source ~/odl-env/bin/activate
pip install -U "opendataloader-pdf[hybrid]"
```

需先安裝 Java 11+（`java -version` 應可正常輸出）。

### 6. 驗證安裝

```bash
# 驗證 MCP server 依賴
cd ~/revelio/src/mcp-server && uv run python -c "import easyocr; print('EasyOCR OK')"

# 驗證共用模組（不需 EasyOCR）
cd ~/revelio/src/mcp-server && uv run python -c "import ocr_common; print('ocr_common OK')"

# 檢查 skill
cat ~/.claude/skills/revelio/SKILL.md

# 檢查 opendataloader-pdf
source ~/odl-env/bin/activate && opendataloader-pdf-hybrid --help >/dev/null && echo "opendataloader OK"

# 檢查結果目錄
ls -la ~/revelio/ocr_results/
```

## First Run

首次執行圖片 OCR 時，EasyOCR 會下載語言模型（約 100–200MB），這是一次性下載，之後使用快取。

首次啟動 opendataloader-pdf hybrid server 約需 30–40 秒（載入 DocumentConverter）。

## Usage

### MCP Mode（快速模式・圖片）

在 Claude Code 中，AI 可直接呼叫圖片 OCR 工具：

```
Claude: 讓我幫你辨識這張圖片...
[自動呼叫 mcp__revelio__ocr_image_file]
```

### Skill Mode（隱私模式・圖片或 PDF）

輸入指令並提供檔案路徑：

```
/revelio ~/Documents/receipt.jpg     # 圖片 → EasyOCR
/revelio ~/reports/financial.pdf     # PDF  → opendataloader-pdf
/revelio --ocr ~/scanned_page.png    # 強制使用 EasyOCR
```

結果存檔後，Claude 會詢問是否讀取，經同意才會讀取內容。

## Troubleshooting

### EasyOCR 載入緩慢

首次載入模型需要時間，後續會快很多。若 server 常駐但久未使用，可設定 `EASYOCR_UNLOAD_TIMEOUT` 讓模型閒置後自動卸載，或呼叫 `unload_ocr_models` 工具手動釋放。

### CUDA / GPU 問題

預設使用 CPU（`EASYOCR_GPU=false`）。若要 GPU/MPS 加速，設定 `EASYOCR_GPU=true`，並確保已安裝對應的 GPU 版 PyTorch。

### 中文辨識不準確（圖片）

- 確保圖片解析度足夠（建議 300 DPI+）
- 避免過度壓縮的 JPEG
- 文字區域對比度要足夠

### PDF 缺少中文字（只有數字和代碼）

部分中文 PDF 使用 CID-keyed fonts 但缺少 ToUnicode CMap，文字層無法解讀。改用 force-ocr 模式啟動 hybrid server：

```bash
source ~/odl-env/bin/activate && opendataloader-pdf-hybrid --port 5002 --force-ocr --ocr-lang "ch_tra,en" &
```

詳見 [ADR-003](decisions/003-pdf-processing-architecture.md) 與 README 的範例輸出。
