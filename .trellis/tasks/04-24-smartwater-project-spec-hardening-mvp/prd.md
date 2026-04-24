# 项目规范固化 MVP

## Goal

在 MVP 关键设计和实现稳定后，把 SmartWater 的后端、前端、AI Worker、跨服务契约和质量约定沉淀进 `.trellis/spec/`，减少团队后续并行开发时的上下文漂移。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* 当前 `.trellis/spec/backend/` 与 `.trellis/spec/frontend/` 仍偏模板化，需要随着项目实现补充真实约定。
* 本任务是规范固化，不直接实现业务功能。

## Scope

### In Scope

* 更新后端目录、API、错误模型、数据库和日志约定。
* 更新前端目录、组件、状态管理、类型安全和质量约定。
* 新增或更新跨服务契约说明，例如任务状态、DTO/schema、Worker 回写、AI adapter 边界。
* 记录密钥配置、供应商 adapter、对象存储和异步任务的项目级约定。
* 把已验证的经验加入 thinking guides 或相关 spec。

### Out of Scope

* 不创建业务功能。
* 不替代各实现子任务的 PRD、测试或验收。
* 不在尚未验证的实现细节上过早制定僵化规范。

## Inputs

* 父任务 PRD。
* 各 MVP 子任务的最终 PRD、实现和质量检查结果。
* `.trellis/spec/backend/`、`.trellis/spec/frontend/`、`.trellis/spec/guides/` 现有内容。

## Outputs

* 更新后的 `.trellis/spec/backend/` 文档。
* 更新后的 `.trellis/spec/frontend/` 文档。
* 跨服务/AI Worker 契约规范文档。
* 必要的 thinking guide 补充。

## Requirements

* 只固化已确认或已实现的约定，不凭空编造团队规范。
* 每条规范应能指导后续子任务实施或检查。
* 规范要覆盖 AI/OCR adapter 的密钥、安全和可替换边界。
* 规范要覆盖前端申请人/审批人员结果可见性差异。

## Acceptance Criteria

* [ ] 后端 spec 反映 Java 服务的真实目录、API、错误、数据库和日志约定。
* [ ] 前端 spec 反映双页演示应用的真实目录、组件、状态和类型约定。
* [ ] 增补跨服务任务状态、结果 schema、Worker 边界和 AI adapter 约定。
* [ ] 增补对象存储、密钥配置和异步处理注意事项。
* [ ] 后续实现/check 子代理可通过 spec 理解项目约定。

## Dependencies

* Depends on MVP 核心实现或契约趋于稳定。
* Reads outputs from all other MVP child tasks.

## Definition of Done

* `.trellis/spec/` 不再只是模板，包含 SmartWater 项目真实可执行约定。
* 后续任务可通过 `trellis-before-dev` 和 context 注入自动获得关键规范。
* 没有把尚未决策的事项写成强制规范。
