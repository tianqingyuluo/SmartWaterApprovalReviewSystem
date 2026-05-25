# CP2-D CP2 文档、测试与演示脚本

## Scope
沉淀 CP2 运行文档、测试记录与答辩演示脚本。

## Deliverables
- CP2 README 与知识库资料范围说明
- ingest 与 MCP 演示脚本
- 截图与测试记录归档

## Dependencies
- `v1-cp2-java-ai-config-health`
- `v1-cp2-python-ingest-chromadb-embedding`
- `v1-cp2-mcp-server-tools`

## Acceptance Criteria
- 可从空 ChromaDB 按文档重建知识库
- 答辩脚本可完整演示工具查询
- 测试记录覆盖主链路与常见异常

## Wave Gate Notes
- Checkpoint: `CP2`
- Lane: `docs-tests`
- Wave: `2`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP2 implementation tasks completed and parent approves Wave 2 docs pack.
