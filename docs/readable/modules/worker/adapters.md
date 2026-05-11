# Worker 适配器

## 概述

Python Worker 的 `src/adapters/` 用来隔离外部 OCR 和审核模型的供应商差异，`services/` 层不直接拼接供应商请求体。

当前有两个核心适配器：

- `ocr_adapter.py`：负责材料 OCR 和字段抽取输入转换。
- `review_adapter.py`：负责审核推理、结构化结果校验和模型失败分类。

## OCR 适配器

`src/adapters/ocr_adapter.py` 当前使用官方 GLM OCR 版面解析接口：

- `POST {OCR_GLM_BASE_URL}/layout_parsing`
- `model: "glm-ocr"`
- `file`: base64 字符串或 URL

当前映射规则：

- 如果响应包含 `md_results`，优先转换为单个 `ocr_markdown` 字段。
- 如果没有可用的 `md_results`，再从 `layout_details` 转换出一组 `ExtractedField`。
- `jpg`、`jpeg`、`png`、`pdf` 以外的扩展名直接返回空结果。
- 请求或响应异常返回 `ocr_error` 字段，避免 Worker 主流程崩溃。

这个适配器不再走 `chat/completions`，也不再使用 `glm-4v` 作为 OCR 模型。

## 审核适配器

审核推理适配器仍位于 `review_adapter.py`。它与 OCR 适配器分离，避免 OCR 接口格式和审核模型接口格式互相污染。
