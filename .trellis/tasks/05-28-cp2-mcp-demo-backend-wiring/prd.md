# 补齐 CP2 知识库 MCP 演示闭环

## Goal

让前端 `AI 知识库与 MCP 演示台` 从纯本地演示数据升级为真实后端可观测演示：页面必须能向后端发请求，能手动检查 MCP/AI 服务健康状态，并能展示文档解析入库的演示入口与结果/命令信息。

## What I Already Know

- 用户指出三个缺口：
  - 当前 `AI 知识库 MCP` 展示页没有向后端发送请求。
  - 页面需要一个按钮查看 MCP 是否健康。
  - 文档解析入库演示缺失。
- 当前前端路由为 `/knowledge-mcp`，页面文件为 `frontend/src/pages/KnowledgeMcpDemoPage.vue`。
- 当前 Java 已有 `/api/ai/health` 和 `/api/ai/ingest`，但前端页面没有调用它们。
- 当前 Python MCP CLI 工具演示可运行，注册工具包括 `knowledge_search` 和 `check_completeness`。
- 当前 Chroma `knowledge_base` collection 已有 811 条向量，但前端没有展示真实入库状态。

## Requirements

- `/knowledge-mcp` 页面加载或点击按钮时，应调用 Java 后端真实接口。
- 页面提供“检查 MCP 健康”按钮，展示 base URL、health URL、MCP URL、可达状态、检查时间和后端响应摘要。
- 页面提供“查看/刷新入库演示”入口，调用后端现有 ingest 运维接口，展示 sourceDir、workdir、chunk 参数、rebuild 标志、ingest CLI 命令和 MCP demo 验证命令。
- `knowledge_search` 和 `check_completeness` 按钮必须真实请求后端 MCP 工具链：前端调用 Java，Java 调用 Python FastAPI 工具代理，Python 工具代理调用已注册的 MCP tool。
- 保留本地演示工具结果只能用于明确标注的失败/空状态演示，不得作为默认成功路径。
- 不扩展完整 Swagger、用户管理或真实远程执行 ingest。

## Acceptance Criteria

- [x] 浏览器打开 `/knowledge-mcp` 后能看到对 Java 后端接口的请求行为。
- [x] 点击“检查 MCP 健康”能展示真实 `/api/ai/health` 返回的 reachable/mcpUrl/checkedAt 等字段。
- [x] 点击“刷新入库演示”能展示真实 `/api/ai/ingest` 返回的 ingest 命令和 MCP demo 命令。
- [x] `knowledge_search` 正常按钮调用 Java `/api/ai/mcp/knowledge-search`，Java 调用 Python `/api/mcp/tools/knowledge_search`，Python 通过 MCP `call_tool` 返回结果。
- [x] `check_completeness` 正常按钮调用 Java `/api/ai/mcp/check-completeness`，空材料选择也发送到后端并返回全部缺失项。
- [x] 前端 build/test 通过。
- [x] Java 后端相关测试通过。
- [x] Python FastAPI/MCP 相关测试通过。

## Out of Scope

- 不让浏览器绕过 Java 直接调用 Python MCP。
- 不新增远程执行 ingest 的写操作接口。
- 不改 Python ingest pipeline 和 Chroma 存储逻辑。
