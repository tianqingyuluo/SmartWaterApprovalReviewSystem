# CP3.5-D MCP Client 真实工具调用

## Scope

把审查 Agent 的工具调用链路改成真实 MCP Client 调用。Agent 不能只调用 Python 内部函数，也不能只证明 MCP Server 可启动；必须在审查链路中发现、调用并记录 MCP 工具结果。

## Problem

旧设计允许 FastAPI 内部 Agent 直接调用共享函数，MCP Server 主要用于演示。这不能满足 CP3 对“Agent 调用 MCP 工具”的验收口径。CP3.5 必须让真实审查任务经过 MCP Client，并在日志/结果中能看到工具名、输入摘要、输出摘要和引用。

## Deliverables

- Python 审查服务内置 MCP Client 或通过适配层连接 MCP Server。
- MCP 工具发现：
  - `knowledge_search`
  - `check_completeness`
  - 其他已有/必要工具
- 工具调用链路：
  - Agent 根据任务上下文选择工具。
  - 工具输入来自真实材料抽取结果和任务元数据。
  - 工具输出进入 Agent 推理上下文。
- 工具调用记录：
  - tool name
  - input summary
  - output summary
  - source/citation
  - latency/status/error
- MCP 不可用时，任务进入明确失败/阻塞/待重试，不改走内部函数伪装成功。

## Acceptance Criteria

- 真实审查任务日志显示 MCP Client 完成工具列表发现。
- 至少一次真实审查调用 `knowledge_search`，并把法规/知识库来源写入审查依据。
- 至少一次真实审查调用 `check_completeness`，并把缺失材料或完整性判断写入问题列表。
- 关闭 MCP Server 后，审查任务不会生成假成功结论，错误状态和日志可见。
- 单元测试覆盖 MCP Client 适配器的成功、失败和工具 schema 转换。
- 真实 E2E 证据包含 MCP 工具调用轨迹。

## Non-Goals

- 不把 MCP Server 改造成通用平台。
- 不做 CP4 的部署观测面板。
- 不用内部函数 fallback 替代 MCP Client。

## Dependencies

- `05-27-cp3-5-real-chain-guardrails`
- `05-27-cp3-5-document-ocr-real-pipeline`
- 既有 `v1-cp2-mcp-server-tools`
