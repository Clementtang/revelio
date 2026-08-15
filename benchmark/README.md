# Regression Benchmark

以「刁鑽文件」為基準的轉換品質回歸測試（PRD Feature 3）。任何引擎更換、依賴升級或
參數調整，都先跑這裡的 benchmark 再比較前後分數，取代憑印象判斷「有沒有變準」。

方法論參考 Fast360 與 olmOCR-bench：用少量針對性文件分類測試（無邊框表格、CID 字型、
掃描件），不追求泛用準確率。比對粒度為完整結構比對（2026-08-15 裁決）：標題、表格
數量/欄數/列數下限、關鍵數字逐列驗證。

## 執行方式

```bash
python3 run_benchmark.py ground-truth/<document>.json <converted-output>.md
```

exit code 0 表示全數通過；每項 FAIL 會列出缺的標題、列數不足或數字不符的位置。

## 文件集

| 文件                          | 考驗重點                                 | Ground truth                                    | 狀態                      |
| ----------------------------- | ---------------------------------------- | ----------------------------------------------- | ------------------------- |
| `tsmc-2025q3-consolidated-en` | 無邊框表格、多欄對齊、大量數字           | `ground-truth/tsmc-2025q3-consolidated-en.json` | 已凍結（2026-08-16 核可） |
| `tsmc-2025q3-consolidated-zh` | CID 字型（無 ToUnicode）、force-OCR 路徑 | `ground-truth/tsmc-2025q3-consolidated-zh.json` | 待核可（標籤與標題）      |

規劃中（依 PRD 分批建置）：TSMC 中文版（CID 字型 + force-OCR 路徑）、多欄學術論文、
掃描件。

測試 PDF 不放進 repo（授權與體積考量），ground truth 的 `source.url` 記錄公開下載來源。

## Ground truth 建置準則

- 關鍵數字只收**已驗證**的值：人工核對過（如 README 範例表格），或算術交叉驗證
  （小計加總等於總計）。未驗證的列寧可不收，不猜
- 每份 ground truth 建好後需 Clement 抽查核可，之後凍結；改動需在 `source.notes` 留紀錄
- 標籤以文件原文為準，不遷就轉換器輸出。轉換器把標籤拆行或錯位時，benchmark 應該
  fail，那正是要抓的缺陷

## Baseline（0.6.0, opendataloader-pdf hybrid mode）

`tsmc-2025q3-consolidated-en`：**26/27**（2026-08-16）

唯一 fail 是已知缺陷：資產負債表的「Total noncurrent assets」標籤被拆成兩列
（`assets` 與 `Total noncurrent` 分離）。損益表 12 組關鍵數字全數正確。

`tsmc-2025q3-consolidated-zh`（2026-08-16，同一份文件的中文版，CID 字型）：

| 轉換設定                             | 分數  | 說明                                                                                                   |
| ------------------------------------ | ----- | ------------------------------------------------------------------------------------------------------ |
| hybrid（未 force-OCR）               | 3/26  | 文字層不可解碼，輸出幾乎全毀                                                                           |
| force-OCR 第一版                     | 3/26  | 與未 force-OCR 相同（設定未生效的歷史產物）                                                            |
| force-OCR + `--ocr-lang "ch_tra,en"` | 12/26 | 數字大多完好；失敗集中在 OCR 字元錯誤（資→賁、權→榷 使標籤比不到）、標題全數丟失、標籤與數值拆到相鄰列 |

中英對照（26/27 vs 12/26）即為 CID 字型 + 視覺 OCR fallback 路徑的品質差距量化。
若引入 VLM OCR fallback（PRD Feature 1 的候選模型），以 12/26 為改善基準。

## 已知限制

- 只驗證「正確值有出現在正確標籤的列上」，不驗證欄位順序與百分比欄，也不偵測
  多抓的雜訊列（列數只驗下限）
- 資產負債表的部分明細列（如 Salary and bonus payable）在 baseline 輸出中有錯位，
  但因無法驗證原始值，未納入 ground truth；表格驗證層（PRD Feature 1）落地後補強
