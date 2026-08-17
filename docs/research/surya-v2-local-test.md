# surya v2 本地實測記錄（Feature 1 表格驗證層選型）

測試日期：2026-08-18
環境：Mac mini M4、16GB RAM、macOS（Darwin 25.5.0）、無 CUDA
依據：`docs/research/watchlist/vlm-ocr-fallback.md` 的候選優先序，surya v2 為首選，本文為實機驗證結果。

## 結論

surya v2 通過三項門檻，建議定為 Feature 1 表格驗證層的驗證模型：

1. **Apple Silicon 可跑**：llama.cpp（Metal 後端）加 surya-ocr Python 套件，開箱即用
2. **記憶體**：llama-server 常駐 RSS 約 2.9GB，與現有 EasyOCR fallback（約 2.6GB）同量級
3. **品質**：在掃描版 ResNet benchmark 的全部 4 個 baseline 失敗點上都辨識正確，繁體中文樣本與原文文字層逐字一致

尚未完成：TSMC 中文財報（CID 字型）的實測。源 PDF 已不在本機（僅剩 4 月的轉換輸出），需重新下載後補測。

## 安裝與環境

```bash
brew install llama.cpp          # build 10450
python3 -m venv ~/surya-env
source ~/surya-env/bin/activate
pip install surya-ocr pymupdf   # surya-ocr 0.22.1
```

模型權重（surya-ocr-2-gguf，0.65B）在首次推論時由 llama-server 自動從 HuggingFace 下載。surya 套件會自行 spawn 與管理 llama-server 程序，用完自動回收。

### 已知陷阱：guided decoding 與 brew 版 llama.cpp 不相容

`LayoutPredictor` 預設走 guided JSON decoding，llama-server（build 10450）把 JSON schema 轉 grammar 時報 `Failed to initialize samplers: failed to parse grammar`，版面偵測回傳 0 個區塊。關閉引導解碼即恢復正常：

```bash
export SURYA_GUIDED_LAYOUT=false
```

`RecognitionPredictor` 與 `TableRecPredictor` 不受影響。

## 效能實測（200dpi 渲染頁面，單一串流）

| 項目                                      | 耗時           |
| ----------------------------------------- | -------------- |
| 套件初始化（模型已下載）                  | 約 1 至 8 秒   |
| 全頁文字辨識（英文論文頁）                | 87 至 96 秒/頁 |
| 全頁文字辨識（中文法律文件頁）            | 31 秒/頁       |
| 版面偵測（LayoutPredictor）               | 約 13 秒/頁    |
| 表格結構辨識（TableRecPredictor，裁切區） | 1.5 至 3 秒/表 |
| 表格裁切區文字辨識（含 HTML 輸出）        | 2 至 15 秒/表  |
| llama-server 常駐記憶體                   | 2.9GB RSS      |

對 Feature 1 的含意：驗證層不需要走全頁辨識（90 秒級），只需版面偵測找表格 bbox（13 秒）加逐表裁切辨識（每表數秒），單頁驗證成本估 15 至 30 秒。

## 品質實測

### 掃描版 ResNet（benchmark baseline 12/16 的 4 個失敗點）

baseline（opendataloader-pdf force-OCR 路徑）失敗的 4 項，surya 全數辨識正確：

| baseline 失敗點                        | surya 結果                  |
| -------------------------------------- | --------------------------- |
| 標題「4.2. CIFAR-10 and Analysis」遺失 | 正確辨識（第 8 頁）         |
| ResNet-101 列缺 21.75                  | 正確辨識（第 6 頁 Table 4） |
| ResNet-152 列缺 4.49                   | 正確辨識（第 7 頁 Table 5） |
| 標籤「ResNet (ILSVRC'15)」遺失         | 正確辨識                    |

另驗證 baseline 最具代表性的缺陷「3.57 被讀成 357（小數點丟失）」：surya 讀出 `3.57`，全文無 `357` 誤讀。

### 表格結構與 cell 文字

第 5 頁雙表測試，流程為 layout 找 bbox、裁切、RecognitionPredictor 輸出 HTML：

- 小表（3 列 3 欄，plain/ResNet 錯誤率）：HTML 表格結構正確，四個數值 27.94、27.88、28.54、25.03 全對（論文公開值）
- 架構表（9 列 7 欄）：結構正確，連 cell 內的卷積設定都以 LaTeX 矩陣（`<math>` 標籤）正確恢復
- `TableRecPredictor` 只回結構（row_id、col_id、bbox），cell 文字需由裁切區辨識取得；驗證層可直接用 RecognitionPredictor 的 HTML 表格輸出

### 繁體中文

以本機一份繁體中文法律文件（有完好文字層可對照）第 4 頁測試：surya 輸出與原文文字層逐字一致，並正確重排欄內斷行、標出粗體標題。CID 字型財報的正式測試待源 PDF 重新下載後進行，以 benchmark 中文版 baseline 12/26 為改善基準。

## 授權注意

surya 模型權重為 openrail 授權：研究、個人使用免費，年營收或募資 500 萬美元以上的商用需另洽 datalab 授權。Revelio 目前定位為個人開源工具，落在免費範圍；若未來商業化需重新評估。llama.cpp（MIT）與 surya-ocr 套件本體（GPL 相容範圍見其 repo）不受此限。

## 後續

1. 請使用者重新下載 TSMC 2025 Q3 中文版合併財報 PDF（investor.tsmc.com），補 CID 字型實測
2. 解 PRD Feature 1 兩個待決問題（驗證範圍、驗收標準）後開始實作驗證層
3. deepseek-ocr.rs 與 Qwen2-VL-OCR-2B 暫不需實測，surya 已達標；若中文 CID 補測不理想再啟動
