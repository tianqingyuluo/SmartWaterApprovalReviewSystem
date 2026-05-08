# Frontend Development Guidelines

> SmartWater MVP 前端双页应用的项目规范入口。

---

## 概述

当前前端是一个 Vue 3 + Vite + TypeScript 的双页应用：

- `ApplicantPage.vue` 负责申请人材料提交、轮询状态和预检查结果展示
- `ReviewerPage.vue` 负责审批人员结果查询与完整结果展示

本目录记录的不是通用 Vue 模板，而是当前 MVP 的真实目录、状态管理和类型约定。

---

## Guidelines Index

| Guide | Description | Status |
|---|---|---|
| [Directory Structure](./directory-structure.md) | Current `src/` layout, page/component/api/type organization | Active |
| [Component Guidelines](./component-guidelines.md) | Page orchestration vs presentational components, shared primitives | Active |
| [Hook Guidelines](./hook-guidelines.md) | `usePolling` and other composables | Active |
| [State Management](./state-management.md) | Page-local refs/reactive state, future Pinia boundary | Active |
| [Quality Guidelines](./quality-guidelines.md) | Build/test gates, forbidden patterns, contract regression tests | Active |
| [Type Safety](./type-safety.md) | Canonical SmartWater DTOs, view models, and union types | Active |
| [SmartWater MVP Visibility](./smartwater-mvp-visibility.md) | Dual-page MVP, applicant/reviewer visibility, status display, canonical enums | Active |

---

## Usage Notes

- Update the relevant file when backend DTOs, task status labels, polling behavior, or component boundaries change.
- `src/api/task.ts` is the contract adapter layer; pages should consume view models, not raw backend DTOs.
- Keep human-facing project docs in `docs/readable/**` in Chinese; this spec may still use English filenames and code identifiers.

---

## Pre-Development Checklist

Before frontend work, read:

- [SmartWater MVP Visibility](./smartwater-mvp-visibility.md)
- [Type Safety](./type-safety.md)
- [State Management](./state-management.md)
- [Component Guidelines](./component-guidelines.md)
- [Quality Guidelines](./quality-guidelines.md)

If the change touches backend DTOs, status transitions or worker-facing result shape, also read:

- [Backend SmartWater MVP Contracts](../backend/smartwater-mvp-contracts.md)
