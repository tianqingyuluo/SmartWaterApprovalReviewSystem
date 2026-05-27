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
| `RETURN_FOR_CORRECTION` | `CORRECTION_REQUIRED` | 退回补正，只产生补正要求，不在 CP3 内完成重传。 |
| `TRANSFER_MANUAL_REVIEW` | `MANUAL_REVIEW_REQUIRED` | 转人工复核。 |

关键规则：

- 只有 `REVIEWER` 和 `ADMIN` 可以提交初审动作。
- 只能处理 AI 初评后进入 `PARTIAL_SUCCESS` 或 `COMPLETED` 的任务。
- 必须已经存在审批人员视图的 AI 结果，不能绕过 AI 初评直接提交动作。
- 同一任务 CP3 内只允许提交一次初审动作；重复或陈旧提交返回业务 `409`。
- 接口不改变 `ProcessingStatus`，处理结果写入初审快照和操作日志，供申请人和审批人员结果接口展示。

## Worker 回调边界

Python Worker 接口保持独立的内部 token 边界，不要求网页登录态：

- `GET /api/task/pending`
- `PUT /api/task/{taskId}/status`
- `PUT /api/task/{taskId}/result`
- `GET /api/material/download?key=<storageKey>`

这些接口由 `X-Worker-Token` 保护；当配置了 `WORKER_TOKEN` 时，Worker 必须携带相同 token。网页登录 token 和 Worker token 不混用。
