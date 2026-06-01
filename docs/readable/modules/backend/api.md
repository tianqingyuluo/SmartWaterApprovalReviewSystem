# 后端 API 与权限说明

## CP3 最小登录与角色

CP3 增加了真实流程所需的最小 RBAC，不包含完整后台用户管理。

登录接口：

- `POST /api/auth/login`：使用用户名和密码登录，返回 Sa-Token token 与当前用户信息。
- `GET /api/auth/me`：读取当前登录用户，要求 `Authorization: Bearer <token>`。

当前角色：

- `APPLICANT`：申请人，只能提交和查看自己的申请。
- `REVIEWER`：审批人员，只能查看进入审核可见状态的任务。
- `ADMIN`：管理员，用于演示和排障，可查看全部任务。

种子账号由 Java 后端启动时初始化，当前仅用于本地演示和验收。CP4 再补完整用户管理。

## 任务接口权限

普通业务接口现在要求登录：

- `POST /api/task/submit`
- `POST /api/task/{taskId}/correction-materials`
- `GET /api/task/list`
- `GET /api/task/{taskId}/status`
- `GET /api/task/{taskId}/result/applicant`
- `GET /api/task/{taskId}/result/reviewer`
- `POST /api/task/{taskId}/reviewer-action`

关键规则：

- 申请人提交任务时，后端把当前用户 ID 写入 `review_task.owner_user_id`。
- 申请人只能查看 `owner_user_id` 等于自己的任务和申请人结果。
- 审批人员只看到 `PARTIAL_SUCCESS`、`COMPLETED`、`FAILED` 这些 AI 初评后可处理的任务。
- `GET /api/task/{taskId}/result/reviewer` 只允许 `REVIEWER` 和 `ADMIN` 调用。
- 管理员可查看全部任务列表，用于演示和排障。
- 申请人列表页和申请人结果页会读取初审处理快照，展示退回补正、通过初审和转人工复核提醒。

## 补正材料补传接口

CP4-C 后，退回补正不再只是展示备注。申请人在自己的任务进入 `CORRECTION_REQUIRED` 后，可以在同一个 `taskId` 上补传一个或多个固定槽位材料：

- `POST /api/task/{taskId}/correction-materials`
- `Content-Type: multipart/form-data`

字段名与首次提交保持一致：

| multipart 字段 | 材料类型 |
|---|---|
| `applicationForm` | `APPLICATION_FORM` |
| `businessLicense` | `BUSINESS_LICENSE` |
| `idCard` | `ID_CARD` |

关键规则：

- 只有任务 owner 的 `APPLICANT` 可以补传；审批人员和管理员不能通过该申请人入口补传。
- 任务当前 `handling_status` 必须是 `CORRECTION_REQUIRED`。
- 至少上传一个文件，允许只替换其中一个材料槽位。
- 后端继续按首次提交规则校验扩展名：`jpg`、`jpeg`、`png`、`pdf`、`docx`。
- 新文件会覆盖 `material_slot (task_id, material_type)` 的当前输入；旧对象可以留在 RustFS/S3，但不再作为当前审查输入。
- 补传后清空当前初审处理快照、`knowledgePackVersion` 和旧结果占位，任务重新进入 Java -> Python FastAPI 审查链路。
- 如果 Python 调度失败，复用现有失败语义：任务进入 `FAILED`，并写入申请人/审批人员失败结果。

## 初审动作接口

CP3-F 增加审批人员初审动作接口：

- `POST /api/task/{taskId}/reviewer-action`

请求体：

```json
{
  "actionCode": "RETURN_FOR_CORRECTION",
  "remark": "请补充身份证有效期页。"
}
```

当前支持的动作码：

| 动作码 | 处理状态 | 含义 |
|---|---|---|
| `APPROVE_INITIAL_REVIEW` | `INITIAL_REVIEW_PASSED` | 通过初审。 |
| `RETURN_FOR_CORRECTION` | `CORRECTION_REQUIRED` | 退回补正；CP4-C 起申请人可通过补传接口提交补正材料。 |
| `TRANSFER_MANUAL_REVIEW` | `MANUAL_REVIEW_REQUIRED` | 转人工复核。 |

申请人可见的处理状态提醒：

| 处理状态 | 申请人侧提示 |
|---|---|
| `INITIAL_REVIEW_PASSED` | 申请已通过初审，请留意后续办理通知。 |
| `CORRECTION_REQUIRED` | 申请已退回补正，请进入结果页补传材料。 |
| `MANUAL_REVIEW_REQUIRED` | 申请已转人工复核，请等待进一步处理。 |

关键规则：

- 只有 `REVIEWER` 和 `ADMIN` 可以提交初审动作。
- 只能处理 AI 初评后进入 `PARTIAL_SUCCESS` 或 `COMPLETED` 的任务。
- 必须已经存在审批人员视图的 AI 结果，不能绕过 AI 初评直接提交动作。
- 同一任务 CP3 内只允许提交一次初审动作；重复或陈旧提交返回业务 `409`。
- 接口不改变 `ProcessingStatus`，处理结果写入初审快照和操作日志，供申请人和审批人员结果接口展示。

## Java 主动调度 Python FastAPI

CP3.5-B 之后，`POST /api/task/submit` 不再只依赖 Worker 轮询。默认配置下，Java 在创建 `review_task` 和三类材料槽位后，会主动调用 Python FastAPI：

- Python 地址来自 `water-approval.ai-service.base-url`。
- 调度路径来自 `water-approval.ai-service.review-task.path`，默认 `/api/review/tasks`。
- 如果配置了 `water-approval.ai-service.internal-token`，Java 会在调度请求中携带 `X-Internal-Token`。
- Java 发送的 payload 使用 camelCase，包含 `taskId`、`sessionId`、`idempotencyKey` 和三类材料槽位；缺失材料也会以 `uploaded=false` 出现在 `materials` 中。

调度成功后，Java 将任务状态写为 `PROCESSING`，避免旧的 Worker 轮询路径再次领取同一个任务。前端继续通过 Java 的状态和结果接口轮询，不直接访问 Python。

如果 Python 不可用、鉴权失败、超时、限流或返回 5xx，Java 会把任务写为 `FAILED`，并写入申请人/审查人两类失败结果：

- 申请人结果说明“AI审查服务调度失败，未生成智能审查结论”。
- 审查人结果包含失败分类，例如 `AUTH_ERROR`、`TIMEOUT`、`RATE_LIMIT`、`UPSTREAM_5XX` 或 `SYSTEM_ERROR`。
- 失败时不会生成草稿审查意见，也不会伪造成 `COMPLETED` 或 `PARTIAL_SUCCESS`。

当 `water-approval.ai-service.review-task.enabled=false` 时，Java 保留旧的 `SUBMITTED` 状态，允许 Worker 通过 `GET /api/task/pending` 继续处理任务。该模式主要用于普通单元测试或兼容性回退。

## Worker 回调边界

Python Worker 接口保持独立的内部 token 边界，不要求网页登录态：

- `GET /api/task/pending`
- `PUT /api/task/{taskId}/status`
- `PUT /api/task/{taskId}/result`
- `GET /api/material/download?key=<storageKey>`

这些接口由 `X-Worker-Token` 保护；当配置了 `WORKER_TOKEN` 时，Worker 必须携带相同 token。网页登录 token 和 Worker token 不混用。
