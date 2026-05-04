# Backend Development Guidelines

> Best practices for backend development in this project.

---

## Overview

This directory contains guidelines for backend development. Fill in each file with your project's specific conventions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Partial |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | Partial |
| [Error Handling](./error-handling.md) | Error types, handling strategies | Partial |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, test/CI gates, forbidden patterns | Active |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | Partial |
| [SmartWater MVP Contracts](./smartwater-mvp-contracts.md) | Cross-service domain enums, task states, material storage, visibility boundaries | Active |
| [Review Reasoning Adapter](./review-reasoning-adapter.md) | Qwen/DeepSeek adapter, schema output, retries, redacted logging | Active |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals)
2. Include **code examples** from your codebase
3. List **forbidden patterns** and why
4. Add **common mistakes** your team has made

The goal is to help AI assistants and new team members understand how YOUR project works.

---

**Language**: All documentation should be written in **English**.


## Pre-Development Checklist

Before backend, Python Worker, or cross-service work, read:

- [SmartWater MVP Contracts](./smartwater-mvp-contracts.md)
- [Quality Guidelines](./quality-guidelines.md)
- [Review Reasoning Adapter](./review-reasoning-adapter.md) when touching AI review reasoning or Worker integration
- [Error Handling](./error-handling.md)
- [Logging Guidelines](./logging-guidelines.md)
- [Database Guidelines](./database-guidelines.md) when adding persistence
