# TODO

追蹤待辦事項與外部依賴。

## Upstream Contributions

### EasyOCR MCP - Memory Management Feature

- **Issue**: https://github.com/WindoC/easyocr-mcp/issues/1
- **Created**: 2026-02-03
- **Status**: 上游已實作（2026-08-14 確認）。Issue 本身仍為 open、上游未在 issue 上回覆或關閉，但功能已於 2026-04-15 合併進 master：背景執行緒閒置自動卸載（`EASYOCR_UNLOAD_TIMEOUT`，預設 300 秒）、`unload_ocr_models` tool、每次呼叫後卸載選項（`unload_jobdone`）。詳見 [調研報告](docs/research/watchlist/easyocr-mcp-memory.md)
- **My Fork**: https://github.com/Clementtang/easyocr-mcp

**內容**：提交 smart memory management 功能

- 延遲載入模型
- 閒置自動卸載（節省 ~2.6GB RAM）
- 新增 `unload_ocr_models` 工具
- 新增 `EASYOCR_UNLOAD_TIMEOUT` 環境變數

**維護者回應**（2026-02-03）：

- `gc.collect()` 在其環境下無法成功釋放 VRAM
- 認為 subprocess isolation 是唯一可靠方案
- 詢問我的測試環境

**我的回覆**（2026-02-05）：

- 提供環境資訊（Mac M4, MPS, 非 CUDA）
- 測試證明 MPS 環境下 `gc.collect()` 可釋放 93.7 MB GPU 記憶體
- 認同 subprocess isolation 作為跨平台方案
- 詳見 [ADR-002](docs/decisions/002-memory-management-strategy.md)

**下一步**：

- 上游似乎不想繼續處理，先擱置
- Revelio 自己的 MCP server 已實作獨立的記憶體管理，不依賴上游
- 如未來上游重啟討論，再評估是否提交 subprocess isolation 方案

### License 詢問

- **Comment**: https://github.com/WindoC/easyocr-mcp/issues/1#issuecomment-3838797789
- **Asked**: 2026-02-03
- **Status**: ✅ 已解決

維護者已新增 Apache License 2.0（與上游 EasyOCR 一致）。`THIRD_PARTY_LICENSES.md` 已更新。

---

## Future Improvements

- [ ] 評估是否移植 subprocess isolation 記憶體管理方案（供 CUDA 環境），見 [ADR-002](docs/decisions/002-memory-management-strategy.md)
- [ ] **逐頁 OCR 分流** — pdf-inspector 的偵測是逐頁的（`pages_needing_ocr` + 原因碼），但 `--force-ocr` 是整個 hybrid server 的旗標，混合文件（部分頁面正常、部分需 OCR）目前仍整份走同一模式。待 opendataloader-pdf 支援逐次轉換指定模式後再評估，見 [ADR-004](docs/decisions/004-pdf-preflight-detection.md)
- [ ] **PDF 路徑的 fixture 驗收測試** — 目前 PDF 流程的邏輯全在 SKILL.md prose 中，無自動化測試。可仿 pdf-inspector 的 golden snapshot 做法：固定幾個 fixture PDF（標準英文、CID 字型無 ToUnicode 中文、無框線表格），端到端比對輸出 Markdown，防止外部引擎升版時輸出悄悄劣化
- [ ] **升版 ruff 時 triage 0.16.x 新規則的 11 個發現**（DTZ005、BLE001、FURB122、PLW1510 等）— CI 目前釘在 0.15.20；其中 BLE001（catch blind `Exception`）是 MCP server 刻意的錯誤正規化設計，升版時決定要改寫或加 `noqa`/規則排除
- [ ] **新增 CLAUDE.md** — 濃縮架構地圖、提交前檢查（ruff/pytest）、repo 慣例（雙語文件同步清單、rename 同步清單），供開發時的 Claude Code 使用

## 已完成

- [x] 在 README 說明 EasyOCR MCP 的來源與授權 — README「History」段與 `THIRD_PARTY_LICENSES.md` 均已註明來源與 Apache 2.0 授權
- [x] PDF force-OCR 決策自動化 — 以 [pdf-inspector](https://github.com/firecrawl/pdf-inspector) 前置偵測取代檔名猜測／試錯重啟（2026-08，見 [ADR-004](docs/decisions/004-pdf-preflight-detection.md)）

## 已廢止

- ~~評估是否將 revelio 的 MCP server 改為依賴 WindoC/easyocr-mcp~~ — Revelio 自行維護 MCP server，不依賴上游
- ~~同步上游 LICENSE (Apache 2.0) 到 fork~~ — fork 已封存，不再維護
