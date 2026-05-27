# CP4-A Java 报告导出与管理能力收口

## Scope
完成 Java 报告导出与用户管理 API 收口，支撑最终答辩闭环。

## Deliverables
- poi-tl 报告模板渲染链路
- 固定模板资源与导出 API
- 用户管理 API 与角色管理收口

## Dependencies
- `v1-cp3-java-ai-task-callback-results`
- `v1-cp3-python-fastapi-rules-agent`
- `v1-cp3-frontend-review-workbench`
- `v1-cp3-integration-stability-tests`

## Acceptance Criteria
- 可导出包含规定字段的 .docx 报告
- 导出不触发二次 AI 调用
- 管理员能力满足 CP4 演示要求

## Wave Gate Notes
- Checkpoint: `CP4`
- Lane: `java`
- Wave: `4`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP3 acceptance completed and parent approves Wave 4 Java closure.
