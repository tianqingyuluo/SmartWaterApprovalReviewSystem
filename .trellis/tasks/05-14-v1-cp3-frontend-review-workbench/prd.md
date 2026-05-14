# CP3-C 前端 AI 结果、待办和审核动作

## Scope
交付审批人员待办、AI 结果展示和三类审核动作页面。

## Deliverables
- 审批待办列表与详情页
- AI 结论/问题/依据/字段展示
- 通过初审/退回补正/转人工复核动作与日志视图

## Dependencies
- `v1-cp3-java-ai-task-callback-results`
- `v1-cp3-python-fastapi-rules-agent`

## Acceptance Criteria
- 审批人员可完整执行三类动作
- AI 结论明确标注为辅助建议
- 页面展示结构化问题关键字段

## Wave Gate Notes
- Checkpoint: `CP3`
- Lane: `frontend`
- Wave: `3`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP3 backend + python review chain completed and parent approves Wave 3.
