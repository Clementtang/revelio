# ADR-004: PDF 前置偵測（pdf-inspector）

## Status

Accepted

## Date

2026-08

## Context

ADR-003 建立了 PDF 雙引擎架構後，剩下一個未自動化的判斷：**這份 PDF 要不要加 `--force-ocr`？**

- `--force-ocr` 是 hybrid server 的啟動旗標，不是逐次轉換的參數。選錯模式就要 kill server、以正確旗標重啟，再付一次 30–40 秒的 DocumentConverter 冷啟動成本。
- 原本的判斷方式是啟發式試錯：由檔名/內容猜測是否為中文 PDF，不確定就先用標準模式試轉，發現輸出只剩數字和代碼（CID 字型缺 ToUnicode CMap 的典型症狀）再重啟重試。
- 這個流程依賴模型「事後目視」輸出品質，慢、不可靠，且無法逐頁區分（一份文件裡可能只有部分頁面有問題）。

## Decision

在 skill 的 PDF 分支加入**前置偵測步驟（B-0）**：轉換前先用 [pdf-inspector](https://github.com/firecrawl/pdf-inspector)（Firecrawl 開源的 Rust PDF 分類器，MIT 授權，PyPI 套件名 `pdf-inspector`）分析 PDF 結構，依結果決定 server 啟動旗標。

### 為何選 pdf-inspector

- **毫秒級**：純結構分析（解析字型物件、內容串流運算子），不渲染、不做 OCR，10–50ms 內完成
- **純本地**：Rust 實作、無網路呼叫，符合 Revelio 隱私優先原則
- **偵測正是我們的痛點**：Identity-H 字型缺 ToUnicode 時，會先檢查兩層 fallback（W array 是否形如 Unicode、內嵌字型是否有 cmap 表）才判定不可解碼，誤報率低；另涵蓋掃描件、向量描邊文字、亂碼文字層等情況
- **逐頁 + 原因碼**：回報 `pages_needing_ocr` 與每頁原因（`suspected_garbled_text` / `scanned` / `no_text` / `vector_text`），機器可讀，skill 可直接據此分支
- **安裝輕量**：預編譯 wheel（abi3），裝進既有的 `~/odl-env` 即可，無額外系統依賴

### 偵測結果 → 啟動旗標的對應

| 偵測結果                                              | 啟動旗標                             |
| ----------------------------------------------------- | ------------------------------------ |
| `pages_needing_ocr` 為空                              | 標準模式                             |
| 原因含 `suspected_garbled_text` / `vector_text`       | `--force-ocr --ocr-lang "ch_tra,en"` |
| `pdf_type` 為 `scanned`/`image_based`，或 `scanned`/`no_text` | `--force-ocr --ocr-lang "ch_tra,en"` |

### 偵測失敗時退回啟發式

pdf-inspector 未安裝或執行失敗時，skill 退回 ADR-003 時代的試錯流程（檔名判斷 + 標準模式試轉後目視檢查）。前置偵測是最佳化，不是硬依賴。

### 仍為外部安裝、不打包

與 opendataloader-pdf 相同（ADR-003），pdf-inspector 由使用者安裝於 `~/odl-env/`，Revelio 不打包、不轉散布、不修改其程式碼，僅於 `THIRD_PARTY_LICENSES.md` 列出授權與出處。

## Consequences

### Positive

- 消除「選錯模式 → 重啟 server」的試錯循環，省下 30–40 秒冷啟動與一次無效轉換
- force-OCR 決策從「模型猜測」變成「結構分析」，可重現、可解釋（附原因碼）
- CID 字型缺 ToUnicode 的中文 PDF（README 範例的情境）可在轉換前被準確識別

### Negative

- `~/odl-env` 多一個安裝依賴（約 3MB wheel）
- 偵測是逐頁的，但 `--force-ocr` 仍是整個 server 的旗標——混合文件（部分頁面正常、部分需 OCR）目前仍整份走同一模式，逐頁分流留待未來評估

### Neutral

- skill 的 PDF 分支多一個步驟，但整體流程反而更短（不再需要試錯迴圈）
- pdf-inspector 本身也能輸出 Markdown，但表格品質以 opendataloader-pdf hybrid mode 為準，Revelio 只用它的偵測能力

## References

- [pdf-inspector](https://github.com/firecrawl/pdf-inspector) — Firecrawl 的 PDF 分類與抽取引擎
- [ADR-003](003-pdf-processing-architecture.md) — 雙引擎 PDF 架構與 CID 字型問題背景
- README「範例輸出」— TSMC 2025 Q3 財報實測（英文標準字型 vs 中文 CID 字型）
