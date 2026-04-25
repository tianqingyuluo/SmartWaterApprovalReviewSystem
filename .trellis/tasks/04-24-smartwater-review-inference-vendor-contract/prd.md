# 审核推理模型选型与适配契约

## Goal

选择一个国内可稳定访问、适合中文法规与公文理解的审核推理模型供应商，并定义 SmartWater 审核推理 adapter、提示输入、结构化输出和失败处理契约。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* OCR 已定为 GLM OCR，但审核推理不能使用 GLM OCR 所属模型能力。
* 推理模型第一优先级是中文法规与公文理解能力，其次是成本、上下文长度、国内可用性和 API 兼容性。

## Scope

### In Scope

* 调研 2–4 个国内可实际接入的推理模型供应商。
* 比较中文法规/公文理解、长上下文、结构化输出、稳定性、成本、API 兼容性、密钥与部署约束。
* 给出推荐供应商和备选方案。
* 定义 `ReviewAssistant` / `Review reasoning adapter` 输入输出契约。
* 定义审核结果 JSON schema：问题清单、意见草稿、风险提示、材料摘要、引用依据、人工复核提示。
* 定义提示词组织原则和输出约束，避免不可解释最终裁决。

### Out of Scope

* 不实现完整 Python Worker。
* 不选择 OCR 供应商。
* 不做模型微调或本地私有化部署。
* 不承诺 AI 输出可替代人工审批。

## Research Requirement

* [x] 已使用 `trellis-research` 子代理产出 `research/inference-vendor-comparison.md`。
* PRD 和实现任务只能引用调研文件中的结论，不把临时对话作为依据。

## Research References

* [`research/inference-vendor-comparison.md`](research/inference-vendor-comparison.md) — 推荐百度千帆 `ERNIE-4.5-Turbo-128K` 作为主推理供应商，阿里云百炼 DashScope/Qwen 作为备选与长上下文兜底。

## Decision

### Primary Vendor

**拍板选择：百度千帆 / ERNIE-4.5-Turbo-128K。**

选择理由：

* 国内可稳定接入，提供 OpenAI-compatible API，Python Worker 初始集成成本低。
* 官方支持 `response_format` 的 `json_schema` 严格结构化输出，更适合审批审核结果的 schema 约束。
* 128K 上下文足够 MVP 处理 `申请书 + 营业执照 + 身份证` 的 OCR 摘要、字段抽取结果和法规知识片段。
* 成本与默认流控对 MVP 演示和早期联调友好。
* 与已定的 GLM OCR 保持供应商解耦，避免 OCR 与审核推理同时绑定智谱。

### Fallback Vendor

**备选：阿里云百炼 DashScope / Qwen。**

使用场景：

* 千帆账号、配额、稳定性或结构化输出实测不满足时切换。
* 后续需要更长上下文或更丰富 Qwen 模型矩阵时切换。
* 通过相同 `ReviewReasoningAdapter` 契约替换，不影响 Java 后端、前端和知识包边界。

### Deferred Options

* Kimi：长上下文能力强，但调研中未看到同等明确的 `json_schema` strict 输出依据，且充值/限流与 thinking/tool 约束会增加 Worker 复杂度。
* 腾讯混元：OpenAI 兼容与工具调用可用，但 strict schema 证据较弱，默认共享并发对 MVP 吞吐存在约束。
* 智谱 GLM：能力可用，但 OCR 已定 GLM OCR，审核推理继续选 GLM 会增加供应商耦合。
* DeepSeek：接口兼容、成本低，适合作后续 benchmark；但公开错误与拥塞场景对第一版政务审核辅助不够稳妥。

## Inputs

* 父任务 PRD 的推理模型选择优先级。
* `smartwater-regulation-knowledge-pack-mvp` 的知识输入形态。
* `smartwater-python-ocr-review-worker-mvp` 的 adapter 需求。

## Outputs

* 推理模型供应商推荐和备选。
* `Review reasoning adapter` 契约。
* 审核推理请求/响应 JSON schema。
* 提示词约束和安全边界。
* 密钥、限流、重试和错误分类建议。

## Requirements

* 供应商必须国内可稳定访问，并可用于实际 API 接入。
* 输出必须支持结构化 JSON，或可通过可靠方式约束为结构化结果。
* 输出必须包含依据引用和人工复核提示。
* 输出不得宣称最终审批决定，只能作为辅助建议。
* 契约必须允许后续替换供应商。

## Review Reasoning Adapter Contract

### Provider Configuration

Python Worker 使用供应商无关配置面：

* `REVIEW_LLM_PROVIDER`: `qianfan`、`dashscope` 等供应商标识。
* `REVIEW_LLM_MODEL`: 默认 `ernie-4.5-turbo-128k`。
* `REVIEW_LLM_BASE_URL`: OpenAI-compatible endpoint。
* `REVIEW_LLM_API_KEY`: 供应商 API key。
* `REVIEW_LLM_APP_ID`: 可选，仅千帆需要时使用。

### Request Schema

`ReviewReasoningRequest` 包含：

* `submissionId`: 本次提交 ID。
* `sessionId`: 申请人/审批人员用于查询的会话 ID。
* `materialSlots`: 固定材料槽位，第一版仅 `WATER_INTAKE_APPLICATION`、`BUSINESS_LICENSE`、`IDENTITY_DOCUMENT`。
* `extractedFields`: OCR/抽取得到的字段键值、置信度和来源材料。
* `missingMaterials`: 缺失材料类型列表。
* `knowledgeFragments`: 法规依据、材料清单、字段规则和提示词片段，每条必须有 `sourceId` / `sourceTitle`。
* `reviewMode`: 第一版固定 `ASSISTIVE_REVIEW`，表示只生成辅助审核建议。
* `outputLanguage`: 第一版固定 `zh-CN`。

### Response Schema

`ReviewReasoningResult` 必须是可本地校验的 JSON，至少包含：

* `summary`: 材料与审核摘要，不超过审批人员结果页可读长度。
* `issues`: 问题清单；每项包含 `code`、`severity`、`message`、`materialType`、`fieldKey`、`basisRefs`、`applicantVisible`。
* `riskHints`: 风险提示；每项包含 `riskLevel`、`description`、`basisRefs`、`requiresManualReview`。
* `draftOpinion`: 审核意见草稿，只能使用辅助建议语气。
* `materialCompleteness`: 材料完整性结果，包含缺失、已收到、无法识别三类。
* `basisRefs`: 被引用依据列表，必须来自输入的 `knowledgeFragments`。
* `manualReviewNotice`: 人工复核提示，明确 AI 不作最终审批决定。
* `modelMetadata`: `provider`、`model`、`requestId`、`finishReason`、`tokenUsage`。

### Prompt and Output Constraints

* 系统提示必须声明：模型是“取水许可材料审核辅助工具”，不得输出最终准予/不准予审批决定。
* 提示输入优先使用结构化 OCR 摘要和知识片段，不直接堆叠全量 OCR 原文。
* 输出必须走供应商结构化输出能力；写回前仍需本地 JSON schema 校验。
* 如果一次输出不是合法 JSON，可执行一次修复提示；仍失败则返回 `SCHEMA_MISMATCH`。
* `basisRefs` 只能引用输入知识片段，不允许模型自造法规名称、条款编号或来源。

### Failure Handling

* 可重试：`TIMEOUT`、`RATE_LIMIT`、`UPSTREAM_5XX`。
* 不重试：`AUTH_ERROR`、`CONTENT_FILTERED`、一次修复后仍失败的 `INVALID_JSON` / `SCHEMA_MISMATCH`、`UNSUPPORTED_CAPABILITY`。
* 重试使用有上限的指数退避，日志记录 provider、model、requestId、token usage、finish reason、retry count 和脱敏输入摘要。
* 禁止日志记录身份证号、营业执照完整识别文本、完整 OCR 原文或完整提示词。

## Acceptance Criteria

* [x] `research/inference-vendor-comparison.md` 已创建并包含供应商比较。
* [x] 明确推荐模型和至少一个备选模型。
* [x] 明确选择依据与放弃其他方案的原因。
* [x] 明确推理 adapter 输入输出 schema。
* [x] 明确提示词组织原则、结构化输出要求和失败处理。
* [x] 明确密钥配置、限流/重试和成本风险。

## Dependencies

* Blocks `smartwater-python-ocr-review-worker-mvp` for actual inference adapter implementation.
* Feeds `smartwater-project-spec-hardening-mvp` for AI adapter conventions.

## Definition of Done

* 团队可以基于该任务结论接入一个真实推理供应商。
* Python Worker 不需要重新讨论模型选型即可实现 adapter。
* 风险、成本和替换路径被记录在研究文件和 PRD 中。
