# Backend Development Guidelines

> SmartWater Java backend、Python Worker 与跨服务后端边界的项目规范入口。

---

## Overview

This directory contains SmartWater backend conventions derived from the current MVP implementation. Prefer the concrete rules here over generic Spring/MyBatis/Python habits.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Actual Java service / Python Worker layout, package boundaries, storage abstraction | Active |
| [Database Guidelines](./database-guidelines.md) | review_task/material_slot/review_result schema, MyBatis-Plus usage, schema sync rules | Active |
| [Error Handling](./error-handling.md) | `R<T>` contract, worker token failure, status transition errors, binary download boundary | Active |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, test/CI gates, forbidden patterns | Active |
| [Logging Guidelines](./logging-guidelines.md) | Task, storage, token and adapter logging guardrails | Active |
| [SmartWater MVP Contracts](./smartwater-mvp-contracts.md) | Cross-service domain enums, task states, material storage, visibility boundaries | Active |
| [Review Reasoning Adapter](./review-reasoning-adapter.md) | Qwen/DeepSeek adapter, schema output, retries, redacted logging | Active |

---

## Usage Notes

- Treat these files as executable project contracts, not style suggestions.
- When Java API shape, Worker writeback schema, storage boundary, or database schema changes, update the relevant spec in the same task.
- `docs/readable/**` human-facing project docs are maintained in Chinese; `.trellis/spec/**` may stay bilingual where existing content already mixes English headings with Chinese rules.


## Pre-Development Checklist

Before backend, Python Worker, or cross-service work, read:

- [SmartWater MVP Contracts](./smartwater-mvp-contracts.md)
- [Quality Guidelines](./quality-guidelines.md)
- [Review Reasoning Adapter](./review-reasoning-adapter.md) when touching AI review reasoning or Worker integration
- [Error Handling](./error-handling.md)
- [Logging Guidelines](./logging-guidelines.md)
- [Database Guidelines](./database-guidelines.md) when adding persistence
