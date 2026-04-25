# 团队协作纪律

> 适用于 SmartWater 项目的 Trellis 任务分派、分支管理、代码审核和阶段集成。

---

## 目标

让团队围绕 Trellis 子任务并行开发，避免长期个人分支、混合提交和跨模块契约漂移。

---

## 分支模型

| 分支类型 | 示例 | 用途 |
|---|---|---|
| 稳定主分支 | `main` | 只接收已验收的阶段成果 |
| MVP 集成分支 | `mvp/smartwater` 或 `develop/smartwater-mvp` | MVP 阶段的统一集成目标 |
| 短任务分支 | `task/smartwater-mvp-domain-contract` | 单个 Trellis 子任务的开发分支 |

### 纪律

* 不维护长期个人 `dev` 分支。
* 一个 Trellis 子任务对应一个短任务分支，通常对应一个 PR。
* 任务分支从 MVP 集成分支创建，不直接从个人旧分支继续开发。
* 任务完成后合回 MVP 集成分支；MVP 整体验收后再合回 `main`。
* 不把多个无关子任务混在同一个任务分支里。

---

## Trellis 身份与任务分派

* 团队先约定稳定的 Trellis 开发者 ID，例如 `alice`、`bob`、`chenyu`。
* 每个成员在本机初始化同名身份，确保本地 `.trellis/.developer` 的 `name` 与任务 `assignee` 完全一致。
* `.trellis/.developer` 和 `.trellis/.current-task` 是本地状态，不提交。
* `.trellis/tasks/**` 是团队共享任务状态，需要随任务规划和分派一起提交。
* `.trellis/workspace/<developer>/` 是成员工作记录，可随 session/journal 更新提交。

---

## 标准执行流程

1. 负责人从 MVP 集成分支拉取最新代码。
2. 负责人确认自己的任务：`python3 ./.trellis/scripts/task.py list --mine`。
3. 负责人启动任务：`python3 ./.trellis/scripts/task.py start <task-dir>`。
4. 从 MVP 集成分支创建短任务分支：`task/<task-name>`。
5. 按子任务 `prd.md` 和 `implement.jsonl` 实现。
6. 如需技术调研，将结果写入该任务的 `research/*.md`。
7. 提交 PR 到 MVP 集成分支。
8. 审核通过后合并，并更新任务状态或父任务说明。

---

## PR 审核标准

每个 PR 至少回答以下问题：

* 是否只完成了一个 Trellis 子任务？
* 是否满足该子任务 `prd.md` 的 `Acceptance Criteria`？
* 是否遵守父任务定义的 MVP 边界和模块职责？
* 是否跑过必要的测试、lint 或 type-check？
* 是否影响跨模块契约；如果影响，是否同步更新相关 PRD/spec？
* 是否没有引入密钥、个人本地文件或无关 workspace 状态？

---

## Git 提交消息纪律

每次 Git 提交必须使用“英文前缀 + 中文说明”的格式：

```text
<type>: <中文提交说明>
```

### 允许的英文前缀

| Prefix | 用途 |
|---|---|
| `feat` | 新功能、能力新增 |
| `fix` | 缺陷修复 |
| `docs` | 文档、PRD、spec、说明材料 |
| `spec` | Trellis/spec 规范、契约、流程规则 |
| `refactor` | 不改变行为的重构 |
| `test` | 测试新增或调整 |
| `chore` | 构建、依赖、任务元数据、仓库维护 |
| `style` | 格式化、样式、无逻辑变化 |

### 示例

正确：

```text
spec: 规范团队提交消息格式
docs: 归档领域契约任务
feat: 增加材料提交接口
fix: 修正任务状态流转校验
```

错误：

```text
更新一下
修正领域契约审核问题
commit message convention
```

### 历史提交改写规则

* 未推送的本地提交可以用 `git commit --amend` 或 `git rebase -i` 改成规范格式。
* 已推送到共享分支或已合并 PR 的提交，默认不改写历史，避免破坏其他成员本地分支和 PR 基线。
* 如果确实需要改写共享历史，必须先由团队全员确认，再统一执行 force-push 和本地分支重置。
* 对已经合并的非规范提交，优先通过新增规范提交补充说明，不为了格式单独重写历史。

---

## 合并纪律

* P0 契约任务优先合并，尤其是域模型、任务状态、DTO/schema 和跨服务边界。
* 后端、Python Worker、前端可以并行，但不得各自发明不兼容的数据结构。
* 发生契约变更时，先更新契约任务或父任务 PRD，再通知受影响任务。
* MVP 集成分支必须保持可构建、可运行或至少不破坏已通过的质量门禁。
* MVP 全部子任务完成后，必须做端到端验收：上传材料 → 生成任务 ID → 异步处理 → 查询结果页。

---

## 任务归档纪律

* 子任务可以在完成验收、PR 合并到 MVP 集成分支后单独归档。
* 父任务在仍有必要子任务处于 `planning`、`in_progress` 或待验收状态时，不应提前归档。
* 父任务作为阶段看板保留到所有 MVP 子任务完成、端到端验收通过、必要 PRD/spec 更新完成之后。
* 归档顺序应为：子任务逐个验收并归档 → MVP 集成分支端到端验收 → 更新父任务总结 → 最后归档父任务。
* 如果某个子任务被取消或移出 MVP 范围，必须先在父任务 PRD 记录原因，再解除或调整父子任务关系。

---

## Wrong vs Correct

### Wrong

* 每个人长期维护 `dev-alice`、`dev-bob`，最后一次性向 `main` 合并。
* 一个 PR 同时改后端提交 API、前端页面、AI Worker 和无关格式化。
* 子任务未通过验收标准就合并，只在聊天里说明“后续再补”。

### Correct

* 每个子任务从 MVP 集成分支创建短任务分支。
* 一个 PR 对应一个 Trellis 子任务，并在 PR 描述里链接任务目录。
* 合并前逐项核对 `Acceptance Criteria`，必要时更新 PRD、research 或 spec。
