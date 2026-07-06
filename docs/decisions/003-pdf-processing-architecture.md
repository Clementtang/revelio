# ADR-003: PDF 處理架構（雙引擎）

## Status

Accepted

## Date

2026-04

## Context

Revelio 最初只用 EasyOCR 處理圖片。實務上遇到大量結構化 PDF（財報、研究報告、合約）需要處理，但純 OCR 的做法有根本限制：

- OCR 把表格攤平成純文字，欄位對齊資訊全失
- 數字欄位容易錯位、誤讀，財報等對精準度要求高的文件不可接受
- 無法保留標題階層與閱讀順序

我們需要一個能直接解析 PDF 結構（而非把整頁當影像辨識）的方案，同時保留對掃描件的 OCR 後備能力。

## Decision

採用**雙引擎**架構，依輸入類型分流，而非用單一引擎硬撐：

- **圖片** → EasyOCR（既有）
- **PDF** → [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf)

### 為何選 opendataloader-pdf

- 直接解析 PDF 結構，輸出結構化 Markdown/JSON，保留表格、標題、閱讀順序
- hybrid mode 對無邊框表格（財報常見）處理正確
- 對文字層不可用的掃描件／CID 字型 PDF，可加 `--force-ocr` 後備到視覺 OCR
- Apache 2.0 授權，與本專案 MIT 相容

### hybrid mode 為預設

基本模式無法正確處理無邊框表格，實測財報會欄位錯位。因此 skill 一律以 hybrid mode 轉換（`hybrid='docling-fast'`, `hybrid_mode='full'`）。

### 外部安裝、不打包

opendataloader-pdf 依賴 Java 11+ 且體積大，由使用者自行安裝於獨立 venv（`~/odl-env/`），Revelio 以子程序呼叫其 hybrid server。Revelio 不打包、不轉散布、不修改其程式碼，僅在文件中列出授權與出處（見 `THIRD_PARTY_LICENSES.md`）。

### CID 字型 PDF 的處理

部分中日韓 PDF 使用 CID-keyed fonts 但缺少 ToUnicode CMap，文字層無法對應回 Unicode。此時以 `--force-ocr --ocr-lang "ch_tra,en"` 啟動 hybrid server，改走視覺 OCR 還原內容（會有少量辨識瑕疵）。README 的範例輸出示範了這兩種情況。

## Consequences

### Positive

- 結構化文件的表格與數字精準度大幅提升
- 圖片與 PDF 各用最適合的引擎，互補而非互斥
- 授權清楚、不增加打包負擔

### Negative

- 新增 Java 11+ 前置需求與額外安裝步驟
- 兩個引擎、兩套輸出慣例，文件與 skill 邏輯較複雜
- hybrid server 首次啟動約需 30–40 秒（載入 DocumentConverter）

### Neutral

- 兩個引擎都在本機執行，維持隱私優先的核心承諾
- 統一由 `/revelio` skill 入口，使用者不需自行判斷該用哪個引擎

## References

- [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- README「範例輸出」— TSMC 2025 Q3 財報實測（英文標準字型 vs 中文 CID 字型）
