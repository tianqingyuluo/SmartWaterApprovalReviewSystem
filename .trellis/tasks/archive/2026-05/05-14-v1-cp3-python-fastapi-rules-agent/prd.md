# CP3-B Python FastAPI、解析、规则与 Agent

## Scope
实现 FastAPI 审查任务主线，打通解析、规则、RAG 与 Agent 汇总。

## Deliverables
- FastAPI 创建任务与后台执行链路
- 多格式文件解析/OCR/抽取流程
- 规则检查与 Agent 汇总并回调 Java

## Dependencies
- `v1-cp2-python-ingest-chromadb-embedding`
- `v1-cp2-mcp-server-tools`
- `v1-cp3-java-ai-task-callback-results`

## Acceptance Criteria
- 主样例与负向样例可处理
- Agent 失败可降级为规则结果+人工复核
- 多次运行结构化结论稳定

## Wave Gate Notes
- Checkpoint: `CP3`
- Lane: `python`
- Wave: `3`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP2 + CP3-A contracts completed and parent approves Wave 3.
