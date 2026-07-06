# Architecture

## Overview

Revelio 是本地隱私優先的文件處理工具，整合於 Claude Code。它由**兩個處理引擎**與**兩種使用模式**組成：

- **EasyOCR** — 辨識圖片中的文字
- **opendataloader-pdf** — 解析 PDF 結構（表格、標題、閱讀順序），掃描件可啟用 hybrid OCR

使用者透過統一的 `/revelio` skill 進入，skill 依副檔名自動選擇引擎；圖片 OCR 也可由 MCP server 直接呼叫。

```
┌──────────────────────────────────────────────────────────────────┐
│                          Claude Code                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌─────────────────┐                 ┌─────────────────────────┐  │
│   │  Revelio MCP    │                 │      /revelio Skill     │  │
│   │  Server         │                 │   (統一入口・隱私模式)  │  │
│   │  (快速模式・圖片)│                 │  依副檔名路由引擎        │  │
│   └────────┬────────┘                 └────────┬────────────────┘  │
│            │ 結果直接回傳                        │ 結果存檔          │
│            │                        ┌───────────┴──────────┐        │
│            │                        │ .jpg/.png/...   .pdf │        │
│            ▼                        ▼                      ▼        │
│   ┌──────────────────────────────────┐   ┌────────────────────┐    │
│   │           EasyOCR Engine         │   │ opendataloader-pdf │    │
│   │        (本地 Python 程序)         │   │  (本地 Java 程序)  │    │
│   └──────────────────────────────────┘   └────────────────────┘    │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Revelio MCP Server（圖片 OCR）

**原始碼**：`src/mcp-server/server.py`
**執行方式**：由 Claude Code 就地引用（`~/.claude.json` 中的 `mcpServers.revelio`），不需複製到其他位置。

**功能**：

- 提供 MCP 協議介面讓 Claude Code 直接呼叫圖片 OCR
- OCR 結果直接回傳至對話上下文
- EasyOCR / PyTorch 延遲載入，並支援閒置自動卸載（見 [ADR-002](decisions/002-memory-management-strategy.md)）

**適用場景**：一般圖片、需要 AI 立即分析、非敏感內容。

**工具**：

- `ocr_image_file` — 從檔案路徑辨識
- `ocr_image_base64` — 從 base64 編碼辨識
- `ocr_image_url` — 從 URL 辨識（僅限 http/https，含大小上限）
- `unload_ocr_models` — 釋放已載入的模型以節省記憶體

**共用模組**：`src/mcp-server/ocr_common.py` — 語言/GPU 環境變數解析、影像驗證與轉換，MCP server 與獨立腳本共用。

### 2. `/revelio` Skill（統一入口・隱私模式）

**原始碼**：`src/skill/SKILL.md`
**安裝位置**：`~/.claude/skills/revelio/`

**功能**：

- 依副檔名自動路由：圖片 → EasyOCR、PDF → opendataloader-pdf
- 可用 `--ocr` / `--pdf` 手動指定
- 結果存檔，**不自動讀取**，需使用者明確同意

**適用場景**：敏感文件（身分證、合約、醫療紀錄、財報）、隱私優先的工作流程。

### 3. 獨立 OCR 腳本

**原始碼**：`src/mcp-server/ocr_to_file.py`

**功能**：獨立執行圖片 OCR 並存檔，由 skill 的圖片路徑呼叫。與 MCP server 共用 `ocr_common.py`，行為（語言、GPU）一致。

### 4. opendataloader-pdf（外部工具）

由使用者自行安裝於獨立 venv（`~/odl-env/`），skill 以子程序呼叫其 hybrid server 進行 PDF 轉換。Revelio 不打包、不修改此工具，僅呼叫。詳見 [ADR-003](decisions/003-pdf-processing-architecture.md)。

## Data Flow

### MCP Mode（快速模式・僅圖片）

```
User Request → Claude → MCP Tool Call → EasyOCR → Result → Claude → User
                                                     ↑
                                              (直接進入對話)
```

### Skill Mode（隱私模式）

```
User: /revelio <file> → Claude → 依副檔名判斷引擎
                                     │
                    ┌────────────────┴────────────────┐
                    ▼ 圖片                             ▼ PDF
             ocr_to_file.py                    opendataloader-pdf
                    │                                  │
                    └────────────────┬─────────────────┘
                                     ▼ 結果存檔
              Claude: "結果已存檔，是否要我讀取？"
                                     │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                     User: "是"          User: "否"
                          │                   │
                          ▼                   ▼
                   Claude 讀取檔案      使用者自行查看
```

## Directory Structure

```
revelio/
├── src/
│   ├── mcp-server/
│   │   ├── server.py         # MCP Server 主程式
│   │   ├── ocr_to_file.py    # 獨立 OCR 腳本
│   │   ├── ocr_common.py     # 共用 helper（語言/GPU/影像）
│   │   └── pyproject.toml    # Python 依賴定義
│   └── skill/
│       └── SKILL.md          # Skill 定義
├── ocr_results/              # 圖片 OCR 輸出（預設位置，git-ignored）
└── docs/                     # 專案文件（架構、ADR）
```

安裝後：

- MCP server：就地引用自 `~/revelio/src/mcp-server/`
- Skill：`~/.claude/skills/revelio/`
- 圖片 OCR 輸出：`~/revelio/ocr_results/`
- PDF 輸出：`~/odl-output/`
- opendataloader-pdf venv：`~/odl-env/`

### 自訂輸出位置（圖片 OCR）

優先順序：CLI 參數 > `REVELIO_OUTPUT_DIR` 環境變數 > 預設值

```bash
# 方式 1: 環境變數
export REVELIO_OUTPUT_DIR="/custom/path"

# 方式 2: CLI 參數
uv run python ocr_to_file.py image.png /custom/path
```

## Configuration

| 環境變數                 | 作用                                   | 預設值                  |
| ------------------------ | -------------------------------------- | ----------------------- |
| `EASYOCR_LANGUAGES`      | OCR 語言（逗號分隔）                    | `ch_tra,en`             |
| `EASYOCR_GPU`            | 是否使用 GPU/MPS（`true`/`false`）      | `false`（CPU）          |
| `EASYOCR_UNLOAD_TIMEOUT` | 閒置多少秒後自動卸載模型（`0` 停用）    | `0`                     |
| `REVELIO_OUTPUT_DIR`     | 圖片 OCR 輸出目錄                       | `~/revelio/ocr_results` |

## Language Support

- 繁體中文（`ch_tra`）
- 英文（`en`）

EasyOCR 支援 80+ 語言，opendataloader-pdf hybrid mode 亦同。兩者皆使用 `ch_tra` 作為繁體中文語言碼。

## Dependencies

- Python 3.11+
- uv（Python 套件管理器）
- EasyOCR + PyTorch（圖片 OCR）
- Java 11+ 與 opendataloader-pdf（PDF 解析，外部安裝）
