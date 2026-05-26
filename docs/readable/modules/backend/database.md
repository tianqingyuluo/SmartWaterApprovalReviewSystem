# 后端数据库说明

## 当前核心表

Java 后端当前使用四张核心业务表：

| 表 | 用途 |
|---|---|
| `review_task` | 审核任务主表，保存任务 ID、会话 ID、归属申请人、状态和知识包版本。 |
| `material_slot` | 固定三类材料槽位的上传记录。 |
| `review_result` | 保存申请人视图和审批人员视图两类 AI 初评结果 JSON。 |
| `review_action_log` | 保存审批人员初审动作操作日志。 |
| `user_account` | CP3 最小登录账号与角色。 |

## CP3 新增字段与表

`review_task.owner_user_id` 用于记录任务归属申请人。新提交任务必须写入当前登录用户 ID；历史数据允许为空，但无法作为申请人“我的申请”结果出现。

`user_account` 保存本地演示账号：

- `username`：登录名，唯一。
- `display_name`：显示名称。
- `password_hash`：BCrypt 密码哈希。
- `role_code`：`APPLICANT`、`REVIEWER` 或 `ADMIN`。
- `enabled`：账号是否启用。

CP3-F 增加初审处理快照和日志：

- `review_task.reviewer_action_code`：审批动作码。
- `review_task.handling_status`：处理状态，例如 `INITIAL_REVIEW_PASSED`、`CORRECTION_REQUIRED`、`MANUAL_REVIEW_REQUIRED`。
- `review_task.reviewer_remark`：审批人员备注。
- `review_task.reviewer_user_id`：提交动作的审批人员或管理员 ID。
- `review_task.reviewer_action_at`：动作提交时间。
- `review_action_log`：每次有效初审动作的操作日志，包含任务、操作者、动作、处理状态、备注和时间。

## 约束

- `review_task.task_id` 和 `review_task.session_id` 保持唯一。
- `material_slot (task_id, material_type)` 保持唯一，保证每类材料一个槽位。
- `review_result (task_id, result_type)` 保持唯一，重复 Worker 回写会更新已有申请人/审批人员结果。
- `review_action_log` 只记录成功落库的初审动作；重复动作在写入日志前返回业务 `409`。
- `user_account.username` 保持唯一。
