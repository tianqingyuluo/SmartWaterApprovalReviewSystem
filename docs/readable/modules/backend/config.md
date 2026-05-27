# 后端配置说明

## Java 调度 Python 审查服务

Java 后端通过 `water-approval.ai-service.*` 配置 Python AI/MCP 服务。CP3.5-B 之后，任务提交默认会主动调用 Python FastAPI 的审查任务入口。

| 配置 | 默认值 | 说明 |
|---|---|---|
| `water-approval.ai-service.base-url` | `http://localhost:8000` | Python FastAPI 服务地址。 |
| `water-approval.ai-service.health-path` | `/health` | Java `/api/ai/health` 探活路径。 |
| `water-approval.ai-service.internal-token` | 空 | Java 调用 Python 时携带的 `X-Internal-Token`，建议放入 `application-secrets.yaml`。 |
| `water-approval.ai-service.timeout` | `3s` | Java 调用 Python 的连接和读取超时。 |
| `water-approval.ai-service.review-task.enabled` | `true` | 是否在提交任务后主动调度 Python FastAPI。 |
| `water-approval.ai-service.review-task.path` | `/api/review/tasks` | Python 审查任务创建路径。 |
| `water-approval.ai-service.review-task.max-attempts` | `3` | 调度失败时的最大尝试次数，至少为 `1`。 |

对应环境变量：

```bash
AI_SERVICE_BASE_URL=http://localhost:8000
AI_SERVICE_INTERNAL_TOKEN=<internal-token>
AI_SERVICE_TIMEOUT=3s
AI_REVIEW_TASK_DISPATCH_ENABLED=true
AI_REVIEW_TASK_PATH=/api/review/tasks
AI_REVIEW_TASK_MAX_ATTEMPTS=3
```

## 状态语义

- `review-task.enabled=true`：`POST /api/task/submit` 创建任务后主动调用 Python；Python 接受后 Java 将任务状态写为 `PROCESSING`。
- `review-task.enabled=false`：Java 保留 `SUBMITTED` 状态，兼容 Worker 通过 `GET /api/task/pending` 轮询领取。
- Python 不可用、鉴权失败、超时、限流或 5xx 时，Java 将任务写为 `FAILED`，并保存失败原因，前端不得看到伪造的 AI 成功结论。

## 本地联调建议

1. 启动 Python FastAPI：`uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000`。
2. 启动 Java 后端：`./mvnw spring-boot:run`。
3. 调用 `GET /api/ai/health` 确认 Java 能探活 Python。
4. 登录后提交材料，确认 Java 日志出现 Python 调度记录，任务状态进入 `PROCESSING`。
5. 关闭 Python 后再次提交，确认任务进入 `FAILED`，审查人结果包含 `TIMEOUT`、`UPSTREAM_5XX` 或对应失败分类。
