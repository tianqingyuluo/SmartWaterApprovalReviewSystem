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

## 规则、RAG 与 Agent 编排

CP3-B 新增 `ReviewTaskOrchestrator`，轮询 Worker 和 FastAPI 后台任务都通过它执行同一条 AI 初评链路：

1. 根据材料槽位执行下载、解析、OCR 和字段抽取。
2. 使用静态知识包进行材料完整性规则检查。
3. 调用知识检索工具组装可引用的 RAG 片段。
4. 调用审核推理适配器生成结构化初评结果。
5. 将规则问题和 Agent 问题合并后写回 Java。

当 Agent 或 LLM 不可用、输出格式异常或返回失败分类时，orchestrator 不丢弃规则检查结果，而是生成 `PARTIAL_SUCCESS`，加入审批人员可见的 `MODEL_UNCERTAIN` 问题、人工复核提示和规则结论。申请人结果仍只包含申请人可见问题，不包含字段快照、模型失败细节或审批人员草拟意见。
