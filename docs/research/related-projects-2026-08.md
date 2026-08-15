# 相關專案與方法論研究（2026-08-14）

跨 GitHub、Hacker News、Reddit 的三路調研，目標是找出可強化 Revelio 的參考專案與作法。
研究方式：三個平行 research agent 分頭搜尋，本文為整合結論。

URL 驗證程度：GitHub 與 HN 連結經實際 fetch 或官方頁面確認；Reddit 連結僅透過搜尋結果佐證存在，未逐篇讀留言區。

## 一、與 Revelio 痛點直接對應的參考

### 痛點 1：CJK PDF 的 CID 字型（無 ToUnicode 映射）

- 社群主流思路是繞過壞掉的文字層，直接把頁面當圖片交給 vision 模型。Karpathy 在 HN 的討論（<https://news.ycombinator.com/item?id=45658928>，2025-10）甚至主張像素輸入比文字 token 更省。Revelio 現在的 `--force-ocr` fallback 方向正確，可再往前一步：評估用本地 VLM（DeepSeek-OCR、Qwen3-VL）取代 EasyOCR 當 fallback 引擎。[deepseek-ocr.rs](https://github.com/TimmyOVO/deepseek-ocr.rs) 有免 Python 的量化本機實作。
- [MinerU](https://github.com/opendatalab/MinerU)（77.6k star）的 pipeline 會自動偵測「亂碼 PDF」並切換 OCR（109 語言含 CJK）。這個偵測邏輯正是 SKILL.md 目前靠「檔名看起來是中文就用 force-ocr」的人工判斷可以自動化的部分。

### 痛點 2：無邊框表格與數字精度

- HN 的 DeepSeek-OCR 千分討論（<https://news.ycombinator.com/item?id=45640594>，2025-10）結論：合併儲存格、跨欄標題在所有模型（含 Gemini、Claude）都持續出錯，屬業界公認難題。最實用的 pattern 是「傳統工具抽取，再用 vision LLM 二次驗證比對」，見 Validated Table Extractor（<https://news.ycombinator.com/item?id=46191251>，2025-12）。
- LLM-aided OCR 討論（<https://news.ycombinator.com/item?id=41203306>，2024-08）警告：數字與人名易被 LLM 誤判且難以驗證，「看起來合理但錯的輸出」最危險。數字精度問題不能只靠後處理，需在 pipeline 設計上把數字欄位標為高風險。
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)（87.6k star）的 PP-StructureV3 提供含 cell 座標的表格結構辨識，在複雜發票類表格的 Fast360 評測（<https://news.ycombinator.com/item?id=44937069>，2025-08）表現突出，是 CJK 表格場景最值得評估的互補引擎。

### 痛點 3：EasyOCR 記憶體管理

- 上游 [WindoC/easyocr-mcp](https://github.com/WindoC/easyocr-mcp) 後來實作了 `EASYOCR_UNLOAD_TIMEOUT`（預設 300 秒閒置卸載）加手動 `unload_ocr_models` tool，與當初在 issue #1 提的方案幾乎一致。TODO.md 的「上游停滯」狀態可更新，值得比對其實作與 ADR-002 的差異。
- r/LocalLLaMA 的 2026 年討論（<https://www.reddit.com/r/LocalLLaMA/comments/1sk6kst/what_is_the_best_open_source_ocr_in_2026/>）顯示 EasyOCR 已非社群首選，多被 PaddleOCR 與 VLM 系取代。長期可考慮讓 OCR 引擎可插拔。

## 二、架構與方法論參考

- **路由設計**：[microsoft/markitdown](https://github.com/microsoft/markitdown) 依副檔名路由到轉換器，與 `/revelio` skill 同構，可對照其邊界格式處理。
- **按需 OCR**：[marker](https://github.com/VikParuchuri/marker) 只在必要時觸發 OCR 的判斷策略，可降低 hybrid server 的啟動成本。
- **評測方法論**：Fast360 與 r/LocalLLaMA 的做法一致（<https://www.reddit.com/r/LocalLLaMA/comments/1jz80f1/i_benchmarked_7_ocr_solutions_on_a_complex/>）：用少量「刁鑽文件」（多欄論文、密集表格、CID 字型財報）建針對性測試集，勝過泛用準確率。「沒有萬用解析器」是 Fast360 的核心結論，印證 hybrid mode 依文件特性選工具的架構方向。[olmOCR-bench](https://github.com/allenai/olmocr)（1400 份文件、7000+ 測試案例）的 benchmark 結構可參考。
- **信任證明**：兩串 r/LocalLLaMA 隱私討論（<https://www.reddit.com/r/LocalLLaMA/comments/1shpw5a/are_people_actually_comfortable_putting_sensitive/>、<https://www.reddit.com/r/LocalLLaMA/comments/1qnujer/how_are_you_guys_handling_sensitive_data_with/>）顯示社群在意「如何證明資料沒離開本機」。Revelio 的 consent gate 已是差異化賣點，README 可更明確說明驗證方式（例如斷網可用、無外連請求）。
- **skill/MCP 包裝已被驗證**：r/ClaudeAI 有使用者主動求 PDF 解析 skill/MCP（<https://www.reddit.com/r/ClaudeAI/comments/1sihiyk/best_skillspluginsmcps_for_parsing_large_pdf/>），也有人分享 PDF 轉知識庫 skill（<https://www.reddit.com/r/ClaudeAI/comments/1radpx2/i_built_a_claude_code_skill_that_turns_any_pdf/>）。Revelio 的定位正好對應此需求缺口。

## 三、其他值得記錄的 repo

| Repo                                                                                                             | 定位                          | 對 Revelio 的參考價值                                                    |
| ---------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------ |
| [docling](https://github.com/docling-project/docling)（64.8k star）                                              | IBM/LF AI 文件轉換引擎        | pipeline 拆分方式、表格結構模型                                          |
| [surya](https://github.com/VikParuchuri/surya)                                                                   | OCR + 版面 + 表格，90+ 語言   | Surya 2 單一 650M 模型可在 Apple Silicon 用 llama.cpp 跑，體積與可攜性佳 |
| [PDF-Extract-Kit](https://github.com/opendatalab/PDF-Extract-Kit)                                                | MinerU 底層版面偵測工具包     | 只想借鏡表格/版面偵測模組時單獨參考                                      |
| [GOT-OCR2.0](https://github.com/Ucas-HaoranWei/GOT-OCR2.0)                                                       | 端到端 OCR-2.0 模型，中英文強 | 架構思路；授權僅供研究用途 [UNVERIFIED 是否可商用]                       |
| [markitdown](https://github.com/microsoft/markitdown)（25k+ star）                                               | 多格式轉 markdown             | 副檔名路由設計                                                           |
| [mcp-mistral-ocr](https://github.com/everaldo/mcp-mistral-ocr)                                                   | 雲端 OCR 包 MCP               | base64/file/url 三種輸入 tool 的介面設計                                 |
| PaddleOCR 官方 [mcp_server](https://paddlepaddle.github.io/PaddleOCR/main/version3.x/deployment/mcp_server.html) | PP-StructureV3 包成 MCP       | 官方 tool schema 設計                                                    |

## 四、優先序結論

1. **表格驗證層**（低成本高價值）：在 skill 流程加「opendataloader 輸出後用 vision 比對關鍵數字」的選配步驟，直擊財報使用場景的最大風險。
2. **CID 偵測自動化**：把「先試標準模式、輸出缺中文就重試 force-ocr」寫進 skill 成為自動 fallback，參考 MinerU 的偵測邏輯。
3. **建 benchmark set**：把現有 TSMC 中英文財報案例正式化為 regression benchmark，之後評估任何新引擎都有依據。
4. **觀察名單**（另行深入調研）：PaddleOCR PP-StructureV3（CJK 表格）、DeepSeek-OCR 本地化實作（VLM fallback）、上游 easyocr-mcp 的記憶體管理實作。

> 後記（2026-08-15）：本研究進行時本地 clone 落後 origin/main 四個月。0.6.0（cloud session PR #1 至 #3）已實現上述第 2 項：ADR-004 以 pdf-inspector 做轉換前結構偵測，比本文建議的「轉後檢查重試」更好。第 1、3 項與觀察名單仍有效，後續依 `docs/prd/quality-enhancements-prd.md` 推進。
