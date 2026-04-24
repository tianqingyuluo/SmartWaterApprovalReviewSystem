# 后端提交与存储 MVP

## Goal

在 Java 后端实现 SmartWater MVP 的材料提交、任务状态、结果查询、数据库记录和对象存储边界，为前端双页演示和 Python Worker 提供稳定业务入口。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* Java 服务位置：`java-services/water-approval/`
* MVP 采用真实数据库与对象存储，不使用本地文件系统作为主存储方案。
* OCR 与审核推理由 Python Worker 负责，Java 后端不直接承担模型调用。

## Scope

### In Scope

* 提供材料提交 API，支持固定槽位上传 `申请书 + 营业执照 + 身份证`。
* 校验文件格式：`jpg/jpeg/png/pdf`。
* 创建任务 ID / 会话 ID，并保存任务、材料元数据和对象存储引用。
* 提供任务状态查询和结果查询 API，支持前端轮询。
* 定义与 Python Worker 的任务派发、拉取或回写边界。
* 存储 OCR/抽取/审核结果、失败原因和部分成功状态。

### Out of Scope

* 不实现 OCR、字段抽取和推理模型调用。
* 不实现账号、权限、提交列表、待办和审批流动作。
* 不实现审核结果导出。
* 不实现多轮补传、版本管理或单材料多文件上传。

## Inputs

* `smartwater-mvp-domain-contract` 输出的领域模型和 DTO/schema。
* 父任务 PRD 的 MVP 范围与跨模块流。
* 数据库和对象存储选型约束。

## Outputs

* Java 后端提交 API。
* Java 后端任务状态与结果查询 API。
* 数据库表/实体/迁移设计。
* 对象存储抽象与配置。
* Python Worker 集成边界。

## Requirements

* 后端必须为每次提交生成不可猜测或足够安全的任务访问标识。
* 缺失材料时仍创建任务，并在结果中保留缺失材料提示。
* 任务状态必须能表达等待、处理中、成功、部分失败和失败。
* 文件内容不得落入 Git；密钥必须通过环境变量或部署密钥注入。
* API 错误响应应保持一致，便于前端展示失败状态。
* 结果查询必须区分申请人基础结果和审批人员完整结果，或为前端提供清晰字段分层。

## Acceptance Criteria

* [ ] 可提交一个包含 0–3 个固定材料槽位文件的任务。
* [ ] 文件格式校验和错误返回明确。
* [ ] 任务、材料元数据和对象存储引用可持久化。
* [ ] 前端可通过任务 ID / 会话 ID 轮询任务状态。
* [ ] Python Worker 可读取任务输入并回写结构化结果。
* [ ] 可保存并查询缺失材料、抽取字段、问题清单、风险提示、审核意见草稿和材料摘要。
* [ ] 不引入账号、待办、审批流或导出能力。

## Dependencies

* Depends on `smartwater-mvp-domain-contract` for entity and API schema.
* Coordinates with `smartwater-python-ocr-review-worker-mvp` for Worker integration.
* Feeds `smartwater-frontend-dual-page-mvp` with API contract.
* Feeds `smartwater-project-spec-hardening-mvp` with backend conventions.

## Definition of Done

* 后端 MVP 能支撑端到端提交、异步处理状态和结果查询。
* 存储边界可替换，不把对象存储或模型密钥硬编码进代码。
* 相关 API 和状态契约可被前端、Worker 和规范固化任务引用。
