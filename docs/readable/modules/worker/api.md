# Worker 与 Java 回写接口

Python Worker 通过 Java 后端的 Worker API 拉取待处理任务、下载材料、更新状态并回写审核结果。Worker API 受 `X-Worker-Token` 保护，普通申请人和前端查询接口仍使用 `taskId + sessionId`。

## FastAPI 审查任务入口

CP3-B 新增 Python FastAPI 服务入口，供 Java 后续通过内部 HTTP 触发 AI 初评：

- `GET /health`
- `POST /api/review/tasks`
- `GET /api/review/tasks/{aiTaskId}`

启动命令：

```bash
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

`POST /api/review/tasks` 使用 Java 的 `taskId` 作为 `aiTaskId`，返回 `202` 和 `QUEUED` 后在后台执行审核。任务状态会先尝试回写 Java 为 `PROCESSING`，最终仍通过 Java `/api/task/{taskId}/result` 写回结构化结果。

如果配置了 `INTERNAL_API_TOKEN`，FastAPI 任务接口必须携带：

```text
X-Internal-Token: <INTERNAL_API_TOKEN>
```

FastAPI 内存任务状态只服务本进程查询和调试。Java 的 `review_task`、`review_result` 仍是最终状态和结果的权威来源。

## 任务领取

- `GET /api/task/pending`
- Java 返回 `SUBMITTED` 或 `QUEUED` 任务，并在服务层领取为 `PROCESSING`。
- 返回材料槽位时始终包含 `APPLICATION_FORM`、`BUSINESS_LICENSE`、`ID_CARD` 三个 MVP 固定类型。
- 轮询 Worker 与 FastAPI 后台任务共用同一条 orchestrator 处理链路，避免两套 AI 初评逻辑分叉。

## 结果回写

- `PUT /api/task/{taskId}/result`
- Worker 回写 `status`、`resultSummary`、`knowledgePackVersion`、`applicantResult` 和 `reviewerResult`。
- Java 使用 `review_result (task_id, result_type)` 作为唯一结果边界；重复回调会更新已有 `APPLICANT` / `REVIEWER` 行，不产生重复结果。

`reviewerResult.extractedFields` 是审批人员字段快照，来源于 OCR / 字段抽取结果：

```json
{
  "fieldKey": "applicant.name",
  "fieldValue": "某某科技有限公司",
  "confidence": 0.93,
  "sourceMaterial": "APPLICATION_FORM",
  "evidence": "申请人：某某科技有限公司"
}
```

申请人结果不携带 `extractedFields`。申请人视图只展示摘要、申请人可见问题和材料缺失信息，避免暴露完整字段抽取细节。

## 查询结果

- `GET /api/task/{taskId}/result/applicant?sessionId=...` 返回申请人投影。
- `GET /api/task/{taskId}/result/reviewer?sessionId=...` 返回审批人员投影，包括 `issues`、`riskHints`、`draftOpinion`、`missingMaterials`、`manualReviewNotice`、`modelMetadata` 和 `extractedFields`。

## 验证要求

- Java 服务测试必须覆盖重复回调幂等和 `extractedFields` 查询。
- Python Worker 测试必须覆盖 `ReviewResult.extracted_fields` 到 camelCase `extractedFields` 的序列化。
- FastAPI 测试必须覆盖内部 token、camelCase DTO、任务创建、状态查询和未知任务 `404`。
- Orchestrator 测试必须覆盖 Agent 失败时降级为规则结果和人工复核提示。
- 结果回写失败时 Worker 不能把 HTTP 200 但业务 `code != 200` 当作成功。
