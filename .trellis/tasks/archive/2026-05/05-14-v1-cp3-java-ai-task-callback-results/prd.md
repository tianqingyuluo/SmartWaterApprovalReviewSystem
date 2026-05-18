# CP3-A Java AI 任务、回调与结果持久化

## Scope
建立 Java 侧 AI 任务模型、回调入口与结果持久化主链路。

## Deliverables
- AI 任务与结果相关数据表设计
- Python 创建任务客户端
- 回调接口幂等处理与结果查询 API

## Dependencies
- 无

## Acceptance Criteria
- Java 可创建 AI 审查任务并持久化状态
- 重复回调不产生重复结果
- 前端可查询结论/问题/字段快照

## Wave Gate Notes
- Checkpoint: `CP3`
- Lane: `java`
- Wave: `1`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: Wave 1 baseline task for CP3 async integration.
