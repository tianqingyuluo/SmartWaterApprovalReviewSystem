# CP3.5-E 智能合规审查与结构化结论

## Scope

基于真实 OCR/解析文本、MCP 工具结果、知识库 RAG 和 LLM Agent 推理，生成可引用、可追溯、稳定的初审结论。该任务的重点是“智能审查”，不是用规则兜底替代 Agent。

## Problem

旧 CP3 任务允许 Agent 失败后降级为规则结果加人工复核。这个做法适合解释系统错误，但不能作为智能初审能力的验收结果。CP3.5 需要让真实 LLM 参与审查，输出结构化结论，并在失败时明确失败，而不是产出假智能。

## Deliverables

- 审查输入：
  - 真实材料抽取文本和字段。
  - MCP `knowledge_search` 结果。
  - MCP `check_completeness` 结果。
  - 可配置审查规则。
- LLM Agent 推理：
  - temperature 设为稳定输出优先。
  - 使用结构化输出 schema。
  - 输出包含结论、问题、严重级别、材料类型、字段、依据、建议和模型元数据。
- 结论归一化：
  - `PASS`
  - `NEEDS_CORRECTION`
  - `MANUAL_REVIEW`
  - `FAILED`
- 追溯信息：
  - 引用材料片段。
  - 引用知识库来源。
  - MCP tool call IDs。
  - 模型名、请求 ID、时间戳。
- 失败语义：
  - LLM 不可用或结构化解析失败时不输出规则假结论。
  - 可以提示“智能审查失败，需要重试/人工处理”，但不能显示为 AI 审查成功。

## Acceptance Criteria

- 真实材料审查能生成结构化结论、问题列表、依据和修改建议。
- 缺材料样例能由完整性工具和 Agent 共同反映到问题列表。
- 内容错误样例能引用材料片段和知识库依据给出修改建议。
- LLM 调用失败时，任务状态明确失败/待重试，前端不展示假 AI 结论。
- 同一材料复跑 3 次，关键结论、问题编码、严重级别和引用来源稳定。
- Java 回写结果包含模型元数据和工具调用摘要。
- 测试覆盖结构化输出解析、结论归一化、失败状态和稳定性签名。

## Non-Goals

- 不做审批最终裁决自动化；CP3 仍是初审建议和工作台。
- 不把规则引擎单独包装成 Agent 结果。
- 不做 CP4 报告导出。

## Dependencies

- `05-27-cp3-5-real-chain-guardrails`
- `05-27-cp3-5-document-ocr-real-pipeline`
- `05-27-cp3-5-mcp-client-tool-chain`
- `05-27-cp3-5-java-python-real-dispatch`
