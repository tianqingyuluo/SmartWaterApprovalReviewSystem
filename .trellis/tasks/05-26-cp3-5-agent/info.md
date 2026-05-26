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
