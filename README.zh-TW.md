<div align="center">

# Revelio

![License](https://img.shields.io/github/license/Clementtang/revelio)
![Top Language](https://img.shields.io/github/languages/top/Clementtang/revelio)
![Last Commit](https://img.shields.io/github/last-commit/Clementtang/revelio)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Java](https://img.shields.io/badge/java-11+-orange)

> _Revelio_（顯形咒）— 哈利波特中用於揭示隱藏事物的咒語。

繁體中文 | [English](README.md)

</div>

在哈利波特的世界中，_Revelio_（顯形咒）是一個用於揭示隱藏物品、秘密訊息和隱形事物的咒語。這個專案做的事情一樣 — 揭示文件中隱藏的文字與結構，同時保護你的敏感內容隱私。

本地隱私優先的文件處理工具，整合於 [Claude Code](https://claude.ai/code)。Revelio 透過 [EasyOCR](https://github.com/JaidedAI/EasyOCR) 辨識圖片文字，並透過 [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf) 解析 PDF 結構（表格、標題、閱讀順序）。所有處理都在你的裝置上完成，敏感內容絕不上傳雲端。

## 功能特色

- **隱私優先** — 所有處理在本機執行，不上傳任何資料
- **雙工具，單一入口** — `/revelio` skill 依副檔名自動選擇：
  - 圖片（`.jpg`, `.png`, `.bmp`, `.tiff` 等）→ **EasyOCR**
  - PDF（`.pdf`）→ **opendataloader-pdf**（保留表格、標題、閱讀順序）
- **手動指定** — 使用 `--ocr` 或 `--pdf` 強制指定工具
- **使用者掌控** — Skill 模式下，由你決定是否讓 Claude 讀取結果
- **多語言支援** — 預設繁體中文 + 英文，兩個工具都支援 80+ 種語言

## 範例輸出

以下是 [台積電 2025 Q3 合併財務報告](https://investor.tsmc.com/english/quarterly-results/2025/q3)（公開資訊）經 opendataloader-pdf **hybrid mode** 轉換的實際輸出。

**損益表** — 轉換為結構化 Markdown 表格，數字精準、欄位分明：

|                            | 2025 Q3 Amount | %   | 2024 Q3 Amount | %   | 2025 9M Amount  | %   | 2024 9M Amount  | %   |
| -------------------------- | -------------- | --- | -------------- | --- | --------------- | --- | --------------- | --- |
| NET REVENUE                | $ 989,918,318  | 100 | $ 759,692,143  | 100 | $ 2,762,963,851 | 100 | $ 2,025,846,521 | 100 |
| COST OF REVENUE            | 401,375,489    | 41  | 320,346,477    | 42  | 1,133,656,708   | 41  | 913,871,108     | 45  |
| GROSS PROFIT               | 588,542,829    | 59  | 439,345,666    | 58  | 1,629,307,143   | 59  | 1,111,975,413   | 55  |
| Research and development   | 63,742,245     | 6   | 52,783,826     | 7   | 181,569,457     | 7   | 146,950,466     | 7   |
| General and administrative | 20,048,234     | 2   | 22,890,591     | 3   | 63,887,355      | 2   | 58,317,959      | 3   |
| Marketing                  | 3,973,966      | -   | 3,404,487      | 1   | 12,002,028      | -   | 9,463,070       | 1   |
| Total operating expenses   | 87,764,445     | 8   | 79,078,904     | 11  | 257,458,840     | 9   | 214,731,495     | 11  |
| INCOME FROM OPERATIONS     | 500,684,818    | 51  | 360,766,289    | 47  | 1,371,189,264   | 50  | 896,340,137     | 44  |
| INCOME BEFORE INCOME TAX   | 525,369,023    | 53  | 384,186,852    | 51  | 1,449,299,639   | 52  | 957,040,631     | 47  |
| INCOME TAX EXPENSE         | 73,613,661     | 7   | 59,106,682     | 8   | 239,318,192     | 8   | 159,077,760     | 8   |
| NET INCOME                 | 451,755,362    | 46  | 325,080,170    | 43  | 1,209,981,447   | 44  | 797,962,871     | 39  |

**中文損益表** — 同一份報告的中文版。部分中日韓 PDF 的字型嵌入方式缺少 Unicode 對照表（CID-keyed fonts without ToUnicode CMap），導致文字層無法直接解析。在 hybrid server 加上 `--force-ocr --ocr-lang "ch_tra,en"` 後改走視覺 OCR，成功還原中文內容（有少量 OCR 辨識瑕疵）：

| 代碼 | 科目         | 2025 Q3 金額 | %   | 2024 Q3 金額 | %   | 2025 9M 金額    | %   | 2024 9M 金額    | %   |
| ---- | ------------ | ------------ | --- | ------------ | --- | --------------- | --- | --------------- | --- |
| 4000 | 營業收入淨額 | 989,918,318  | 100 | 759,692,143  | 100 | $ 2,762,963,851 | 100 | $ 2,025,846,521 | 100 |
| 5000 | 營業成本     | 401,375,489  | 41  | 320,346,477  | 42  | 1,133,656,708   | 41  | 913,871,108     | 45  |
|      | 營業毛利     | 588,542,829  | 59  | 439,345,666  | 58  | 1,629,307,143   | 59  | 1,111,975,413   | 55  |
| 6300 | 研究發展費用 | 63,742,245   | 6   | 52,783,826   | 7   | 181,569,457     | 7   | 146,950,466     | 7   |
| 6100 | 行銷費用     | 3,973,966    | -   | 3,404,487    | 1   | 12,002,028      | -   | 9,463,070       | 1   |
| 6000 | 合計         | 87,764,445   | 8   | 79,078,904   | 11  | 257,458,840     | 9   | 214,731,495     | 11  |
| 6900 | 營業淨利     | 500,684,818  | 51  | 360,766,289  | 47  | 1,371,189,264   | 50  | 896,340,137     | 44  |
| 7900 | 稅前淨利     | 525,369,023  | 53  | 384,186,852  | 51  | 1,449,299,639   | 52  | 957,040,631     | 47  |
| 7950 | 所得稅費用   | 73,613,661   | 7   | 59,106,682   | 8   | 239,318,192     | 8   | 159,077,760     | 8   |
| 8200 | 本期淨利     | 451,755,362  | 46  | 325,080,170  | 43  | 1,209,981,447   | 44  | 797,962,871     | 39  |

> **為什麼需要不同模式？** 英文版 PDF 使用標準字型，附帶 Unicode 對照表，hybrid mode 可直接從 PDF 結構提取文字。中文版 PDF 使用 CID-keyed fonts 但缺少 ToUnicode CMap，文字層無法解讀。加上 `--force-ocr --ocr-lang "ch_tra,en"` 後，hybrid server 改為以視覺方式讀取頁面影像（OCR），成功還原內容，但會產生少量辨識瑕疵（例如「二十」被誤讀為「二+」）。

## 快速開始

### 環境需求

- macOS 或 Linux
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（Python 套件管理器）
- [Claude Code](https://claude.ai/code) CLI
- **Java 11+**（opendataloader-pdf 需要）

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

3. **設定 EasyOCR MCP server** — 在 `~/.claude.json` 的 `mcpServers` 中加入：

   ```json
   {
     "mcpServers": {
       "revelio": {
         "command": "uv",
         "args": [
           "--directory",
           "/Users/<你>/revelio/src/mcp-server",
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

4. **安裝 Skill**：

   ```bash
   cp -r src/skill ~/.claude/skills/revelio
   ```

5. **安裝 opendataloader-pdf**（PDF 功能需要）：

   ```bash
   python3 -m venv ~/odl-env
   source ~/odl-env/bin/activate
   pip install -U "opendataloader-pdf[hybrid]"
   ```

## 使用方式

### `/revelio` Skill — 統一入口

在 Claude Code 中直接呼叫，skill 會自動判斷：

```
你：/revelio ~/Documents/receipt.jpg
Claude：[自動選擇 EasyOCR] 正在執行本地 OCR...
        結果已存至 ~/revelio/ocr_results/receipt_<時間戳>.txt
        是否要讓我讀取內容？

你：/revelio ~/reports/財務報告.pdf
Claude：[自動選擇 opendataloader-pdf] 正在轉換 PDF...
        結果已存至 ~/odl-output/財務報告/
        是否要讓我讀取內容？

你：/revelio --ocr ~/scanned_page.png
Claude：[強制使用 EasyOCR] 正在執行本地 OCR...
```

結果儲存在本地，只有經過你明確同意，Claude 才會讀取。

### MCP Server — 直接處理圖片 OCR

若是非敏感圖片，Claude 可以直接呼叫 MCP 工具，跳過隱私確認流程。只要請 Claude 讀取圖片中的文字即可。

## 設定選項

### 輸出目錄

| 工具               | 預設輸出位置             |
| ------------------ | ------------------------ |
| EasyOCR            | `~/revelio/ocr_results/` |
| opendataloader-pdf | `~/odl-output/`          |

EasyOCR 可透過環境變數自訂：

```bash
export REVELIO_OUTPUT_DIR="/你的/自訂/路徑"
```

### 支援語言

預設：繁體中文（`ch_tra`）+ 英文（`en`）。EasyOCR 支援 80+ 種語言，透過 `EASYOCR_LANGUAGES` 設定：

```bash
export EASYOCR_LANGUAGES="ch_tra,en,ja"
```

opendataloader-pdf 的 hybrid 模式同樣支援 80+ 種 OCR 語言。

## 背景

Revelio 起始於 2026 年初，原本只是一個本地 EasyOCR 的封裝，用於處理敏感圖片的 OCR。2026 年 4 月擴充了 PDF 處理能力，起因是 OCR 在處理結構化文件（財報、研究報告、合約）時有其極限 — OCR 會把表格攤平成純文字、數字欄位錯位，而 opendataloader-pdf 直接解析 PDF 結構，保留表格與數字精準度。

兩個工具互補而非互斥：

- **EasyOCR**（透過 `src/mcp-server/`）— 處理圖片與截圖中的文字
- **opendataloader-pdf**（外部工具，由 skill 呼叫）— 原生 PDF 解析，掃描件可啟用 hybrid OCR

## 技術棧

- **OCR 引擎**：[EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **PDF 解析器**：[opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf)（需要 Java 11+）
- **Python 執行環境**：[uv](https://github.com/astral-sh/uv)
- **整合平台**：Claude Code（MCP 協議 + Skills）

## 專案結構

```
revelio/
├── src/
│   ├── mcp-server/      # EasyOCR MCP server
│   │   ├── server.py
│   │   ├── ocr_to_file.py
│   │   └── pyproject.toml
│   └── skill/           # /revelio skill（路由至 OCR 或 PDF 工具）
│       └── SKILL.md
├── ocr_results/         # EasyOCR 輸出（不納入 git）
└── docs/                # 文件（架構、ADR）
```

### 安裝位置

| 元件                    | 安裝路徑                               | 原始碼                                   |
| ----------------------- | -------------------------------------- | ---------------------------------------- |
| MCP server              | 直接引用自 `~/revelio/src/mcp-server/` | `src/mcp-server/`                        |
| Skill                   | `~/.claude/skills/revelio/`            | `src/skill/`                             |
| OCR 結果                | `~/revelio/ocr_results/`               | —                                        |
| PDF 輸出                | `~/odl-output/`                        | —                                        |
| opendataloader-pdf venv | `~/odl-env/`                           | `pip install opendataloader-pdf[hybrid]` |

## 文件

- [架構說明](docs/architecture.md) — 系統設計與資料流
- [安裝指南](docs/setup.md) — 詳細安裝說明
- [決策記錄](docs/decisions/) — 重大決策的 ADR
- [變更日誌](CHANGELOG.zh-TW.md) — 版本歷程

## 歷程

- **2026-04** — 整合 PDF 處理功能（opendataloader-pdf）；skill 從 `/ocr-local` 改名為 `/revelio`，MCP server 從 `easyocr` 改名為 `revelio`
- **2026-02** — 曾嘗試向 [WindoC/easyocr-mcp](https://github.com/WindoC/easyocr-mcp) 提交 upstream 貢獻（討論停滯）。[Clementtang/easyocr-mcp fork](https://github.com/Clementtang/easyocr-mcp) 已封存，Revelio 自行維護 MCP server 實作。詳見 [ADR-002](docs/decisions/002-memory-management-strategy.md)。

## 授權

MIT

## 貢獻

歡迎貢獻。請先閱讀[架構說明](docs/architecture.md)文件，了解設計理念。
