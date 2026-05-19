# 项目可读文档

本目录存放面向团队成员的项目说明文档，用于快速了解当前实现、近期变更和运行注意事项。

当前入口：

- [开发日志](./dev-log/index.md)：按任务或 PR 记录阶段性变更、验证结果和后续事项。
- [Worker 适配器文档](./modules/worker/adapters.md)：记录 Python Worker 的 OCR / 审核适配器边界与当前接口约定。
- [Worker 与 Java 回写接口](./modules/worker/api.md)：记录 Worker 领取任务、结果回写、字段快照和幂等约定。
- [Worker 模块文档](./modules/worker/failure-handling.md)：记录 Python Worker 与 Java 后端的失败处理和接口契约。
- [前端页面说明](./modules/frontend/pages.md)：记录 CP2 MCP 演示台与当前前端页面边界。
- [前端 API 契约说明](./modules/frontend/api-contract.md)：记录 MCP 演示台的工具调用路径、请求/响应示例和演示兜底约定。

其他边界：

- 原始参考资料仍放在 `docs/参考资料` 及现有源材料目录中。
- 可执行规则和约束放在 `.trellis/spec/**`。
- 任务规划与验收状态放在 `.trellis/tasks/**`。
