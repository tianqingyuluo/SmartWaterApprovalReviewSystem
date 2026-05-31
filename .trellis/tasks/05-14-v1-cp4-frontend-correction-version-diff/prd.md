# CP4-C 前端角色工作台、补正和版本差异收口

## Scope
完成三角色工作台、全栈补正闭环与版本差异视图，并接入报告导出入口。

本任务承接 CP3-F 已完成的“退回补正状态 + 审批备注回显”。CP3-F 不做补正材料重新上传、材料版本和差异对比；这些能力统一在 CP4-C 收口。

## Deliverables
- 申请人/审批人员/管理员工作台
- 申请人结果页在 `CORRECTION_REQUIRED` 时显示“修改补正材料/重新提交”入口
- 补正上传闭环页面，支持申请人补传被要求补正的材料
- Java 后端补正上传接口，限制仅 `CORRECTION_REQUIRED` 任务可补传
- Java 保存新材料版本，不覆盖旧版本，并记录补正提交时间、提交人和关联任务
- 补传后任务重新进入待审/处理中，并重新调度 Python FastAPI 审查链路
- 材料/字段/问题版本差异与报告导出入口
- 审批人员详情页展示补正前后材料、字段和问题差异

## Dependencies
- `v1-cp3-frontend-review-workbench`
- `v1-cp4-java-report-export-admin`
- `v1-cp3-reviewer-actions-applicant-result`

## Acceptance Criteria
- 申请人可查看补正意见并补传材料
- 补传后旧材料版本仍可追溯，新材料版本成为当前审查输入
- 补传后 Java 能重新调度 Python 审查，并回写新的 AI 审查结果
- 审批人员可查看新旧版本差异
- 管理员可完成用户与角色管理
- 非 `CORRECTION_REQUIRED` 状态下不得补传补正材料
- 普通申请人只能补传自己的任务材料

## Wave Gate Notes
- Checkpoint: `CP4`
- Lane: `frontend`
- Wave: `4`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP3 frontend chain and CP4-A export API completed; parent approves Wave 4.
