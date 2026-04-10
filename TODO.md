# TODO

追蹤待辦事項與外部依賴。

## Upstream Contributions

### EasyOCR MCP - Memory Management Feature

- **Issue**: https://github.com/WindoC/easyocr-mcp/issues/1
- **Created**: 2026-02-03
- **Status**: 停滯（自 2026-02-05 起上游未回應，超過 2 個月）
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

- [ ] 評估是否將 revelio 的 MCP server 改為依賴 WindoC/easyocr-mcp
- [ ] 在 README 說明 EasyOCR MCP 的來源與授權
- [ ] 同步上游 LICENSE (Apache 2.0) 到 fork
