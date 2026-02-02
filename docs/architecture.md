# Architecture

## Overview

Revelio 提供兩種 OCR 使用模式，讓使用者根據隱私需求選擇適合的方式。

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐         ┌─────────────────┐           │
│   │  MCP Server     │         │  /ocr-local     │           │
│   │  (Fast Mode)    │         │  Skill          │           │
│   │                 │         │  (Private Mode) │           │
│   └────────┬────────┘         └────────┬────────┘           │
│            │                           │                     │
│            │ 結果直接回傳               │ 結果存檔            │
│            │                           │ 詢問是否讀取        │
│            ▼                           ▼                     │
│   ┌─────────────────────────────────────────────┐           │
│   │              EasyOCR Engine                  │           │
│   │         (Local Python Process)              │           │
│   └─────────────────────────────────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. EasyOCR MCP Server

**位置**：`~/.claude/easyocr-mcp/`

**功能**：

- 提供 MCP 協議介面讓 Claude Code 直接呼叫
- OCR 結果直接回傳至對話上下文

**適用場景**：

- 一般圖片處理
- 需要 AI 立即分析結果
- 非敏感內容

**工具**：

- `ocr_image_file` - 從檔案路徑辨識
- `ocr_image_base64` - 從 base64 編碼辨識
- `ocr_image_url` - 從 URL 辨識

### 2. `/ocr-local` Skill

**位置**：`~/.claude/skills/ocr-local/`

**功能**：

- 執行本地 OCR 腳本
- 結果存至 `~/.claude/ocr_results/`
- **不自動讀取結果**，需使用者同意

**適用場景**：

- 敏感文件（身分證、合約、醫療紀錄）
- 隱私優先的工作流程
- 使用者想保留控制權

### 3. 本地腳本

**位置**：`~/.claude/easyocr-mcp/ocr_to_file.py`

**功能**：

- 獨立執行 OCR 並存檔
- 被 Skill 呼叫

## Data Flow

### MCP Mode（快速模式）

```
User Request → Claude → MCP Tool Call → EasyOCR → Result → Claude → User
                                                     ↑
                                              (直接進入對話)
```

### Skill Mode（隱私模式）

```
User: /ocr-local → Claude → Bash Script → EasyOCR → File
                                                      │
                     ┌────────────────────────────────┘
                     ▼
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
~/.claude/
├── easyocr-mcp/
│   ├── server.py          # MCP Server 主程式
│   ├── ocr_to_file.py     # 獨立 OCR 腳本
│   └── pyproject.toml     # Python 依賴定義
├── skills/
│   └── ocr-local/
│       └── SKILL.md       # Skill 定義
└── ocr_results/
    └── *.txt              # OCR 輸出檔案
```

## Language Support

目前支援：

- 繁體中文 (`ch_tra`)
- 英文 (`en`)

EasyOCR 支援 80+ 語言，未來可擴充。

## Dependencies

- Python 3.11+
- uv (Python package manager)
- EasyOCR
- PyTorch (EasyOCR 依賴)
