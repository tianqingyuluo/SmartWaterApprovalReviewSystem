# CP3-F 审核员初审动作与申请人结果回显

## Scope

在 AI 初评结果之后补齐人工初审处理后端能力：审批人员基于 AI 初评报告执行基础审核动作并填写备注；申请人查询接口能够看到处理结果。该任务提供 CP3 真实闭环所需的状态、接口、日志和结果契约；前端待办、按钮和页面展示由 `v1-cp3-frontend-review-workbench` 接入。

## Deliverables

- Java 后端新增初审处理模型、接口和操作日志。
- 支持三类 CP3 初审动作：
  - `APPROVE_INITIAL_REVIEW`：通过初审。
  - `RETURN_FOR_CORRECTION`：退回补正。
  - `TRANSFER_MANUAL_REVIEW`：转人工复核。
- 审批人员备注、操作者、操作时间、任务状态变更可追溯。
- 申请人结果接口返回审核员处理结果、备注和当前状态，供前端申请人侧展示。
- 审批人员动作 API 返回稳定 DTO，供前端审批详情页接入。

## Non-Goals

- 不做补正材料重新上传闭环。
- 不做材料版本记录和新旧差异对比。
- 不做正式办结、行政许可最终决定或复杂多级审批流。
- 不做 Word 报告导出。
- 不实现前端待办、动作按钮或结果展示页面；这些由 CP3-C 负责。

## Acceptance Criteria

- 审批人员只能对有权限的任务执行动作。
- AI 初审完成后，审批人员可基于 AI 报告和材料信息提交三类动作之一。
- 每次动作生成操作日志，重复提交有明确限制或幂等策略。
- 申请人能看到“通过初审 / 退回补正 / 转人工复核”和审批人员备注。
- `RETURN_FOR_CORRECTION` 只产生补正要求和状态，不在 CP3 内要求完成重传。
- Java 测试覆盖动作提交、权限校验、申请人回显契约和状态转换。
- API 契约足够支撑 CP3-C 前端完成待办、三类动作和申请人结果展示。

## Dependencies

- `v1-cp3-minimal-rbac-task-visibility`
- `v1-cp3-python-fastapi-rules-agent`
- 已归档：`v1-cp3-java-ai-task-callback-results`

## CP4 Boundary

CP4 在本任务基础上实现补正重传、材料版本、差异对比、导出报告和更完整的角色工作台。本任务只负责 CP3 初审处理结果闭环。
