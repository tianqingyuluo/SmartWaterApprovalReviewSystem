# CP3.5-F 真实端到端验收与答辩证据

## Scope

用真实账号、真实材料、真实中间件、真实 OCR/LLM/MCP 调用完成 CP3.5 端到端验收，并把证据整理到 `docs/readable/**`。这是 CP3.5 的最终收口任务。

## Problem

CP3 旧证据的核心限制是“不宣称真实 OCR/LLM/对象存储联机 E2E”。CP3.5 不能再只提交单元测试通过或局部 mock 证明，必须能现场跑通完整链路，并且能解释每一步从哪里来、到哪里去、失败时是什么状态。

## Deliverables

- 一键或少步骤启动说明：
  - Java 后端
  - Python FastAPI
  - Python Worker/调度组件
  - 前端
  - MySQL
  - RustFS
  - MCP/ChromaDB/知识库依赖
- 真实账号准备：
  - 申请人账号
  - 审批人员账号
  - 管理员账号
  - Git 提交账号证据按指导书口径整理到账号维度
- 真实样例：
  - 材料完整且基本合规。
  - 缺少材料。
  - 材料内容存在明显问题。
- 验收证据：
  - 上传材料截图/日志。
  - Java 调度 Python 日志。
  - Python OCR/LLM/MCP 调用日志或 trace。
  - Java 回写和前端展示截图。
  - 复跑稳定性记录。
  - 关键依赖关闭时的失败状态记录。
  - Git 提交记录与账号归属。

## Acceptance Criteria

- 从前端登录申请人账号提交材料，到审批人员账号查看 AI 初审结果，全链路真实跑通。
- 前端结果页可同时看到原始材料预览、OCR/抽取字段、AI 结论、问题、依据和建议。
- 至少一份样例证明真实 OCR 调用成功。
- 至少一份样例证明真实 MCP 工具调用成功。
- 至少一份样例证明真实 LLM 生成结构化审查结论。
- 关闭 OCR/LLM/MCP 任一关键依赖时，系统不生成假成功结论。
- 同一材料复跑 3 次，关键结构化结果稳定。
- `docs/readable/cp3-5-real-e2e-evidence.md` 或等价文档记录完整证据。
- Git 提交记录按账号整理，满足指导书对版本控制的检查口径。

## Non-Goals

- 不做 CP4 答辩完整包、部署手册或报告导出。
- 不用静态截图替代实时可运行系统。
- 不把测试环境 mock 结果写进最终验收证据。

## Dependencies

- `05-27-cp3-5-real-chain-guardrails`
- `05-27-cp3-5-java-python-real-dispatch`
- `05-27-cp3-5-document-ocr-real-pipeline`
- `05-27-cp3-5-mcp-client-tool-chain`
- `05-27-cp3-5-intelligent-compliance-result`
- `05-26-v1-cp3-material-safe-preview`
- `05-26-v1-cp3-glm-ocr-data-uri-fix`
