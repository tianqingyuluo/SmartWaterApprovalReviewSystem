# Migrate to v0.5.0-beta.11

## Goal

把当前仓库的 Trellis 工作流从“可能残留 0.4.x 迁移中间态”收敛到“确认已经符合 0.5.0-beta.11 约定，补齐缺口，并完成一次可验证的迁移检查”，避免后续实现阶段因命令、技能路径、子代理名称或 Codex hook 配置不一致而出现隐藏问题。

## What I Already Know

* 当前任务目录已存在，任务状态为 `planning`，标题为 `Migrate to v0.5.0-beta.11`。
* [`.trellis/.version`](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/.trellis/.version) 显示当前模板版本是 `0.5.0-beta.11`。
* 仓库内已存在 `trellis-*` 命名的 agent 与 skill 文件，例如 [`.codex/agents/trellis-implement.toml`](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/.codex/agents/trellis-implement.toml) 和 [`.agents/skills/trellis-brainstorm/SKILL.md`](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/.agents/skills/trellis-brainstorm/SKILL.md)。
* 未发现旧命名的 agent 文件 `implement` / `check` / `research`。
* 未发现 `.iflow/`、`.trellis/scripts/multi_agent/`、`worktree.yaml` 这类 0.4.x 已移除组件的本地遗留。
* 未发现仓库内实际使用已退役命令 `/record-session`、`/check-cross-layer`、`/parallel`、`/onboard`、`/create-command`、`/integrate-skill` 的位置；目前匹配只出现在本任务旧版 PRD 文本里。
* 当前任务目录已生成 `implement.jsonl` / `check.jsonl`，并已通过 `task.py validate` 校验。
* 项目级 [`.codex/config.toml`](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/.codex/config.toml#L1) 只负责提示；实际用户级 `~/.codex/config.toml` 已确认启用 `features.codex_hooks = true`。
* 本机 `trellis --version` 返回 `0.5.0-beta.11`。
* 项目级 [`.codex/hooks.json`](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/.codex/hooks.json#L1) 已存在 `SessionStart` 与 `UserPromptSubmit` hooks 配置。
* `trellis update --help` 显示支持 `--dry-run`、`--force`、`--skip-all`、`--create-new`、`--migrate`；若进入交互提示，默认回车可采用安全的 backup-rename 策略。

## Assumptions (Temporary)

* 当前仓库虽然已经呈现 `0.5.0-beta.11` 模板形态，但仍需要一次面向实际工作流的迁移审计和执行复验。
* 后续运行 `trellis update --migrate` / `trellis update` 更像是验证与补齐，而不是首次安装模板。

## Open Questions

* 无。当前范围与迁移提示处理策略都已确定。

## Requirements (Evolving)

* 明确当前仓库相对 Trellis `0.5.0-beta.11` 的真实状态：已迁移完成、部分完成、或仍有缺口。
* 检查迁移指南中高风险项在本仓库是否仍有遗留：
  retired commands、旧 agent 名称、旧 skill 路径、旧任务上下文文件路径、Codex hook 启用前提。
* 产出一份可执行的迁移结论，而不是只保留上游迁移说明摘录。
* 实际执行 `trellis update --migrate`，必要时继续执行 `trellis update` 作为二次复验。
* 如迁移后仍缺少任务上下文文件，执行 `task.py init-context` 补齐。
* 如 `trellis update --migrate` 遇到 “Modified by you” 提示，采用默认回车的 backup-rename 安全策略，优先保留现有本地改动。
* 记录执行结果、用户交互提示处理策略、后续清理项和复验步骤。

## Acceptance Criteria (Evolving)

* [x] 能清楚说明当前仓库与 `0.5.0-beta.11` 迁移要求相比还差哪些步骤：当前 Trellis 模板迁移本身已完成，剩余工作主要是后续业务开发阶段继续补足项目 spec 内容。
* [x] 已确认仓库内不存在 retired commands、旧 agent 命名、旧 skill 路径、旧多代理流水线或 `.iflow` 遗留。
* [x] 已执行 `trellis update --migrate` 并记录结果。
* [x] 已执行后续复验命令，确认达到 `Already up to date!` 状态。
* [x] 已明确并处理 `implement.jsonl` / `check.jsonl` 重新生成需求。
* [x] 已确认 Codex 用户级 `features.codex_hooks = true` 前提已满足。
* [x] 已按约定处理迁移冲突提示，未无意覆盖本地修改。
* [x] PRD 已记录最终选择的迁移范围和对应的验证标准。

## Definition of Done

* PRD 范围明确。
* 已完成迁移命令执行与复验，或明确记录阻塞原因。
* 如有代码或配置改动：相关检查通过。
* 如果迁移产生新的 Trellis 使用约定，后续进入 `trellis-update-spec` 判断是否需要固化。

## Research References

* 无。当前阶段基于本仓库现状、CLI 帮助信息和已写入的迁移说明进行梳理，暂不需要额外外部研究。

## Technical Approach

先完成仓库状态审计，再按实际结果执行迁移与复验：

* 运行 `trellis update --migrate`，如遇提示优先采用默认安全策略。
* 再运行 `trellis update` 验证是否已无进一步差异。
* 若当前任务缺少 `implement.jsonl` / `check.jsonl`，执行 `python3 ./.trellis/scripts/task.py init-context "$TASK_DIR" <type> --platform codex` 补齐上下文。
* 根据执行结果更新任务状态、风险和后续动作。

## Implementation Plan

* Step 1: 运行迁移前审计与 dry-run 级别检查，确认当前差异面。
* Step 2: 执行 `trellis update --migrate`，遇到提示采用默认 backup-rename 策略。
* Step 3: 执行 `trellis update` 做二次复验，确认是否已无剩余差异。
* Step 4: 为当前任务生成 `implement.jsonl` / `check.jsonl`，确保 Codex 子代理上下文可用。
* Step 5: 汇总结论、风险和后续动作，准备进入实现或收尾阶段。

## Decision (ADR-lite)

**Context**: 当前任务目录已存在，但 `prd.md` 主要是上游迁移指南原文，不足以指导本仓库的实施或验收。  
**Decision**: 将任务范围确定为“审计 + 执行”，先按当前仓库状态收敛真实问题，再实际运行迁移和复验命令；如遇冲突提示，使用默认 backup-rename 安全策略。  
**Consequences**: 会执行真实命令并可能产生文件变更，但能把“看起来已经迁移”与“经过验证确实完成迁移”区分开，同时避免无意覆盖本地修改。

## Out of Scope

* 当前业务代码（`java-services/`、`python-services/`）的功能开发。
* 与 Trellis 迁移无关的仓库初始化或产品功能设计。
* 未经确认就直接修改用户级 `~/.codex/config.toml`。

## Technical Notes

* 已执行 `python3 ./.trellis/scripts/task.py start .trellis/tasks/04-23-migrate-to-0.5.0-beta.11`，当前任务已激活。
* 已搜索 retired commands，未发现仓库内真实调用。
* 已检查 agent / skill 命名，当前仓库已采用 `trellis-*` 命名。
* 已检查 `.iflow/`、`multi_agent`、`worktree.yaml`，未发现遗留。
* 已确认本机 `trellis` 版本为 `0.5.0-beta.11`。
* 已确认项目级 hooks 文件存在，且用户级 Codex 配置已启用 `features.codex_hooks = true`。
* 用户已确认：如遇“Modified by you”提示，采用默认回车的 backup-rename 安全策略。
* 已执行 `trellis update --dry-run --migrate`，结果为 `Already up to date!`。
* 已执行 `trellis update --migrate`，结果为 `Already up to date!`，未出现需要处理的冲突提示。
* 已执行 `trellis update`，结果为 `Already up to date!`。
* 已执行 `python3 ./.trellis/scripts/task.py init-context .trellis/tasks/04-23-migrate-to-0.5.0-beta.11 fullstack --platform codex`，生成 `implement.jsonl` 与 `check.jsonl`。
* 已执行 `python3 ./.trellis/scripts/task.py validate .trellis/tasks/04-23-migrate-to-0.5.0-beta.11`，校验通过。

## Execution Result

当前仓库的 Trellis 迁移状态已验证为完成状态：

* 模板版本与 CLI 版本均为 `0.5.0-beta.11`。
* 迁移 dry-run、真实 migrate、普通 update 三条路径都返回 `Already up to date!`。
* 未发现旧版命令、旧 agent 命名、旧 skill 路径、`.iflow`、`multi_agent`、`worktree.yaml` 等遗留项。
* 当前任务缺失的执行上下文文件已补齐并通过校验。

## Quality Verification

* 本次变更仅涉及 Trellis 任务文档、任务上下文文件和当前任务指针，没有修改业务代码。
* 因未变更业务实现，项目级 lint、type-check、tests 不属于本次迁移验收的有效信号，故未额外执行。
* 对本次任务本身已执行的有效检查包括：
  `trellis update --dry-run --migrate`、
  `trellis update --migrate`、
  `trellis update`、
  `task.py init-context`、
  `task.py validate`。

## Spec Update Judgment

* 本次任务没有发现需要写入 `.trellis/spec/` 的新实现约束或跨层契约。
* 当前 `.trellis/spec/backend/` 与 `.trellis/spec/frontend/` 仍是占位模板，这是现状记录，不是本次迁移新增知识，因此本次不更新 spec。

## Remaining Risks / Follow-up

* 本次任务验证的是 Trellis 工作流迁移状态，不包含业务代码层面的 lint、type-check、tests。
* `.trellis/spec/backend/` 与 `.trellis/spec/frontend/` 目前仍是占位模板；这不影响本次迁移结果，但会影响后续 AI 执行时可获得的项目约束质量。
* 任务 `status` 当前仍显示为 `planning`；如果接下来继续实际开发或准备归档，需要按 Trellis 流程进入后续阶段。
