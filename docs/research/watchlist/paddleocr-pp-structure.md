# PaddleOCR PP-StructureV3 調研：CJK 表格互補引擎評估

調研日期：2026-08-14

## 背景

Revelio 目前圖片走 EasyOCR、PDF 走 opendataloader-pdf hybrid mode。痛點是 CJK 財報中的無邊框表格辨識與數字精度。本文評估 PaddleOCR 的 PP-StructureV3 是否適合作為互補引擎，運行環境為 Mac mini（Apple Silicon M4，MPS，無 CUDA）。

## 表格結構辨識能力

PP-StructureV3 是文件解析 pipeline，整合版面偵測（PP-DocLayout-plus）、OCR（PP-OCRv5）、表格辨識、公式辨識與版面還原，輸出 Markdown 與 JSON，也支援匯出 DOCX。（[官方文件](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-StructureV3/PP-StructureV3.en.md)）

表格結構模組（SLANet 系列）明確針對無邊框與複雜表格設計：SLANet_plus 改善「無邊框與複雜表格」辨識，SLANeXt_wireless 有專門的無邊框權重。輸出格式是 HTML tag 序列（含 `colspan`/`rowspan` 表示合併儲存格）加上每個儲存格的座標框與信心分數，並非單純 Markdown 表格。（[table_structure_recognition 文件](https://paddlepaddle.github.io/PaddleX/3.3/en/module_usage/tutorials/ocr_modules/table_structure_recognition.html)）模型輕量，SLANet/SLANet_plus 僅 6.9MB，新一代 SLANeXt_wired 351MB、精度較高但推論較慢。

官方基準測試中，PP-StructureV3 的 TableEdit 錯誤率中文為 0.109、英文為 0.159（數字愈低愈好），中文表格表現優於英文，這點對 CJK 財報是正向訊號。（[PP-StructureV3.en.md](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-StructureV3/PP-StructureV3.en.md)）

## Apple Silicon 相容性：有條件可行

這是硬門檻，結論是**有條件可行**：

- PaddlePaddle 官方已支援 macOS arm64 的 pip 安裝，但明確**只提供 CPU 版本**，不支援 GPU 加速；x86_64 已停止支援。（[PaddlePaddle macOS pip 安裝文件](https://www.paddlepaddle.org.cn/documentation/docs/en/install/pip/macos-pip_en.html)）
- 有近期回報 paddlepaddle 3.3.1 在 macOS 26（Sequoia 之後版本）因版本號解析錯誤而無法匯入，需降版至 2.5.2 暫時繞過。（[GitHub Issue #78542](https://github.com/PaddlePaddle/Paddle/issues/78542)）[UNVERIFIED：此 issue 是否已在最新版修復，未進一步查證]
- MPS/Metal 加速僅限於較新的 PaddleOCR-VL（vision-language）pipeline，透過 MLX-VLM 框架取得；標準 PP-OCRv5／PP-StructureV3 pipeline **沒有原生 MLX 後端**，仍走 CPU 推論。（[DeepWiki Apple Silicon Optimization](https://deepwiki.com/PaddlePaddle/PaddleOCR/8.4-apple-silicon-optimization)，AI 生成頁面，細節如「M4 官方驗證」等未逐條交叉查證，標 [UNVERIFIED]）
- 官方未提供 Apple Silicon 的 Docker image，需本機虛擬環境安裝。

換言之：可以裝、可以跑，但在 Mac mini M4 上 PP-StructureV3 是純 CPU 推論，MPS 幫不上忙。

## 資源需求

官方 GPU 基準（V100 1.77 秒/頁、A100 1.12 秒/頁）與 CPU 基準（Intel 約 3.74 秒/圖）顯示 CPU 推論比 GPU 慢 2 至 3 倍量級。Apple Silicon 上沒有對應的 PP-StructureV3 官方基準數字，需自行實測；以 CPU-only 路徑推估，單頁財報表格處理落在數秒等級，批次處理財報 PDF 會有明顯延遲。記憶體方面缺乏官方數字，一般建議 8GB 以上，16GB 較穩妥（來源同上 DeepWiki 頁面，未交叉查證，標 [UNVERIFIED]）。

## MCP Server

官方文件頁面（`paddlepaddle.github.io/.../mcp_server.html`）已 301 轉址到 `paddleocr.ai`，新網址回傳 404，實際內容無法直接驗證，架構描述引用自搜尋摘要：paddleocr-mcp 是基於 FastMCP v2 的輕量伺服器，把 OCR 與 PP-StructureV3 pipeline 註冊為 MCP tool，支援本機模式（直接跑已安裝的 Python 套件）與服務代理模式，可透過 pip 安裝並選擇 `local` 或 `local-cpu` extras。（[GitHub 原始文件](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/deployment/mcp_server.md)，[Glama 列表](https://glama.ai/mcp/servers/PaddlePaddle/PaddleOCR)）tool 級別的完整 input/output schema 未能取得原始文件驗證，標 [UNVERIFIED]。

## 授權與社群

Apache 2.0，GitHub 70k+ star，屬活躍專案。（[GitHub 首頁](https://github.com/PaddlePaddle/PaddleOCR)）

## 與現有組合的定位

EasyOCR 負責一般圖片文字、opendataloader-pdf hybrid mode 負責 PDF 版面與文字抽取。PP-StructureV3 的強項在結構化表格（含合併儲存格與座標），是現有組合缺的一塊，尤其是無邊框財報表格。但它是獨立的重量級框架（PaddlePaddle 整個深度學習框架），不是輕量函式庫，導入成本包含框架相容性風險（見上述 macOS 版本問題）與純 CPU 推論的效能代價。

## 建議：觀察

理由：CJK 表格能力符合痛點，授權與模型都可用；但 Apple Silicon 僅 CPU 推論，且 3.3.1 版在較新 macOS 有回報問題，MCP server 文件目前拿不到穩定連結佐證細節。建議先在小樣本 CJK 財報上實測 CPU 推論速度與表格辨識準確度，若能接受延遲、且版本相容性問題確認已解，再考慮採用；現階段不建議直接整合進生產路徑。
