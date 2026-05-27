# CP2-C 前端 AI 知识库与 MCP 演示台

## Scope
交付可独立演示的 CP2 前端演示台，聚焦 AI 知识库与 MCP 工具调用可视化。

该任务只覆盖检查点 2 的演示能力，不扩展为 CP3 完整审批流程页面。

## Deliverables
- 演示台首页与状态面板，展示知识库状态、MCP 服务状态、最近一次调用信息
- `knowledge_search` 调用区：查询输入、参数配置、结果列表、依据片段展示
- `check_completeness` 调用区：材料输入、完整性判断结果、缺失项/问题提示展示
- 全量状态处理：加载中、空结果、失败重试
- 演示模式标识：页面固定展示“演示模式/非正式审批结论”
- 接口契约输出：整理请求/响应 JSON 样例与字段说明，供 CP2 文档引用

## Dependencies
- `v1-cp2-python-ingest-chromadb-embedding`

## Acceptance Criteria
- 不依赖 CP3 审批待办链路，也可独立完成 `knowledge_search` 与 `check_completeness` 演示
- 状态面板可明确显示知识库与 MCP 服务可用性
- 两个工具在加载、空结果、失败三类状态下都有可见且可解释的 UI 表现
- 页面明确标识演示模式，避免与正式审批结论混淆
- 输出接口契约样例可直接用于 CP2 验收材料
