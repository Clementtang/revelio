# Revelio

> _Revelio_ - 顯形咒，揭示隱藏之物

本地隱私優先的 OCR 解決方案，使用 EasyOCR 在本機執行文字辨識，確保敏感內容不會上傳至雲端。

## 功能特色

- **隱私優先**：所有 OCR 處理都在本機完成
- **繁中支援**：支援繁體中文 (`ch_tra`) + 英文 (`en`)
- **Claude Code 整合**：提供 MCP Server 與 Skill 兩種使用方式
- **使用者控制**：Skill 模式下，使用者可選擇是否讓 AI 讀取結果

## 使用方式

### 方式一：`/ocr-local` Skill（隱私模式）

```
/ocr-local
```

- 結果存至本地檔案
- Claude 不會自動讀取，需使用者同意
- 適合處理敏感內容

### 方式二：EasyOCR MCP Server（快速模式）

Claude Code 可直接呼叫 MCP 工具進行 OCR，結果會直接進入對話。

適合一般用途、需要 AI 立即處理結果的情況。

## 檔案位置

| 元件       | 路徑                          |
| ---------- | ----------------------------- |
| MCP Server | `~/.claude/easyocr-mcp/`      |
| Skill 定義 | `~/.claude/skills/ocr-local/` |
| OCR 結果   | `~/revelio/ocr_results/`      |

### 自訂輸出位置

設定環境變數 `REVELIO_OUTPUT_DIR` 可自訂 OCR 結果存放位置：

```bash
export REVELIO_OUTPUT_DIR="/path/to/your/folder"
```

## 技術棧

- **OCR 引擎**：[EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **Python 環境**：[uv](https://github.com/astral-sh/uv)
- **整合平台**：Claude Code (MCP + Skills)

## 文件

- [架構說明](docs/architecture.md)
- [安裝設定](docs/setup.md)
- [決策記錄](docs/decisions/)
- [變更日誌](CHANGELOG.md)

## License

MIT
