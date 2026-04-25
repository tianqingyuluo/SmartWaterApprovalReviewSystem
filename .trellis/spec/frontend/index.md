# Frontend Development Guidelines

> Best practices for frontend development in this project.

---

## Overview

This directory contains guidelines for frontend development. Fill in each file with your project's specific conventions.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Partial |
| [Component Guidelines](./component-guidelines.md) | Component patterns, props, composition | Partial |
| [Hook Guidelines](./hook-guidelines.md) | Custom hooks, data fetching patterns | Partial |
| [State Management](./state-management.md) | Local state, global state, server state | Partial |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Partial |
| [Type Safety](./type-safety.md) | Type patterns, validation | Partial |
| [SmartWater MVP Visibility](./smartwater-mvp-visibility.md) | Dual-page MVP, applicant/reviewer visibility, status display, canonical enums | Active |

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

Before frontend work, read:

- [SmartWater MVP Visibility](./smartwater-mvp-visibility.md)
- [Type Safety](./type-safety.md)
- [State Management](./state-management.md)
- [Component Guidelines](./component-guidelines.md)

If the frontend change touches API DTOs or task status, also read:

- [Backend SmartWater MVP Contracts](../backend/smartwater-mvp-contracts.md)

