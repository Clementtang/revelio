# 上游 easyocr-mcp 記憶體管理實作追蹤

日期：2026-08-14

## 背景

Revelio 曾向上游 [WindoC/easyocr-mcp Issue #1](https://github.com/WindoC/easyocr-mcp/issues/1) 提交 smart memory management 建議（延遲載入、閒置自動卸載、`unload_ocr_models` tool）。TODO.md 原記錄該 issue 自 2026-02-05 起「停滯」。本次調研確認上游其實已在背景把功能做進 codebase，只是沒有回到 issue 留言告知。

## 時間軸（已驗證）

- 2026-02-03：上游開 PR「Add memory controls and unload options」（commit `abbd5d8`）
- 2026-02-04：追加 `_clear_reader_cache` 內的 `gc.collect()`（commit `c663e40`）
- 2026-02-05：Clement 在 issue #1 留言，提供 MPS 環境測試數據（ADR-002 依據）
- 2026-04-15：`memory-controls` 分支合併進 master（PR #2, commit `29f91e2`）
- Issue #1 目前狀態：**仍為 open**，上游未在 issue 上回覆或關閉，但功能已在 README／原始碼中生效

## 逐項比對

| 項目                 | Revelio ADR-002 設計                                           | Revelio `server.py` 現況                                             | 上游 easyocr-mcp 現況                                                                                                                                       |
| -------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 延遲載入模型         | 已規劃（reader 首次使用才建立）                                | 已實作（`get_reader` 內 `if cache_key not in _reader_cache` 才建立） | 已實作，機制相同                                                                                                                                            |
| Reader cache         | 已規劃                                                         | 已實作（`_reader_cache` dict）                                       | 已實作                                                                                                                                                      |
| 閒置自動卸載         | 已規劃（`unload_ocr_models` + `EASYOCR_UNLOAD_TIMEOUT`）       | **未實作**（`server.py` 目前只有 cache，無卸載邏輯、無背景執行緒）   | 已實作：背景 daemon thread（`_unload_watcher_loop`）每 10 秒輪詢，閒置超過 `EASYOCR_UNLOAD_TIMEOUT`（預設 300 秒，設 0 停用）即呼叫 `_clear_reader_cache()` |
| 手動卸載 tool        | 已規劃                                                         | 未實作                                                               | 已實作：`unload_ocr_models` tool                                                                                                                            |
| 每次呼叫後即卸載     | 未提及                                                         | 未實作                                                               | 已實作：`unload_jobdone` 參數（call 層級） + `UNLOAD_JOBDONE` 環境變數（全域預設）                                                                          |
| 記憶體釋放手法       | `gc.collect()`，ADR-002 驗證 MPS 下有效，CUDA 下上游回報不可靠 | 無相關程式碼                                                         | 仍是 `gc.collect()`，**未採用 subprocess isolation**，與上游當初回應的立場（懷疑 gc.collect 在其環境下無效）不一致，但實作上並未進一步處理跨平台差異        |
| Subprocess isolation | ADR-002 列為未來方向，尚未決定是否跟進                         | 無                                                                   | 未採用                                                                                                                                                      |

## 觀察

上游最終選擇的方案和 Clement 在 issue 上建議、以及 ADR-002 記錄的設計幾乎一致：背景執行緒輪詢 + `gc.collect()`，而不是上游當初在 issue 討論中傾向的 subprocess isolation。這代表 ADR-002 中「上游若採用 subprocess isolation 應評估跟進」的前提目前不成立，可以維持觀察即可，不需要動作。

Revelio 自家 `src/mcp-server/server.py`（`/Users/clementtang/revelio/src/mcp-server/server.py`）目前**沒有任何卸載機制**，只有 `_reader_cache` 字典做效能快取，模型載入後會一直留在記憶體，這點與 ADR-002 文字描述（「現有實作（auto-unload + `unload_ocr_models` tool）」）不符，屬於文件與程式碼落差，非本次任務範圍但建議另開項目處理。

## 建議（僅供參考，未動 server.py）

1. 可直接參考上游 `_unload_watcher_loop` 的 daemon thread 輪詢設計，補上 `EASYOCR_UNLOAD_TIMEOUT` 與 `unload_ocr_models` tool，實作成本低且已有上游程式碼可參照
2. 上游的 `unload_jobdone` per-call 參數是額外亮點，如果 Revelio 使用情境是單次批次處理後就不再用，這個設計比純 timeout 更精準，可一併考慮
3. gc.collect() 手法在 Apple Silicon MPS 下已由 ADR-002 驗證有效，補上機制不需要等 subprocess isolation
4. 建議同步修正 ADR-002 與程式碼不一致的描述

## 後記（2026-08-15）

本報告的「Revelio server.py 現況」欄以 2026-04 的本地 clone 為準，已過時：origin/main 0.5.0 起（cloud session PR #1）server.py 已有 Timer 式閒置卸載與 `unload_ocr_models` tool，ADR-002 的文件與程式碼落差已不存在。仍成立的結論：上游未採用 subprocess isolation；`unload_jobdone` 與 in-flight 保護為 0.6.0 尚缺、於 2026-08-15 補上的項目。

## 參考

- [Issue #1](https://github.com/WindoC/easyocr-mcp/issues/1)（open）
- [PR #2 memory-controls](https://github.com/WindoC/easyocr-mcp/pull/2)
- [上游 easyocr-mcp.py 原始碼](https://github.com/WindoC/easyocr-mcp/blob/master/easyocr-mcp.py)
- ADR-002：`/Users/clementtang/revelio/docs/decisions/002-memory-management-strategy.md`
