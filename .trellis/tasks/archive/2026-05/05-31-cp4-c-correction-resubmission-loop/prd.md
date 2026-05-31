# 实现申请人补正材料补传闭环

## Goal

当审批人员对任务执行 `RETURN_FOR_CORRECTION` 后，申请人应能在结果页看到补正意见并补传材料。补传后 Java 后端更新当前材料输入、重新进入 AI 审查流程，并再次调度 Python FastAPI 生成新的审查结果。

## What I Already Know

- CP3-F 已完成退回补正状态和审批备注回显，但明确不做补正材料重新上传闭环。
- CP4-C 已扩展为全栈补正闭环，要求申请人补传、Java 保存新材料版本/输入、重新调度 Python、审批人员看差异。
- 当前数据模型 `material_slot (task_id, material_type)` 是唯一当前槽位记录，不支持历史版本表。
- 当前 Java 提交链路已经能保存材料到 RustFS/MySQL，并主动调度 Python FastAPI。
- 当前前端结果页申请人视图能显示 `handlingStatus=CORRECTION_REQUIRED` 与 `reviewerRemark`，但没有补传入口。

## Requirements

- 新增申请人补传接口，允许 `CORRECTION_REQUIRED` 任务的 owner 上传一个或多个固定槽位材料。
- 后端必须拒绝非 owner 申请人、未登录用户、非 `CORRECTION_REQUIRED` 状态、无上传文件、非法文件类型。
- 补传材料覆盖当前槽位输入，不暴露对象存储 key 给前端；旧对象可保留在对象存储中但不作为当前审查输入。
- 补传成功后清除初审处理快照和旧结果，任务重新进入 `PROCESSING`，并重新调度 Python FastAPI。
- 如果 Python 调度失败，任务进入 `FAILED` 并写入可查询的失败结果，复用现有失败语义。
- 前端申请人结果页在 `CORRECTION_REQUIRED` 时显示补传表单，只允许上传三类固定材料。
- 补传成功后前端展示成功状态并刷新结果。

## Acceptance Criteria

- [ ] 申请人能在退回补正结果页补传材料。
- [ ] 非 `CORRECTION_REQUIRED` 任务不能补传。
- [ ] 申请人不能补传他人的任务材料。
- [ ] 补传后 Java 使用新的材料槽位重新调度 Python FastAPI。
- [ ] 补传后旧审查结果不继续作为当前结果展示。
- [ ] 前端补传入口仅在申请人视图且退回补正状态展示。
- [ ] Java 后端相关测试通过。
- [ ] 前端类型/适配器或页面相关测试通过。

## Definition of Done

- Java 单测覆盖权限、状态限制、补传后重新调度和失败路径。
- 前端测试覆盖补传 API/FormData 或页面分支。
- 文档或 spec 更新补正闭环的最新边界。
- 能说明真实依赖：MySQL、RustFS、Java -> Python FastAPI。

## Out of Scope

- 不新增完整历史材料版本表。
- 不实现新旧材料/字段/问题差异视图。
- 不实现 Word 报告导出。
- 不实现完整用户管理。
- 不让浏览器直接访问 RustFS 或 Python。

## Technical Notes

- 生产路径依赖 MySQL `review_task/material_slot/review_result/review_action_log`、RustFS/S3 `StorageService`、Java `AiServiceClient` 调度 Python。
- 当前最小闭环可复用 `ReviewTaskServiceImpl.submit` 的材料校验、存储和调度逻辑，但需要避免复制出漂移的规则。
- 单元测试应 mock `StorageService` 和 `AiServiceClient`，真实集成验证另行通过本地服务完成。
