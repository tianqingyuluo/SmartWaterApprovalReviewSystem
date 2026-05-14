# Journal - tianqingyuluo (Part 1)

> AI development session journal
> Started: 2026-04-20

---



## Session 1: SmartWater roadmap planning checkpoint

**Date**: 2026-04-24
**Task**: SmartWater roadmap planning checkpoint
**Branch**: `main`

### Summary

Kept planning state for smartwater-architecture-roadmap. Confirmed MVP as a dual-page demo app with applicant submission plus AI precheck, reviewer read-only result page, async OCR+AI pipeline, GLM OCR, separate domestic reasoning model, real DB+object storage, fixed upload slots, image/PDF only, single applicant and single water source. Next unresolved product question: whether MVP should auto-detect 'no permit required' cases.

### Main Changes

(Add details)

### Git Commits

(No commits - planning session)

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 2: 完成 SmartWater MVP 领域契约

**Date**: 2026-04-25
**Task**: 完成 SmartWater MVP 领域契约
**Branch**: `mvp/smartwater`

### Summary

合并 PR #1，完成 MVP 领域模型、材料槽位、状态机、API/Worker 契约与下游边界设计。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `0f536b7` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: 归档 Git 提交消息规范任务

**Date**: 2026-04-25
**Task**: 归档 Git 提交消息规范任务
**Branch**: `mvp/smartwater`

### Summary

确认提交消息规范已落地到团队协作 spec，并归档 git-commit-message-convention 任务。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `30814db` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 4: 完成审核推理模型选型

**Date**: 2026-04-25
**Task**: 完成审核推理模型选型
**Branch**: `mvp/smartwater`

### Summary

完成国内审核推理模型调研，用户确认 Qwen 为主选、DeepSeek 为备选，并固化 ReviewReasoningAdapter 契约、结构化输出约束和失败处理。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `9452938` | (see git log) |
| `eaac0f3` | (see git log) |
| `60084bf` | (see git log) |
| `d0f26b8` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 5: 法规知识包 MVP 收尾

**Date**: 2026-05-05
**Task**: 法规知识包 MVP 收尾
**Branch**: `task/smartwater-regulation-knowledge-pack-mvp`

### Summary

归档 PR6 法规知识包子任务，记录知识包与 Worker/Java 回写契约对齐结果。

### Main Changes

- Archived `.trellis/tasks/04-24-smartwater-regulation-knowledge-pack-mvp` to `.trellis/tasks/archive/2026-05/`.
- Recorded PR #6 contract alignment after merging the PR5/MVP baseline into the knowledge-pack branch.
- Updated readable documentation for the knowledge pack version writeback and `basisRefs` validation behavior.

### Git Commits

| Hash | Message |
|------|---------|
| `8f1fada` | fix: 对齐法规知识包与Worker回写契约 |

### Testing

- [OK] `uv run python -m unittest discover -s tests -v` passed, 15 tests.
- [OK] `uv run python -m compileall main.py src tests knowledge_pack` passed.
- [OK] `./mvnw test` passed in non-sandbox environment, 47 tests.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 6: Wrap up OCR model selection fix

**Date**: 2026-05-11
**Task**: Wrap up OCR model selection fix
**Branch**: `mvp/smartwater`

### Summary

Switched Worker OCR from glm-4v chat completions to the official GLM OCR layout_parsing API, added regression coverage and docs/spec updates, tracked the Trellis task context and upgraded Trellis workflow/session handling, and checked in the Worker uv lockfile plus typing/test cleanup.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3c95685` | (see git log) |
| `444248f` | (see git log) |
| `219000f` | (see git log) |
| `610f4fb` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 7: 前端 Tailwind 样式体系重构

**Date**: 2026-05-13
**Task**: 前端 Tailwind 样式体系重构
**Branch**: `mvp/smartwater`

### Summary

接入 TailwindCSS/PostCSS，迁移三页审核流程与核心组件样式，沉淀前端样式规范并通过 frontend test/build。

### Main Changes

- 接入 TailwindCSS 3、PostCSS 和 Autoprefixer，并提交 `frontend/package-lock.json` 依赖锁定。
- 新增 `frontend/tailwind.config.js`，沉淀 SmartWater 后台管理界面的颜色、阴影、圆角、字体和动画 token。
- 将申请列表、新建申请、AI 初审结果三页，以及核心通用/业务组件迁移为 Tailwind utility class 与少量 `sw-*` 共享 class。
- 收敛 `frontend/src/style.css`，保留 Tailwind 入口、基础全局规则和少量共享组件样式。
- 新增 `.trellis/spec/frontend/styling-guidelines.md`，并在 `docs/readable/dev-log/2026-05.md` 记录本次样式体系重构。

### Git Commits

| Hash | Message |
|------|---------|
| `e1723d8` | (see git log) |

### Testing

- [OK] `cd frontend && npm run test` 通过，2 files / 8 tests。
- [OK] `cd frontend && npm run build` 通过。
- [OK] `git diff --check` 通过。

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 8: CP1-D 证据文档整理

**Date**: 2026-05-14
**Task**: CP1-D 证据文档整理
**Branch**: `v1`

### Summary

完成 CP1-D 任务：建立 CP1 评分点到 MVP 证据映射总表，整理本地启动步骤、Git 分工与提交证明，更新开发日志。覆盖 19 个评分项，8 项待补齐已关联后续子任务。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `fdd4138` | (see git log) |
| `c576c5d` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete
