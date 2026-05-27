# CP3-D 集成测试与稳定性验收

## Scope
形成 Java-Python 全链路测试与稳定性验收证据。

## Deliverables
- 端到端联调测试用例与结果
- 结构化结果稳定性复跑记录
- 回调失败与查询兜底验证记录

## Dependencies
- `v1-cp3-java-ai-task-callback-results`
- `v1-cp3-python-fastapi-rules-agent`
- `v1-cp3-frontend-review-workbench`

## Acceptance Criteria
- 提交材料可触发并回写 AI 结果
- 重复运行关键结构化字段一致
- 异常场景有可解释状态和记录

## Wave Gate Notes
- Checkpoint: `CP3`
- Lane: `docs-tests`
- Wave: `3`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP3 core chain delivered and parent approves Wave 3 acceptance.
