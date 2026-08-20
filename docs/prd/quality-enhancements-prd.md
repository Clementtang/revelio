# PRD：Revelio 品質強化（大綱版）

> 狀態：大綱＋待決問題清單。2026-08-15 Clement 已裁決：Feature 1 驗證模型採本地 VLM、實作順序 3 → 2 → 1、記憶體管理補強納入本輪（Feature 4）、benchmark 採完整結構比對。
> 2026-08-15 與 origin/main（0.6.0，cloud session PR #1 至 #3 的產出）對齊後修訂：原 Feature 2（CID 偵測自動化）已由 ADR-004 的 pdf-inspector 前置偵測實現，自本 PRD 移除；Feature 4 縮減為 0.6.0 既有卸載機制之上的三點補強。
> 依據：`docs/research/related-projects-2026-08.md` 的優先序結論。
> 標註慣例：【推測】開頭的段落是 Claude 的推測，【已裁決】為 Clement 的判斷，其餘為研究結論或既有事實。

## 背景與問題

Revelio 0.6.0 已有雙引擎架構（ADR-003）與 pdf-inspector 前置偵測（ADR-004），但仍有品質風險靠人工把關：

1. 表格數字錯誤只能靠「人工抽查」（SKILL.md 現行做法），財報場景一個錯數字就是重大風險
2. 沒有 regression benchmark，換引擎或升級依賴時無法客觀比較
3. 記憶體卸載機制有長任務進行中被卸載的時序風險，且缺 jobdone 模式

## Feature 1：表格驗證層（Table Verification）

### 目標

opendataloader-pdf 輸出後，自動比對關鍵數字，把「人工抽查」變成「機器初篩＋人工複核異常」。

### 大綱

- 參考 pattern：Validated Table Extractor（傳統工具抽取，vision LLM 二次驗證比對）
- 流程：轉換完成後，將 PDF 頁面截圖與 markdown 表格交叉比對，標記不一致的 cell
- 輸出：驗證報告（哪些數字有疑慮），附在轉換結果旁
- 定位：選配步驟，預設詢問使用者是否執行

### 待決問題

- [x] 驗證用的 vision 模型跑在哪？【已裁決 2026-08-15】採本地 VLM，維持 privacy-first 與 consent gate 精神。候選模型見 `docs/research/watchlist/vlm-ocr-fallback.md`（優先實測 surya v2 GGUF，次選 deepseek-ocr.rs 量化版、Qwen2-VL-OCR-2B）
- [x] 本地 VLM 的選型【已裁決 2026-08-18，依實測】surya v2（0.65B GGUF，llama.cpp Metal）。實測記錄見 `docs/research/surya-v2-local-test.md`：中英文表格數值全對、記憶體 2.9GB 與 EasyOCR 同量級；弱點在裝飾性大字距標題，與數字驗證無關
- [x] 驗證範圍【已裁決 2026-08-20】只驗數字欄位，不逐 cell 驗文字。依據：surya 數值辨識極強但中文標籤偶有誤讀與幻覺，驗文字會產生假警報；財報場景的真實風險是數字錯
- [x] 不一致時的呈現方式【已裁決 2026-08-15 隨 Feature 1 定位確認】只標記不修正
- [x] 驗收標準【已裁決 2026-08-20】在四份凍結 benchmark 上，對「轉換輸出與 ground truth 不符的數字」漏報為零（baseline 已知數字錯誤如掃描版 357 必須全數被標記）；誤報率不設硬門檻先觀察，驗證報告附信心分數供人工複核排序

### 流程設計（依 2026-08-20 裁決展開）

1. 輸入：源 PDF、轉換輸出 markdown、報告輸出路徑。定位維持選配，由 skill 在轉換完成後詢問是否執行
2. 抽取：解析 markdown 表格，取出全部數字 cell（正規化：千分位逗號、貨幣符號、百分號、括號負數、CJK 字間空格）
3. 獨立辨識：pymupdf 200dpi 渲染各頁，surya LayoutPredictor 找表格 bbox（需 `SURYA_GUIDED_LAYOUT=false`），裁切後 RecognitionPredictor 輸出 HTML 表格，抽出數字
4. 比對：逐頁把 markdown 數字集合與 surya 數字集合對照，markdown 有而 surya 讀不到（或讀出不同值）的數字列為可疑
5. 輸出：驗證報告（頁碼、可疑數字、surya 讀到的值、信心分數），附在轉換結果旁；不改動轉換輸出本身
6. 效能預算：單頁 15 至 30 秒（版面偵測 13 秒加逐表辨識數秒），只在使用者同意時付出

## Feature 2：CID 偵測自動化（已由 ADR-004 實現，移出範圍）

原規劃「skill 自動偵測文字層壞掉的 PDF 並切換 force-ocr」。0.6.0 的 pdf-inspector 前置偵測（ADR-004）已用更好的方式解決：轉換前毫秒級結構分析，逐頁回報 `pages_needing_ocr` 與原因碼（含 `suspected_garbled_text`），偵測失敗時退回啟發式。原待決問題全數消滅，不需再做。

## Feature 3：Regression Benchmark Set

### 目標

把「刁鑽文件」正式化為 benchmark，之後評估新引擎（PaddleOCR、VLM 系）或升級依賴都有客觀依據。

### 大綱

- 方法論參考：Fast360 與 olmOCR-bench，用針對性文件分類測試，而非泛用準確率
- 初始文件集候選：TSMC 2025 Q3 英文財報（標準字型＋無邊框表格）、中文財報（CID 字型）、另需補多欄論文與掃描件各一
- 每份文件配 ground truth（人工核對過的關鍵數字與結構）
- 執行方式：腳本跑轉換、比對 ground truth、輸出分數
- 存放：repo 內 `benchmark/`，測試 PDF 需確認可再散布（公開文件）

### 待決問題

- [x] 比對粒度【已裁決 2026-08-15】完整結構比對（關鍵數字加表格列數、標題層級）。ground truth 建置工作量較大，採分批建置：先建 TSMC 英文財報一份跑通流程，再逐份擴充
- [x] ground truth 誰建？首批由 Claude 建、Clement 抽查核可後凍結（四份均於 2026-08-20 前凍結）
- [x] TSMC 財報 PDF 不進 repo：公開下載 URL + sha256 寫在 ground truth，本機副本在 `benchmark/fixtures/`（gitignore）。`run_suite.py` 以 sha256 閘門驗收
- [x] benchmark 分數不進 CI 的完整 OCR 路徑；CI 只跑 matcher / suite helper。本機 `run_suite.py` 對凍結 baseline 打分

## Feature 4：MCP server 記憶體管理補強

### 目標

0.6.0 已有 Timer 式閒置卸載與 `unload_ocr_models` tool（`server.py`），本 feature 補三點：

1. **in-flight 保護**：現行 Timer 在每次呼叫「結束後」重新計時，前一次呼叫佈下的 timer 可能在長任務（大圖、高解析掃描件）進行中觸發卸載。devil's advocate review（2026-08-15）判定為 Major：呼叫端仍握有 reader 引用不會 crash，但 `gc.collect()` 會在 MPS 運算中於背景執行緒觸發（此時序未經 ADR-002 驗證），且下次呼叫需重付數十秒冷啟動
2. **jobdone 模式**：`EASYOCR_UNLOAD_JOBDONE=1` 每次辨識完成即卸載（預設關閉），對「單次批次處理後不再用」的場景比 timeout 更精準
3. **預設值改為 300 秒**：現行預設 `0`（停用），依裁決改為預設啟用 300 秒閒置卸載

### 待決問題

- [x] timeout 預設值【已裁決 2026-08-15】300 秒，可由 `EASYOCR_UNLOAD_TIMEOUT` 覆寫
- [x] jobdone 模式【已裁決 2026-08-15】一併實作，預設關閉

## 實作順序（已裁決 2026-08-15）

Feature 4 最先（範圍小、可單獨驗收），再 Feature 3（Feature 1 的驗收標準依賴 benchmark 存在，先有尺才能量），最後 Feature 1（待決問題最多）。

## 不做的事（本輪範圍外）

- 更換或新增 OCR 引擎（等 VLM 實測結論，見 watchlist 報告）
- README 信任證明強化（文件工作，隨時可做，不佔本 PRD 範圍）
