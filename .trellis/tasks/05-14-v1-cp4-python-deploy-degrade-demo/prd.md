# CP4-B Python 部署、降级与演示样例

## Scope
补齐 Python 部署、系统依赖与外部 API 降级演示方案。

## Deliverables
- FastAPI 与 MCP Server 部署文档
- LibreOffice/字体与模型配置清单
- 外部 API 失败降级演示说明

## Dependencies
- `v1-cp2-python-ingest-chromadb-embedding`
- `v1-cp2-mcp-server-tools`
- `v1-cp3-python-fastapi-rules-agent`

## Acceptance Criteria
- 新环境可按说明启动服务
- API 错误返回结构化失败状态
- 降级演示路径可复现

## Wave Gate Notes
- Checkpoint: `CP4`
- Lane: `python`
- Wave: `4`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: CP2/CP3 Python baseline completed and parent approves Wave 4.
