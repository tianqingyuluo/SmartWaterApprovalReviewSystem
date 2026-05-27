# CP3.5 真实端到端验收证据

> 记录日期：2026-05-27  
> 分支：`task/cp3-5-complete-e2e`  
> 任务：`.trellis/tasks/05-26-cp3-5-agent`  
> 证据目录：`/tmp/smartwater-cp35/`

## 结论

CP3.5 主链路在本地真实联调环境跑通：

```text
真实账号 -> Java -> RustFS -> Python FastAPI/Worker -> 文档解析/OCR
-> MCP Client -> LLM Agent -> Java 回写 -> API/前端结果查询
```

第三次真实联机运行 `SW4FA46D708B44411D` 达到 `COMPLETED`，审批人员结果包含：

- `modelMetadata`：真实 DashScope/Qwen 调用元数据。
- `toolCallTraces`：3 条 MCP Client 调用轨迹。
- `extractedFields`：54 个真实材料抽取字段。
- `issues`：`MISSING_FIELD`、`INCONSISTENT_IDENTITY`。
- `riskHints`：2 条风险提示。
- `draftOpinion` 和 `manualReviewNotice`：均已回写并可查询。

## 运行环境

| 组件 | 运行方式 | 证据 |
| --- | --- | --- |
| Java 后端 | `:8080`，真实 MySQL 与 RustFS 配置 | `complete-submit-3.json`、`complete-status-3.json` |
| Python FastAPI | `uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000` | `/health` 返回 `smart-water-review-fastapi` |
| MySQL | 本地容器，端口 `3306` | Java 提交、状态、结果查询均成功 |
| RustFS | 本地容器，端口 `9000/9001` | Java 上传真实材料，Python 通过受控下载链路处理 |
| OCR/解析 | DOCX 解析 + 图片 OCR | reviewer `extractedFields=54` |
| MCP | Python MCP stdio server | reviewer `toolCallTraces=3` |
| LLM | DashScope/Qwen OpenAI-compatible API | reviewer `modelMetadata` 存在 |

## 样例材料

| 表单字段 | 文件 | 类型 | 用途 |
| --- | --- | --- | --- |
| `applicationForm` | `docs/参考资料/申请书.docx` | DOCX | 申请书结构化解析 |
| `businessLicense` | `docs/参考资料/营业执照.jpg` | 图片 | 营业执照 OCR |
| `idCard` | `docs/参考资料/身份证.jpg` | 图片 | 身份证 OCR |

## 真实链路步骤

1. 使用 `applicant/applicant123` 登录 Java `/api/auth/login`。
2. 通过 Java `/api/task/submit` 上传三份真实材料。
3. Java 保存材料并主动调度 Python `POST /api/review/tasks`。
4. Python 受理任务并处理真实材料。
5. Python 通过 MCP Client 调用 `list_tools`、`check_completeness`、`knowledge_search`。
6. Python 调用真实 LLM，解析结构化审核 JSON 并保留 `modelMetadata`。
7. Python 通过 Worker API 回写 Java。
8. 使用 `reviewer/reviewer123` 查询 `/api/task/{taskId}/result/reviewer`。

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `/tmp/smartwater-cp35/complete-submit-3.json` | 提交响应，任务 `SW4FA46D708B44411D`，初始状态 `PROCESSING` |
| `/tmp/smartwater-cp35/complete-status-history-3.json` | 状态轮询历史，第 11 次轮询到 `COMPLETED` |
| `/tmp/smartwater-cp35/complete-status-3.json` | Java 状态查询，三份材料均 `uploaded=true` |
| `/tmp/smartwater-cp35/complete-applicant-result-3.json` | 申请人结果投影，未暴露 reviewer-only 字段 |
| `/tmp/smartwater-cp35/complete-reviewer-result-3.json` | 审批人员完整结果，包含模型元数据、MCP trace、抽取字段和审核结论 |
| `/tmp/smartwater-cp35/complete-summary-3.json` | 脱敏摘要，便于快速复核 |

`complete-summary-3.json` 摘要：

```json
{
  "taskId": "SW4FA46D708B44411D",
  "status": "COMPLETED",
  "hasModelMetadata": true,
  "toolCallTraceCount": 3,
  "extractedFieldCount": 54,
  "issueCodes": [
    "MISSING_FIELD",
    "INCONSISTENT_IDENTITY"
  ],
  "riskHintCount": 2,
  "draftOpinionPresent": true,
  "manualReviewNoticePresent": true
}
```

## MCP 与 LLM 证据

审批人员结果中的 MCP 调用轨迹：

| 工具 | 状态 | 作用 |
| --- | --- | --- |
| `list_tools` | `SUCCESS` | 发现 MCP 工具，返回 `knowledge_search`、`check_completeness` |
| `check_completeness` | `SUCCESS` | 三份材料均已提交，`missing=[]` |
| `knowledge_search` | `SUCCESS` | 检索 8 条知识片段和依据来源 |

模型元数据摘要：

```json
{
  "provider": "dashscope",
  "model": "qwen-max",
  "finishReason": "stop",
  "tokenUsage": {
    "prompt_tokens": 9773,
    "completion_tokens": 590,
    "total_tokens": 10363
  }
}
```

文档中不记录登录 token、Worker token、对象存储密钥、外部 API key、原始完整材料文本或完整 prompt。

## 自动化门禁

本次变更完成后已运行：

| 模块 | 命令 | 结果 |
| --- | --- | --- |
| Python | `uv run --extra dev ruff check src tests` | 通过 |
| Python | `uv run --extra dev python -m compileall src main.py` | 通过 |
| Python | `uv run --extra dev python -m pytest -q` | `107 passed, 4 subtests passed` |
| Java | `./mvnw test` | `94 tests`，`BUILD SUCCESS` |
| 前端 | `npm run test -- --run` | `19 passed` |
| 前端 | `npm run build` | 通过 |

## 修复点

- Python Agent 从直接调用知识工具改为 `SmartWaterMcpClient` 发现并调用 MCP stdio 工具。
- 审批人员结果新增 `toolCallTraces`，Java 和前端均可展示。
- LLM 解析器支持 fenced JSON、wrapper key、camelCase key 和真实 Qwen 中文 key。
- `basisRefs` 仍必须来自输入知识片段，不能接受模型编造依据。
- CP3.5 失败语义收紧：OCR、下载、MCP、LLM 等技术失败进入 `FAILED`，缺材料业务问题仍可 `PARTIAL_SUCCESS`。

## 历史失败对照

前两次真实运行已证明 Java -> Python -> RustFS -> OCR/解析 -> MCP -> Java 回写可达，但 LLM 输出中文 key 导致 schema 失败：

| 任务 | 状态 | `modelMetadata` | `toolCallTraces` | `extractedFields` | 问题 |
| --- | --- | --- | ---: | ---: | --- |
| `SWC655B9F95E5242A8` | `FAILED` | 无 | 3 | 54 | `MODEL_UNCERTAIN` |
| `SW8739D585C6CB47FF` | `FAILED` | 无 | 3 | 54 | `MODEL_UNCERTAIN` |
| `SW4FA46D708B44411D` | `COMPLETED` | 有 | 3 | 54 | `MISSING_FIELD`、`INCONSISTENT_IDENTITY` |

第三次运行验证了中文 key 归一化补丁后，真实 LLM 结果可以通过本地 schema 校验并回写 Java。
