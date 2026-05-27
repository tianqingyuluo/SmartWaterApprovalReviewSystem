# CP3.5 真实端到端验收证据

> 记录日期：2026-05-27
> 分支：`v1`
> 任务：`.trellis/tasks/05-26-cp3-5-agent`
> 证据目录：`/tmp/smartwater-cp35/`

## 结论

CP3.5 主链路在本地真实联调环境跑通：

```text
真实账号 -> Java -> RustFS -> Python FastAPI/Worker -> 文档解析/OCR
-> MCP Client -> LLM Agent -> Java 回写 -> API/前端结果查询
-> 浏览器安全材料预览
```

最终真实联机运行 `SW1F9B70302CD14DAE` 达到 `COMPLETED`，审批人员结果包含：

- `modelMetadata`：真实 DashScope/Qwen 调用元数据。
- `toolCallTraces`：3 条 MCP Client 调用轨迹。
- `extractedFields`：54 个真实材料抽取字段。
- `issues`：`INCONSISTENT_IDENTITY`、`MULTI_APPLICANT_UNSUPPORTED`。
- `draftOpinion` 和 `manualReviewNotice`：均已回写并可查询。
- 原始材料安全预览：图片材料可通过网页登录 API 以二进制流预览，DOCX 明确返回 `415`。

## 运行环境

| 组件 | 运行方式 | 证据 |
| --- | --- | --- |
| Java 后端 | `:8080`，真实 MySQL 与 RustFS 配置 | `complete-submit-7.json`、`complete-status-7.json` |
| Python FastAPI | `uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000` | 真实任务被 Java 主动调度并回写 |
| MySQL | 本地容器，端口 `3306` | Java 提交、状态、结果查询均成功 |
| RustFS | 本地容器，端口 `9000/9001` | Java 上传真实材料，Python 与预览接口通过受控链路读取 |
| OCR/解析 | DOCX 解析 + 图片 OCR | reviewer `extractedFields=54` |
| MCP | Python MCP stdio server | reviewer `toolCallTraces=3` |
| LLM | DashScope/Qwen OpenAI-compatible API | reviewer `modelMetadata` 存在 |

## 样例材料

| 表单字段 | 文件 | 类型 | 用途 |
| --- | --- | --- | --- |
| `applicationForm` | `docs/参考资料/申请书.docx` | DOCX | 申请书结构化解析 |
| `businessLicense` | `docs/参考资料/营业执照.jpg` | 图片 | 营业执照 OCR 与浏览器预览 |
| `idCard` | `docs/参考资料/身份证.jpg` | 图片 | 身份证 OCR 与浏览器预览 |

## 真实链路步骤

1. 使用 `applicant/applicant123` 登录 Java `/api/auth/login`。
2. 通过 Java `/api/task/submit` 上传三份真实材料。
3. Java 保存材料到 RustFS，并主动调度 Python `POST /api/review/tasks`。
4. Python 受理任务并处理真实材料。
5. Python 通过 MCP Client 调用 `list_tools`、`check_completeness`、`knowledge_search`。
6. Python 调用真实 LLM，解析结构化审核 JSON 并保留 `modelMetadata`。
7. Python 通过 Worker API 回写 Java。
8. 使用 `reviewer/reviewer123` 查询 `/api/task/{taskId}/result/reviewer`。
9. 使用网页登录 token 查询 `/api/task/{taskId}/material/{materialType}/preview` 验证原始材料安全预览。

## 证据文件

| 文件 | 内容 |
| --- | --- |
| `/tmp/smartwater-cp35/complete-submit-7.json` | 提交响应，任务 `SW1F9B70302CD14DAE`，初始状态 `PROCESSING` |
| `/tmp/smartwater-cp35/complete-status-history-7.json` | 状态轮询历史，最终到 `COMPLETED` |
| `/tmp/smartwater-cp35/complete-status-7.json` | Java 状态查询，三份材料均 `uploaded=true` |
| `/tmp/smartwater-cp35/complete-applicant-result-7.json` | 申请人结果投影，未暴露 reviewer-only 字段 |
| `/tmp/smartwater-cp35/complete-reviewer-result-7.json` | 审批人员完整结果，包含模型元数据、MCP trace、抽取字段和审核结论 |
| `/tmp/smartwater-cp35/complete-summary-7.json` | 脱敏摘要，便于快速复核 |
| `/tmp/smartwater-cp35/complete-preview-business_license-7.bin` | 营业执照预览响应体前 4096 字节采样 |
| `/tmp/smartwater-cp35/complete-preview-id_card-7.bin` | 身份证预览响应体前 4096 字节采样 |
| `/tmp/smartwater-cp35/complete-preview-application_form-7.err.txt` | DOCX 预览不支持的 `415` 文本响应 |

`complete-summary-7.json` 摘要：

```json
{
  "taskId": "SW1F9B70302CD14DAE",
  "status": "COMPLETED",
  "modelMetadataPresent": true,
  "toolCallTraceCount": 3,
  "extractedFieldCount": 54,
  "issueCodes": [
    "INCONSISTENT_IDENTITY",
    "INCONSISTENT_IDENTITY",
    "MULTI_APPLICANT_UNSUPPORTED"
  ],
  "materialPreview": {
    "APPLICATION_FORM": {
      "httpStatus": 415,
      "contentType": "text/plain;charset=UTF-8",
      "bytes": 45,
      "bodyPrefix": "当前材料格式暂不支持浏览器预览"
    },
    "BUSINESS_LICENSE": {
      "httpStatus": 200,
      "contentType": "image/jpeg",
      "nosniff": "nosniff",
      "bytes": 449597
    },
    "ID_CARD": {
      "httpStatus": 200,
      "contentType": "image/jpeg",
      "nosniff": "nosniff",
      "bytes": 70770
    }
  }
}
```

## MCP 与 LLM 证据

审批人员结果中的 MCP 调用轨迹：

| 工具 | 状态 | 作用 |
| --- | --- | --- |
| `list_tools` | `SUCCESS` | 发现 MCP 工具，返回 `knowledge_search`、`check_completeness` |
| `check_completeness` | `SUCCESS` | 三份材料均已提交，`missing=[]` |
| `knowledge_search` | `SUCCESS` | 检索知识片段和依据来源 |

模型元数据只在本地证据 JSON 中保留完整值；本文档不记录登录 token、Worker token、对象存储密钥、外部 API key、原始完整材料文本或完整 prompt。

## 安全材料预览证据

新增浏览器安全预览接口：

```http
GET /api/task/{taskId}/material/{materialType}/preview
Authorization: Bearer <sa-token>
```

验收结果：

| 材料 | HTTP | Content-Type | 安全头 | 行为 |
| --- | ---: | --- | --- | --- |
| `APPLICATION_FORM` | `415` | `text/plain;charset=UTF-8` | 不适用 | DOCX 不嵌入浏览器预览，页面显示明确不支持 |
| `BUSINESS_LICENSE` | `200` | `image/jpeg` | `X-Content-Type-Options: nosniff` | 以 `inline` 二进制流预览 |
| `ID_CARD` | `200` | `image/jpeg` | `X-Content-Type-Options: nosniff` | 以 `inline` 二进制流预览 |

预览接口不接受 `storageKey` 参数，不暴露 Worker token，不复用 `/api/material/download?key=...` 的 Worker 下载边界。

## 自动化门禁

本次变更完成后已运行：

| 模块 | 命令 | 结果 |
| --- | --- | --- |
| Python | `uv run --extra dev ruff check src tests` | 通过 |
| Python | `uv run --extra dev python -m compileall src main.py` | 通过 |
| Python | `uv run --extra dev python -m pytest -q` | `109 passed, 4 subtests passed` |
| Java | `./mvnw test` | `102 tests`，`BUILD SUCCESS` |
| 前端 | `npm run test -- --run` | `20 passed` |
| 前端 | `npm run build` | 通过 |

## 修复点

- Java 新增 `GET /api/task/{taskId}/material/{materialType}/preview`，复用普通网页登录鉴权和任务可见性，不让浏览器传 `storageKey`。
- 二进制预览只支持 `pdf/jpg/jpeg/png`，DOCX 返回 HTTP `415 text/plain;charset=UTF-8`。
- 前端结果页通过 axios blob 请求加载材料预览，图片和 PDF 生成 object URL，组件卸载或任务切换时释放 URL。
- Python LLM parser 支持将 Qwen 返回的括号包裹依据、标题依据、前缀依据归一化回输入 `source_id`。
- `basisRefs` 仍必须来自输入知识片段；归一化只接受可映射别名，不接受模型编造依据。

## 历史失败对照

早期运行证明了不同阶段的链路问题，最终以 `*-7` 作为当前可合并证据：

| 任务 | 状态 | `modelMetadata` | `toolCallTraces` | `extractedFields` | 问题 |
| --- | --- | --- | ---: | ---: | --- |
| `SWC655B9F95E5242A8` | `FAILED` | 无 | 3 | 54 | Qwen 中文 key / schema 归一化不足，`MODEL_UNCERTAIN` |
| `SW8739D585C6CB47FF` | `FAILED` | 无 | 3 | 54 | Qwen 中文 key / schema 归一化不足，`MODEL_UNCERTAIN` |
| `SW4FA46D708B44411D` | `COMPLETED` | 有 | 3 | 54 | 首次证明真实 LLM 结构化结果可回写 |
| `complete-summary-5` | `FAILED` | 无 | 3 | 54 | Qwen `basis_refs` 使用 `[BASIS_ID]`、材料标题等别名，被旧校验误判为编造依据 |
| `complete-summary-6` | `FAILED` | 无 | 3 | 54 | 同类 basis ref 别名归一化缺口复现 |
| `SW1F9B70302CD14DAE` | `COMPLETED` | 有 | 3 | 54 | basis ref 归一化修复后通过，并补齐安全预览证据 |

结论：`*-5`、`*-6` 不是外部服务失败，而是本地 parser 对真实模型输出变体支持不够；修复后 `*-7` 验证真实模型输出可以通过本地 schema 校验并回写 Java。
