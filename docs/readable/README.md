# 项目可读文档

本目录存放面向团队成员的项目说明文档，用于快速了解当前实现、近期变更和运行注意事项。

当前入口：

- [开发日志](./dev-log/index.md)：按任务或 PR 记录阶段性变更、验证结果和后续事项。
- [CP2 知识库与 MCP README](./cp2-readme.md)：CP2 知识库范围、空库重建步骤与演示入口。
- [CP2 答辩演示脚本](./cp2-demo-script.md)：按时间线执行 Java/Python/前端演示命令。
- [CP2 测试与截图归档](./cp2-test-evidence.md)：主链路测试记录、异常验证和截图补图清单。
- [CP3 集成稳定性验收记录](./cp3-test-evidence.md)：记录 CP3-D 自动化验收命令、结构化稳定性复跑和回调失败兜底证据。
- [CP3.5 全真实链路护栏与验收模板](./cp3-5-real-chain-guardrails.md)：记录 CP3 失败复盘、禁止演示兜底规则、真实联机验收清单和后续证据模板。
- [CP3.5 真实端到端验收证据](./cp3-5-real-e2e-evidence.md)：记录 2026-05-27 真实账号、真实材料、RustFS、OCR/解析、MCP Client、LLM、Java 回写和结果查询证据。
- [后端 API 与权限说明](./modules/backend/api.md)：记录登录、角色、任务可见性和 Worker 回调边界。
- [后端配置说明](./modules/backend/config.md)：记录 Java AI 服务、Python 主动调度和本地联调配置。
- [后端数据库说明](./modules/backend/database.md)：记录任务、材料、结果和账号表的当前用途。
- [Worker 适配器文档](./modules/worker/adapters.md)：记录 Python Worker 的 OCR / 审核适配器边界与当前接口约定。
- [Worker 与 Java 回写接口](./modules/worker/api.md)：记录 Worker 领取任务、结果回写、字段快照和幂等约定。
- [Worker 模块文档](./modules/worker/failure-handling.md)：记录 Python Worker 与 Java 后端的失败处理和接口契约。
- [前端页面与角色可见性](./modules/frontend/state-and-visibility.md)：记录登录态、角色入口和申请人/审核员结果投影。

其他边界：

- 原始参考资料仍放在 `docs/参考资料/` 及现有源材料目录中。
- 可执行规则和约束放在 `.trellis/spec/**`。
- 任务规划与验收状态放在 `.trellis/tasks/**`。
