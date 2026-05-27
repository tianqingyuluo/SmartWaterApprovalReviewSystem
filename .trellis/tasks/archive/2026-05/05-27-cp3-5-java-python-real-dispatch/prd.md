# CP3.5-B Java 主动调度 Python 审查链路

## Scope

把“前端提交后 Java 创建任务、主动调用 Python FastAPI 审查、Python 回写 Java、前端查询结果”的生产链路打通。CP3 旧证据主要证明 Worker 轮询和回写，不足以证明 Java-Python 的真实集成。

## Problem

当前系统可以保存材料、生成任务，并通过 Worker 轮询证明部分回写能力。但课程检查点需要的是完整系统集成：用户提交后，后端服务应能把任务交给 AI 审查服务，并把状态、错误和结果持久化到业务系统。只靠 Worker 轮询或测试 stub，现场演示链路不稳定，也难以解释失败。

## Deliverables

- Java 侧 Python FastAPI client，使用配置化 base URL、超时、重试和错误映射。
- 提交任务后触发 Python 审查的生产路径：
  - 创建 Java 审查任务。
  - 传递任务 ID、材料清单、材料下载引用和回写地址。
  - Python 接收后进入真实处理队列或同步受理。
- Java 审查状态机补齐：
  - `SUBMITTED` / `DISPATCHING` / `PROCESSING` / `SUCCEEDED` / `FAILED` / `RETRYABLE_FAILED` 等实际需要状态。
  - 不把 Python 不可用伪装为成功。
- 回写接口保持幂等，支持重复回调不重复插入结果。
- 前端任务状态能看到调度中、处理中、失败原因和成功结果。
- 日志记录关联 ID，能串起前端提交、Java 调度、Python 受理、Python 回写。

## Acceptance Criteria

- 真实启动 Java 和 Python 后，前端提交材料能触发 Java 主动调用 Python。
- 关闭 Python 服务时，Java 任务进入明确失败/可重试状态，前端能看到原因，不产生假 AI 结论。
- Python 回写成功后，Java 持久化结构化结论、问题列表、抽取字段和模型/工具元数据。
- 重复回写同一 Python 任务结果时，Java 不产生重复结果。
- Java 集成测试覆盖成功调度、Python 不可用、回写幂等和结果查询。
- 真实 E2E 证据包含 Java 调用 Python 的日志片段或请求追踪 ID。

## Non-Goals

- 不把 Python Worker token 暴露给浏览器。
- 不实现 OCR 或 Agent 推理本身；本任务只负责 Java-Python 调度和状态回写。
- 不做 CP4 的报告导出或补正版本链路。

## Dependencies

- `05-27-cp3-5-real-chain-guardrails`
- 既有 `v1-cp3-java-ai-task-callback-results`
- 既有 `v1-cp3-reviewer-actions-applicant-result`
