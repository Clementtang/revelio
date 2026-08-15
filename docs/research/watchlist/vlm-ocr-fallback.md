# 本地 VLM OCR 作為 CID 字型 PDF Fallback 可行性調研

調研日期：2026-08-14
背景：Revelio 目前對 CID 字型（無 ToUnicode 映射）PDF 的 fallback 是 EasyOCR，Mac mini M4 上已佔用約 2.6GB 記憶體，且有辨識瑕疵（例如「二十」誤讀為「二＋」）。本文評估本地 VLM 直接讀渲染頁面能否取代或補強這個 fallback，運行環境限定 Apple Silicon（MPS，無 CUDA）。

## 候選方案比較表

| 方案                                               | 模型大小                                                        | Apple Silicon 支援                                                   | CJK 能力                                | 授權                                                                        |
| -------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------- |
| DeepSeek-OCR 官方版                                | 3B 總參數                                                       | 無，官方僅列 CUDA 11.8+ / torch 2.6.0                                | 提示詞範例含中文，語言清單未在官網明列  | MIT                                                                         |
| deepseek-ocr.rs（TimmyOVO）                        | 依量化：Q4K/Q6K/Q8K，FP16 約需 13GB RAM（含 cache/activations） | 有，官方宣稱針對 Apple Silicon 最佳化，內建 Metal 後端與原生二進位   | 繼承 DeepSeek-OCR 模型能力              | 專案本體 Apache-2.0，模型權重繼承上游 DeepSeek-OCR 授權限制                 |
| Qwen2.5-VL / Qwen2-VL-OCR 系列（含 2B OCR 微調版） | 2B 起（社群微調版），32B 為完整版                               | 有，MLX 框架原生支援，社群有多個 Apple Silicon 移植 repo             | 官方列出中文、日文、韓文、多數歐洲語言  | Apache-2.0（Qwen 系列一般授權）                                             |
| surya v2（datalab-to，GGUF）                       | 0.65B（單一模型跑版面、OCR、表格辨識）                          | 有，官方明確支援 llama.cpp + Metal 後端，並附 Apple Silicon 效能數據 | 官方列出含中文、日文、韓文在內 90+ 語言 | openrail（研究／個人／年營收或募資 500 萬美元以下新創免費，商用需另洽授權） |

## 各方案可行性結論

**DeepSeek-OCR 官方 repo**：官方文件只涵蓋 CUDA 環境，安裝說明未提及 macOS 或 MPS，A100-40G 基準測資（約 2500 tokens/s）也是 GPU 環境下數字，直接在 Mac mini M4 上跑官方版本可行性低，需靠社群移植。（[GitHub](https://github.com/deepseek-ai/DeepSeek-OCR)）

**deepseek-ocr.rs**：這是目前查到對 Apple Silicon 支援最明確的 DeepSeek-OCR 本地化路徑，用 Rust 重寫、免 Python 環境、內建 DSQ 量化（Q4K/Q6K/Q8K）與 Metal FP16 後端，作者定位為「optimised for Apple Silicon」而非實驗性專案，另外還支援 PaddleOCR-VL 與 DotsOCR 兩個備選後端。記憶體門檻方面，DeepSeek-OCR 全精度版本約需 13GB RAM（含 cache 與 activations），量化版本應可再往下壓，但頁面未給出量化後精確數字。需注意授權，本體雖是 Apache-2.0，但模型權重仍繼承上游 DeepSeek-OCR 的限制條款。（[GitHub](https://github.com/TimmyOVO/deepseek-ocr.rs)、[HuggingFace](https://huggingface.co/TimmyOVO/deepseek-ocr.rs)）另有 ttieli/DeepSeek-OCR-macOS 這個社群一鍵工具，號稱「智能適配 Mac 芯片」，可作為快速試用的替代路徑，但未逐一驗證其穩定度。（[GitHub](https://github.com/ttieli/DeepSeek-OCR-macOS)）

**Qwen2.5-VL / Qwen2-VL-OCR**：MLX 生態成熟，官方與社群都有現成的 Apple Silicon 執行路徑，中文（含理論上涵蓋繁體）為官方列出的支援語言之一。有專門針對 OCR 微調的 2B 小尺寸版本（Qwen2-VL-OCR-2B-Instruct），對記憶體有限的 Mac mini 較友善，但這是社群微調模型，準確度沒有官方基準佐證，需要實測驗證。（[GitHub](https://github.com/codingstark-dev/qwen2.5-vl-apple-silicon)、[HuggingFace](https://huggingface.co/prithivMLmods/Qwen2-VL-OCR-2B-Instruct)）

**surya v2**：0.65B 參數是四個方案中最小的，官方直接給出 llama.cpp + Metal 在 Apple Silicon 上的實測數字（約 0.108 頁/秒，8 平行、約 30W 功耗），語言涵蓋 90 種以上並明確包含中日韓，記憶體壓力應遠低於 3B 級的 DeepSeek-OCR。但授權是 openrail 而非完全開源，商用需視營收／募資規模另外授權，Revelio 若走商業化路線需先確認是否落在免費門檻內。（[HuggingFace](https://huggingface.co/datalab-to/surya-ocr-2-gguf)、[GitHub](https://github.com/datalab-to/surya)）

## 對照現有 EasyOCR fallback（繁體中文財報表格場景）

VLM 路線的潛在優勢在於能理解版面語境而非逐字元辨識，對「二十」這類容易被切割誤讀的字元組合，理論上錯誤率會低於傳統 CRNN 架構的 EasyOCR。但財報表格常見的密集數字與跨欄合併儲存格，是否能被 VLM 準確保留結構，目前查到的資料都沒有針對繁體中文財報表格的實測基準，這塊需要自行用 Revelio 的既有測試 PDF 跑一次才有數據。記憶體方面，DeepSeek-OCR 全精度版（約 13GB）明顯高於 EasyOCR 現有的 2.6GB，surya v2（0.65B）與 Qwen2-VL-OCR-2B 這類小尺寸模型較有機會維持在同等級記憶體佔用內。

## 建議

優先試 surya v2 GGUF：參數量最小、官方已給出 Apple Silicon 實測數據、CJK 語言支援明確列出，記憶體壓力預期最低，可先用 Revelio 現有的 CID 字型測試 PDF（含 TSMC 財報範例）跑準確度與記憶體對比。若準確度不足，再試 deepseek-ocr.rs 的 Q4K 或 Q6K 量化版本，這是目前對 Apple Silicon 支援最扎實的 DeepSeek-OCR 路徑，但要先確認授權條款是否符合 Revelio 的散布方式。Qwen2-VL-OCR-2B 可作第三選項，MLX 生態成熟、社群資源多，但準確度基準較弱，建議實測而非直接採信社群宣稱。三者都建議先在小樣本上跑一輪繁體中文財報 PDF 比對 EasyOCR 現有輸出，再決定要不要正式取代或並存。
