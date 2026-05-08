# Python OCR 与智能审核 Worker MVP

## Goal

在 Python 服务中实现 SmartWater MVP 的异步材料处理 Worker：调用 GLM OCR 识别材料，抽取结构化字段，调用独立审核推理模型生成 AI 辅助审核结果，并回写 Java 后端。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* Python 服务位置：`python-services/smart-water-approval-review-system-py/`
* OCR 供应商已定为 GLM OCR。
* 审核推理服务与 OCR 解耦，模型供应商由 `smartwater-review-inference-vendor-contract` 任务确定。

## Scope

### In Scope

* 实现或设计 `OCR adapter`，首个实现面向 GLM OCR。
* 实现申请书、营业执照、身份证的字段抽取和结构化归一。
* 基于法规知识包、抽取字段和材料文本组织审核推理输入。
* 实现 `Review reasoning adapter` 边界，接入由模型选型任务确定的供应商。
* 输出材料缺失、字段问题、一致性问题、风险提示、审核意见草稿、材料摘要和人工复核提示。
* 支持部分失败：单材料 OCR 失败或推理失败时回写可解释失败信息。

### Out of Scope

* 不负责 Java 业务 API、数据库表结构和对象存储策略。
* 不负责前端展示。
* 不提供法规知识维护后台。
* 不把 GLM OCR 用作审核推理模型。

## Inputs

* Java 后端提供的任务 ID、材料对象存储引用和材料类型。
* `smartwater-mvp-domain-contract` 输出的 Worker DTO/schema。
* `smartwater-regulation-knowledge-pack-mvp` 输出的材料清单、规则和提示词片段。
* `smartwater-review-inference-vendor-contract` 输出的推理模型供应商和适配契约。

## Outputs

* GLM OCR 适配层。
* 字段抽取和归一化结果。
* 审核推理请求/响应适配层。
* 结构化审核结果回写。
* 错误分类、失败原因和可重试性标记。

## Requirements

* OCR 与审核推理必须是两个独立 adapter，不能混用职责。
* API 密钥必须通过环境变量或部署密钥注入，不写入 Git。
* 输出必须包含可解释字段，例如依据、命中字段、风险等级或人工复核提示。
* AI 输出必须标记为辅助建议，不给出不可复核的最终审批判定。
* Worker 必须遵循固定材料槽位，不依赖自由分类。
* 缺失材料时仍对已上传材料生成部分结果。

## Acceptance Criteria

* [ ] 定义并实现 GLM OCR adapter 边界。
* [ ] 定义并实现 Review reasoning adapter 边界。
* [ ] 可处理申请书、营业执照、身份证三类材料的首版字段抽取。
* [ ] 可基于静态知识包生成审核问题、风险提示、意见草稿和摘要。
* [ ] 可回写成功、部分失败和失败状态。
* [ ] 不在代码中硬编码密钥。
* [ ] 不把 OCR 模型当作审核推理模型使用。

## Dependencies

* Depends on `smartwater-mvp-domain-contract` for Worker contract.
* Depends on `smartwater-regulation-knowledge-pack-mvp` for knowledge inputs.
* Depends on `smartwater-review-inference-vendor-contract` for inference adapter details.
* Coordinates with `smartwater-backend-submission-storage-mvp` for task pull/push and result writeback.

## Definition of Done

* Python Worker 能作为独立服务边界完成 OCR、抽取、审核推理和回写。
* 失败路径可观测且不会阻塞已成功材料的部分结果。
* 供应商相关细节被隔离在 adapter 内，便于后续替换。
