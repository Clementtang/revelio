# 變更日誌

本檔案記錄專案的所有重要變更。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)。

## [未發布]

## [0.4.1] - 2025-02-02

### 修復

- 修正 README 中 skill 安裝路徑（`src/skill` 而非 `skills/ocr-local`）
- 統一 Python 版本需求（>=3.11）於 pyproject.toml 與文件
- 更新文件中過時的 `~/.claude/ocr_results/` 路徑為 `~/revelio/ocr_results/`

### 新增

- LICENSE 授權檔案（MIT）
- CONTRIBUTING.md 貢獻指南
- `ocr_to_file.py` 錯誤處理：
  - 驗證圖片檔案存在
  - 處理 EasyOCR 初始化錯誤
  - 處理檔案寫入錯誤

### 變更

- 更新 pyproject.toml 中繼資料（名稱、版本、描述）
- 更新最低依賴版本（pillow、requests、numpy、mcp）

## [0.4.0] - 2025-02-02

### 新增

- 原始碼現已納入版本庫
  - `src/mcp-server/`：EasyOCR MCP Server 實作
  - `src/skill/`：Claude Code Skill 定義
- 各原始碼元件的 README 安裝說明
- 雙語文件（英文 + 繁體中文）
  - `README.md` / `README.zh-TW.md`
  - `CHANGELOG.md` / `CHANGELOG.zh-TW.md`

### 變更

- 更新專案結構文件

## [0.3.0] - 2025-02-02

### 變更

- OCR 結果改存至 `~/revelio/ocr_results/`（原為 `~/.claude/ocr_results/`）
- 輸出目錄可透過 `REVELIO_OUTPUT_DIR` 環境變數自訂
- 設定優先順序：CLI 參數 > 環境變數 > 預設值

### 新增

- 專案內新增 `ocr_results/` 目錄（含 `.gitkeep`）
- `.gitignore` 規則排除 OCR 結果檔案（可能包含敏感資料）

## [0.2.0] - 2025-02-02

### 新增

- `/ocr-local` Skill，提供隱私優先的 OCR 工作流程
  - 結果存至本地檔案，而非回傳給 Claude
  - 使用者必須明確同意，Claude 才會讀取內容
  - 位於 `~/.claude/skills/ocr-local/SKILL.md`

### 變更

- 確立雙模式架構：MCP（快速）vs Skill（隱私）

## [0.1.0] - 2025-02-02

### 新增

- 初始 EasyOCR MCP Server 設定
  - `ocr_image_file`：從本地檔案路徑辨識
  - `ocr_image_base64`：從 base64 編碼辨識
  - `ocr_image_url`：從 URL 辨識
- 支援繁體中文（`ch_tra`）+ 英文（`en`）
- 本地 Python 腳本 `ocr_to_file.py` 供獨立使用
- 結果目錄位於 `~/.claude/ocr_results/`

### 技術細節

- MCP Server 位置：`~/.claude/easyocr-mcp/`
- 使用 `uv` 管理 Python 依賴
- EasyOCR 在本機執行，不呼叫任何雲端 API

---

## 版本歷程摘要

| 版本  | 日期       | 重點                |
| ----- | ---------- | ------------------- |
| 0.4.1 | 2025-02-02 | 錯誤修復與錯誤處理  |
| 0.4.0 | 2025-02-02 | 原始碼與雙語文件    |
| 0.3.0 | 2025-02-02 | 可自訂輸出目錄      |
| 0.2.0 | 2025-02-02 | 隱私優先 Skill 模式 |
| 0.1.0 | 2025-02-02 | 初始 MCP Server     |
