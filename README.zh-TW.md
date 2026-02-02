# Revelio

> _Revelio_（顯形咒）— 哈利波特中用於揭示隱藏事物的咒語。

繁體中文 | [English](README.md)

本地隱私優先的 OCR 解決方案，使用 EasyOCR 在本機執行文字辨識。所有處理都在你的裝置上完成，敏感內容絕不上傳雲端。

## 功能特色

- **隱私優先** — 所有 OCR 處理在本機執行，不上傳任何資料
- **多語言支援** — 支援繁體中文（`ch_tra`）與英文（`en`）
- **Claude Code 整合** — 雙模式：MCP Server（快速）與 Skill（隱私）
- **使用者掌控** — Skill 模式下，由你決定是否讓 Claude 讀取結果

## 快速開始

### 環境需求

- macOS 或 Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（Python 套件管理器）
- [Claude Code](https://claude.ai/code) CLI

### 安裝步驟

1. **安裝 uv**（若尚未安裝）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **下載專案**：

```bash
git clone https://github.com/Clementtang/revelio.git ~/revelio
cd ~/revelio
```

3. **設定 Claude Code** — 在 `~/.claude/settings.json` 中加入 MCP Server：

```json
{
  "mcpServers": {
    "easyocr": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "~/.claude/easyocr-mcp",
        "python",
        "server.py"
      ]
    }
  }
}
```

4. **安裝 Skill** — 複製到 skills 目錄：

```bash
cp -r skills/ocr-local ~/.claude/skills/
```

## 使用方式

### 模式一：`/ocr-local` Skill（隱私模式）

適合處理敏感文件。結果儲存在本地，只有經過你明確同意，Claude 才會讀取。

```
你：/ocr-local
Claude：請提供要辨識的圖片路徑。
你：~/Documents/contract.jpg
Claude：✓ 辨識完成，結果已存至 ~/revelio/ocr_results/...
        是否要讓我讀取內容？
你：是 / 否
```

### 模式二：MCP Server（快速模式）

適合一般用途。Claude 直接取得 OCR 結果，可立即協助處理。

當你要求 Claude 辨識圖片中的文字時，它會自動使用 MCP 工具。

## 設定選項

### 輸出目錄

預設：`~/revelio/ocr_results/`

透過環境變數自訂：

```bash
export REVELIO_OUTPUT_DIR="/你的/自訂/路徑"
```

優先順序：CLI 參數 > 環境變數 > 預設值

### 支援語言

目前設定：

- 繁體中文（`ch_tra`）
- 英文（`en`）

EasyOCR 支援 80+ 種語言。若要新增，修改 `EASYOCR_LANGUAGES` 環境變數：

```bash
export EASYOCR_LANGUAGES="ch_tra,en,ja"  # 新增日文
```

## 專案結構

```
revelio/
├── src/
│   ├── mcp-server/      # EasyOCR MCP Server 原始碼
│   │   ├── server.py
│   │   ├── ocr_to_file.py
│   │   └── pyproject.toml
│   └── skill/           # Claude Code Skill
│       └── SKILL.md
├── ocr_results/         # OCR 輸出（不納入 git）
└── docs/                # 文件
```

## 安裝位置

| 元件       | 安裝路徑                      | 原始碼            |
| ---------- | ----------------------------- | ----------------- |
| MCP Server | `~/.claude/easyocr-mcp/`      | `src/mcp-server/` |
| Skill 定義 | `~/.claude/skills/ocr-local/` | `src/skill/`      |
| OCR 結果   | `~/revelio/ocr_results/`      | —                 |

## 文件

- [架構說明](docs/architecture.md) — 系統設計與資料流
- [安裝指南](docs/setup.md) — 詳細安裝說明
- [決策記錄](docs/decisions/) — 重大決策的 ADR
- [變更日誌](CHANGELOG.zh-TW.md) — 版本歷程

## 技術棧

- **OCR 引擎**：[EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **Python 執行環境**：[uv](https://github.com/astral-sh/uv)
- **整合平台**：Claude Code（MCP 協議 + Skills）

## 為什麼叫「Revelio」？

在哈利波特的世界中，_Revelio_（顯形咒）是一個用於揭示隱藏物品、秘密訊息和隱形事物的咒語。這個專案做的事情一樣 — 揭示圖片中隱藏的文字，同時保護你的敏感內容隱私。

## 授權

MIT

## 貢獻

歡迎貢獻！請先閱讀[架構說明](docs/architecture.md)文件，了解雙模式設計的理念。
