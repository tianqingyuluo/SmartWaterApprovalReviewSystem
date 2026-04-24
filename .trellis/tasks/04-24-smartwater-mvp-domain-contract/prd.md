# MVP 域模型与跨模块契约

## Goal

定义 SmartWater MVP 的统一业务语言、材料类型、任务状态、结果结构和跨模块接口边界，作为后端、Python Worker、前端和知识包任务的共同契约。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* MVP 主线：智能审核辅助，不做完整审批流。
* 第一版材料：`申请书 + 营业执照 + 身份证`。
* 第一版形态：匿名/演示型单次提交，通过任务 ID / 会话 ID 追踪结果。
* 第一版处理：异步 OCR、字段抽取、审核推理，前端轮询状态。

## Scope

### In Scope

* 定义核心实体：提交任务、材料、材料槽位、抽取字段、审核问题、风险提示、审核意见草稿、材料摘要。
* 定义固定材料类型：`APPLICATION_FORM`、`BUSINESS_LICENSE`、`ID_CARD`。
* 定义任务状态：提交成功、等待处理、处理中、部分成功、处理成功、处理失败。
* 定义前端可见结果分层：申请人基础提示 vs 审批人员完整结果。
* 定义 Java 后端与 Python Worker 的输入输出 DTO 或 JSON schema 草案。
* 定义跨任务依赖顺序和可并行开发边界。

### Out of Scope

* 不实现 Java API、Python Worker 或前端页面。
* 不选择数据库、对象存储或推理模型供应商。
* 不定义 V1/V2 完整审批流状态机。

## Inputs

* 父任务 PRD 中的 MVP 范围、模块边界和跨模块流。
* `docs/参考资料/` 中的申请书、填报说明、办理流程和证照样例。
* 现有 Java/Python 服务骨架。

## Outputs

* MVP 领域模型说明文档：`info.md`。
* 跨服务任务状态和结果结构草案：`info.md`。
* 前后端 API 数据结构草案：`info.md`。
* Worker 调用/回写契约草案：`info.md`。
* 对后续子任务的上下游依赖说明：`info.md`。

## Requirements

* 材料槽位必须固定，不支持自由上传自动分类。
* 每个材料槽位最多一个文件。
* 缺失材料允许提交，结果中必须明确缺失项。
* 同一提交不支持多轮补传和版本管理。
* 审核结果必须标记为 AI 辅助建议，不能表达为最终审批结论。
* 申请人结果不能暴露审批侧详细推理、结论草稿或完整风险分析。
* 契约必须支持 OCR 失败、推理失败、部分材料成功等部分失败状态。

## Acceptance Criteria

* [x] 明确 MVP 核心实体和字段含义。
* [x] 明确材料类型枚举、文件格式约束和单文件槽位约束。
* [x] 明确任务状态枚举及状态流转。
* [x] 明确申请人可见结果和审批人员可见结果的差异。
* [x] 明确 Java 后端、Python Worker、前端、知识包之间的边界。
* [x] 明确至少一版 JSON DTO/schema 草案，供实现子任务引用。
* [x] 明确哪些契约应在实现稳定后进入 `.trellis/spec/`。

## Design Artifact

* `info.md` — DDD 领域模型、固定材料槽位、状态机、结果投影、前后端 API 草案、Worker 输入/回写契约和下游任务实施边界。

## Dependencies

* Blocks `smartwater-backend-submission-storage-mvp` for API/entity naming.
* Blocks `smartwater-python-ocr-review-worker-mvp` for Worker input/output schema.
* Blocks `smartwater-frontend-dual-page-mvp` for UI status and result shape.
* Feeds `smartwater-project-spec-hardening-mvp` for spec hardening.

## Definition of Done

* 子任务 PRD 和契约文档足够让后端、Worker、前端并行开发。
* 父任务 PRD 中的模块边界未被突破。
* 所有未决问题明确转入后续任务或研究文件。
