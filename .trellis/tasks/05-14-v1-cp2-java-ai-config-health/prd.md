# CP2-A Java 配置与知识库触发入口

## Scope
在 Java 侧补齐 AI 服务配置、健康检查与 ingest 触发入口约定。

## Deliverables
- Python AI 服务地址与内部 token 配置说明
- 健康检查/状态查询接口约定
- ingest 触发 API 或运维替代方案

## Dependencies
- `v1-cp2-python-ingest-chromadb-embedding`
- `v1-cp2-mcp-server-tools`

## Acceptance Criteria
- Java 可配置并探活 Python 服务
- 部署文档可验证健康检查路径
- 与 Python ingest/MCP 接口契约一致

## Wave Gate Notes
- Checkpoint: `CP2`
- Lane: `java`
- Wave: `2`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP2 Python ingest and MCP tool baseline completed; parent approves Wave 2.
