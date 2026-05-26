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

关键规则：

- 申请人提交任务时，后端把当前用户 ID 写入 `review_task.owner_user_id`。
- 申请人只能查看 `owner_user_id` 等于自己的任务和申请人结果。
- 审批人员只看到 `PARTIAL_SUCCESS`、`COMPLETED`、`FAILED` 这些 AI 初评后可处理的任务。
- `GET /api/task/{taskId}/result/reviewer` 只允许 `REVIEWER` 和 `ADMIN` 调用。
- 管理员可查看全部任务列表，用于演示和排障。

## Worker 回调边界

Python Worker 接口保持独立的内部 token 边界，不要求网页登录态：

- `GET /api/task/pending`
- `PUT /api/task/{taskId}/status`
- `PUT /api/task/{taskId}/result`
- `GET /api/material/download?key=<storageKey>`

这些接口由 `X-Worker-Token` 保护；当配置了 `WORKER_TOKEN` 时，Worker 必须携带相同 token。网页登录 token 和 Worker token 不混用。
