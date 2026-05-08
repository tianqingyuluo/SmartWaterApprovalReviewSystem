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
* `docs/readable/dev-log/2026-05.md` 中已记录的 PR #5、PR #6、PR #7 合并结果与后续事项。
* 当前真实代码目录：
  * Java：`java-services/water-approval/src/main/java/com/tianqingyuluo/waterapproval/{common,config,controller,dto,entity,mapper,service,storage}`
  * Frontend：`frontend/src/{api,components/{common,business},composables,pages,router,types,utils}`
  * Python Worker：`python-services/smart-water-approval-review-system-py/src/{adapters,models,services}`

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
* 材料类型模型必须预留 `material_type` 扩展能力：MVP 用字符串枚举值保存，未来材料动态化时再迁移到字典表/配置表，后续支持“水资源论证报告”等材料。
* MVP 可暂不实现 Word/Docx 解析，但完整版文件格式必须支持 Word/Docx。
* 文件读取、OCR、PDF/Word 解析失败时允许有界重试；重试耗尽后必须映射为 `PARTIAL_SUCCESS` 或 `FAILED`，不能丢失任务状态。
* `.claude/`、`.codex/`、`.opencode/` 等本机 AI 客户端目录不作为团队共享状态追踪，成员按自己的操作系统和客户端自行生成。
* Trellis 命令示例需要说明 Windows 可用 `python` 替代 Linux/macOS 常见的 `python3`。
* 启动上下文必须自动注入短任务分支纪律，提醒成员不要直接在 `main` 或 `mvp/smartwater` 上实现。
* 项目必须维护面向人阅读的文档树 `docs/readable/**`，其中模块文档统一放在 `docs/readable/modules/<module>/`。
* 任务完成/finish 阶段必须注入文档维护检查，让 AI 主动更新项目开发日志和相关项目文档，或明确说明无需更新。
* `docs/readable/**` 下团队维护的项目文档必须使用中文，技术标识符、命令、API 路径、枚举值、文件路径和引用原文除外。
* 将 backend/frontend index 中仍为模板或 `Partial` 的条目，按当前已落地实现重新分类为 `Active`、`Partial` 或保留占位，并写明原因。
* 对已合并的 Java 服务目录、错误模型、数据库边界、日志规则，以及前端双页目录、组件分层、类型与 API 适配方式，补充“实际约定”和“禁止事项”，而不是继续保留示例模板。

## Acceptance Criteria

* [x] 后端 spec 反映 Java 服务的真实目录、API、错误、数据库和日志约定。
* [x] 前端 spec 反映双页演示应用的真实目录、组件、状态和类型约定。
* [x] 增补跨服务任务状态、结果 schema、Worker 边界和 AI adapter 约定。
* [x] 增补对象存储、密钥配置和异步处理注意事项。
* [x] 明确材料类型扩展策略和 Word/Docx 完整版支持要求。
* [x] 后续实现/check 子代理可通过 spec 理解项目约定。
* [x] 明确本地 AI 客户端目录不追踪、由成员自行生成。
* [x] 明确 Windows 环境可使用 `python` 执行 Trellis 脚本。
* [x] 在共享 session context 与 before-dev 流程中注入短任务分支纪律。
* [x] 增补 `docs/readable/**` 项目文档组织和 finish 阶段文档维护规范。
* [x] 明确 `docs/readable/**` 项目文档维护语言为中文。
* [x] `docs/readable/dev-log/2026-05.md` 补记本次规范固化的完成结论，或明确无需补记的理由。

## Hardening Notes

* 先前已固化跨服务契约、AI adapter、材料扩展、文件处理和前端可见性边界。
* 随着 Java MVP、Worker MVP、法规知识包和前端 PR #7 均已落地并合并，Java 目录/API/错误/数据库/日志与前端目录/组件/API 适配现在应继续实化，不再继续停留在模板状态。
* 如某部分仍无法实化，必须写出“为什么现在不能定”为项目规范，而不是简单保留模板。
* 新增 spec 已接入 backend/frontend index 的 Pre-Development Checklist，后续 before-dev 可自动提示读取。

## Dependencies

* Depends on MVP 核心实现或契约趋于稳定。
* Reads outputs from all other MVP child tasks.

## Definition of Done

* `.trellis/spec/` 不再只是模板，包含 SmartWater 项目真实可执行约定。
* 后续任务可通过 `trellis-before-dev` 和 context 注入自动获得关键规范。
* 没有把尚未决策的事项写成强制规范。
* `smartwater-project-spec-hardening-mvp` 可从 `planning` 进入执行并在本轮完成收尾，不再因为“等待前端/后端稳定”而挂起。
