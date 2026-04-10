# ADR-002: EasyOCR 記憶體管理策略

## Status

Accepted（上游未回應，維持現行方案）

## Date

2026-02-05

## Context

EasyOCR 模型載入後佔用約 2.6GB RAM（含 ~94MB GPU 記憶體）。MCP Server 長期運行但不一定持續使用 OCR，閒置時記憶體浪費嚴重。

我們在 fork 中實作了 smart memory management（`gc.collect()` + auto-unload），並向上游提交 Issue：
https://github.com/WindoC/easyocr-mcp/issues/1

上游維護者 WindoC 回應：`gc.collect()` 在其環境下無法釋放 VRAM，建議改用 subprocess isolation。

## Investigation

### 測試環境

- Mac mini M4, 16GB unified memory
- PyTorch 2.7.1, MPS (Apple Metal GPU)
- EasyOCR detector + recognizer 均運行於 `mps:0`
- Python 3.13

### 測試結果

模擬 `easyocr-mcp.py` 中的 `dict.clear()` + `gc.collect()` 模式：

```
Before load:    RSS=318 MB  MPS=0.0 MB
After load+OCR: RSS=701 MB  MPS=93.7 MB
After clear+gc: RSS=537 MB  MPS=0.0 MB
→ MPS 記憶體釋放: 93.7/93.7 MB (100%)
```

Reference leak 測試：當 Python reference 未正確釋放時，MPS 記憶體維持 93.7 MB 不會回收，直到 `del` 後才釋放。

### 關鍵發現

| 環境        | `gc.collect()` 釋放 GPU 記憶體 | 原因                             |
| ----------- | ------------------------------ | -------------------------------- |
| Apple MPS   | 有效                           | 統一記憶體架構，CPU/GPU 共享 RAM |
| NVIDIA CUDA | 不可靠（WindoC 回報）          | 獨立 VRAM，與系統 RAM 分離       |

WindoC 的 README 預設安裝指令使用 `cu128`（CUDA 12.8），推測其測試環境為 NVIDIA GPU，但尚未確認。

## Decision

### 現階段：維持 `gc.collect()` 方案

目前我們的使用環境為 Apple Silicon MPS，`gc.collect()` 已驗證有效。現有實作（auto-unload + `unload_ocr_models` tool）在此環境下運作正常。

### 未來方向：關注 subprocess isolation

如果上游採用 subprocess isolation 方案，應評估是否跟進。該方案的優劣：

**優點**：

- 跨平台可靠（MPS、CUDA、CPU 皆適用）
- 終止 process 是唯一保證釋放所有記憶體的方式

**缺點**：

- 實作複雜度提高（IPC、process 生命週期管理）
- 每次 OCR 需啟動新 process，冷啟動延遲增加
- 與目前 reader cache 機制不相容

## Consequences

### Positive

- 在 MPS 環境下，現有方案已滿足需求
- 記錄了跨平台差異，為未來決策提供依據

### Negative

- 現有方案無法保證在 CUDA 環境下有效
- 如果使用者切換到 NVIDIA GPU，需重新評估

## References

- [Issue #1 討論](https://github.com/WindoC/easyocr-mcp/issues/1)
- [我的 fork](https://github.com/Clementtang/easyocr-mcp/commit/bd7e7f5)
- [PyTorch MPS Backend](https://pytorch.org/docs/stable/notes/mps.html)
