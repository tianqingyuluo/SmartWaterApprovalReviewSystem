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

* 必须使用 `trellis-research` 子代理产出 `research/inference-vendor-comparison.md`。
* PRD 和实现任务只能引用调研文件中的结论，不把临时对话作为依据。

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

## Acceptance Criteria

* [ ] `research/inference-vendor-comparison.md` 已创建并包含供应商比较。
* [ ] 明确推荐模型和至少一个备选模型。
* [ ] 明确选择依据与放弃其他方案的原因。
* [ ] 明确推理 adapter 输入输出 schema。
* [ ] 明确提示词组织原则、结构化输出要求和失败处理。
* [ ] 明确密钥配置、限流/重试和成本风险。

## Dependencies

* Blocks `smartwater-python-ocr-review-worker-mvp` for actual inference adapter implementation.
* Feeds `smartwater-project-spec-hardening-mvp` for AI adapter conventions.

## Definition of Done

* 团队可以基于该任务结论接入一个真实推理供应商。
* Python Worker 不需要重新讨论模型选型即可实现 adapter。
* 风险、成本和替换路径被记录在研究文件和 PRD 中。
