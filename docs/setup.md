# Setup Guide

## Prerequisites

- macOS / Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Python package manager
- Claude Code CLI

## Installation

### 1. 安裝 uv（如尚未安裝）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. EasyOCR MCP Server

MCP Server 已設定於 `~/.claude/easyocr-mcp/`。

確認 Claude Code 設定已包含此 MCP：

```bash
cat ~/.claude/settings.json | grep -A5 easyocr
```

應看到類似：

```json
"easyocr": {
  "command": "uv",
  "args": ["run", "--directory", "~/.claude/easyocr-mcp", "python", "server.py"]
}
```

### 3. Skill 設定

Skill 已設定於 `~/.claude/skills/ocr-local/`。

Claude Code 會自動偵測 skills 目錄下的 SKILL.md。

### 4. 驗證安裝

```bash
# 測試 MCP Server
cd ~/.claude/easyocr-mcp && uv run python -c "import easyocr; print('EasyOCR OK')"

# 檢查 Skill 檔案
cat ~/.claude/skills/ocr-local/SKILL.md

# 檢查結果目錄
ls -la ~/revelio/ocr_results/
```

## First Run

首次執行 OCR 時，EasyOCR 會下載語言模型（約 100-200MB）。

這是一次性的下載，之後會使用快取。

## Usage

### MCP Mode

在 Claude Code 中，AI 可直接呼叫 OCR 工具：

```
Claude: 讓我幫你辨識這張圖片...
[自動呼叫 mcp__easyocr__ocr_image_file]
```

### Skill Mode

輸入指令觸發：

```
/ocr-local
```

然後提供圖片路徑。

## Troubleshooting

### EasyOCR 載入緩慢

首次載入模型需要時間，後續會快很多。

### CUDA/GPU 問題

EasyOCR 預設使用 CPU。如需 GPU 加速，需安裝 CUDA 版 PyTorch。

### 中文辨識不準確

- 確保圖片解析度足夠（建議 300 DPI+）
- 避免過度壓縮的 JPEG
- 文字區域對比度要足夠
