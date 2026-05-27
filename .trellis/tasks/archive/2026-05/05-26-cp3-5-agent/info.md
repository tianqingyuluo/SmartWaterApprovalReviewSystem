# CP3.5 技术路线

## 主链路

```text
Frontend
  -> Java Spring Boot
  -> MySQL task/material metadata
  -> RustFS material object storage
  -> Python FastAPI review endpoint
  -> OCR / structured parser
  -> MCP Client tool calls
  -> ChromaDB / knowledge retrieval
  -> LLM Agent structured reasoning
  -> Java callback persistence
  -> Frontend review result workbench
```

## 关键设计约束

- Java 是业务任务和权限边界的入口，Python 不绕过 Java 直接暴露材料给浏览器。
- Python 审查链路必须接收 Java 任务上下文，下载真实材料，再执行真实解析和推理。
- MCP Server 可以继续提供工具，但 Agent 侧必须使用 MCP Client 协议调用工具。
- 失败语义优先于演示成功：关键智能依赖不可用时，状态必须可解释，不产出假审查结论。
- 前端所有展示都来自后端真实 API，不使用硬编码材料、硬编码结论或静态占位充当验收结果。

## 验收门禁

- `real_e2e`: 使用真实账号、真实材料、真实对象存储、真实 OCR/LLM/MCP。
- `traceability`: 每个结论能追溯到材料、抽取字段、知识库依据、模型元数据和工具调用记录。
- `security`: 浏览器只能通过登录态和任务权限访问材料预览，不接触 Worker token 和 storage key。
- `stability`: 同一输入复跑关键结构化输出稳定。
- `git_evidence`: 按账号整理提交证据，避免最后只剩单账号集中提交。

## 推进备忘录

记录日期：2026-05-27

当前不能全并行。CP3.5 的关键路径是先让真实链路骨架活起来，再逐步推进 OCR、MCP、Agent 和最终验收。

第一批可立即推进：

- `CP3.5-A 全真实链路护栏与失败复盘`：`tianqingyuluo` 先收口验收口径、真实样例和证据格式。
- `CP3.5-B Java 主动调度 Python 审查链路`：`ymx545` 同步推进，尽早定 Java -> Python 主链路接口。
- `CP3.5-H GLM OCR data URI 请求格式修复`：`6newuser6` 同步推进，修掉已确认的真实 OCR 请求格式问题。
- `CP3.5-G 材料安全预览接口与前端嵌入`：`yuexianwei3699` 可以先做前端页面结构、状态流和错误态；真实预览接口必须等 `ymx545` 给出 Java 安全预览契约后接入。

暂时锁定：

- `CP3.5-C 生产级文档解析与 OCR`：等 `B` 的材料下载/任务上下文接口和 `H` 的 GLM OCR 修复完成后解锁。
- `CP3.5-D MCP Client 真实工具调用`：等 `C` 能产出真实文本块和抽取字段后解锁。
- `CP3.5-E 智能合规审查与结构化结论`：等 `B/C/D` 基本可用后解锁，避免没有真实输入和真实工具结果时做成规则演示。
- `CP3.5-F 真实端到端验收与答辩证据`：最后解锁，必须拿 `B/C/D/E/G/H` 的真实结果收口，不提前做截图式演示文档。

执行原则：

- `B` 和 `H` 是当前最关键的两个技术前置；一个决定 Java-Python 主链路能不能活，一个决定真实 OCR 能不能活。
- `G` 可以做前端准备，但不能用假材料预览充当验收结果。
- 所有锁定任务如果需要提前做，只能做接口讨论或 PRD 修订，不能进入实现和验收。
