# ADR-001: Dual Mode Architecture (MCP + Skill)

## Status

Accepted

## Date

2025-02-02

## Context

使用者需要本地 OCR 功能來處理圖片中的文字。然而，不同情境有不同的隱私需求：

1. **一般情境**：快速處理，讓 AI 立即協助分析
2. **敏感情境**：處理含有個人資訊的文件，不希望內容自動進入 AI 對話

最初只建立了 MCP Server，所有 OCR 結果會直接回傳給 Claude，這在處理敏感文件時造成隱私顧慮。

## Decision

採用雙模式架構：

### Mode 1: MCP Server（快速模式）

- OCR 結果直接回傳至對話
- 適合一般用途
- 使用方式：Claude 自動呼叫 MCP 工具

### Mode 2: `/ocr-local` Skill（隱私模式）

- OCR 結果存至本地檔案
- Claude **不會自動讀取**結果
- 必須經過使用者明確同意才會讀取
- 使用方式：使用者輸入 `/ocr-local`

## Consequences

### Positive

- 使用者可根據情境選擇適合的模式
- 敏感內容不會在未經同意下進入 AI 對話
- 保留快速處理的便利性

### Negative

- 維護兩套整合方式
- 使用者需了解兩種模式的差異

### Neutral

- 底層都使用同一個 EasyOCR 引擎
- 結果格式一致

## Alternatives Considered

### 只保留 MCP Server

- 優點：簡單
- 缺點：無法滿足隱私需求
- 結論：拒絕

### 只保留 Skill

- 優點：隱私優先
- 缺點：一般用途太繁瑣
- 結論：拒絕

### 在 MCP 加入隱私選項

- 優點：單一介面
- 缺點：MCP 協議設計上結果會回傳，難以實現「不讀取」
- 結論：技術限制，拒絕

## References

- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [Claude Code MCP 文件](https://docs.anthropic.com/claude-code/mcp)
- [Claude Code Skills 文件](https://docs.anthropic.com/claude-code/skills)
