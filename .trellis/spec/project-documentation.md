# Project Documentation Discipline

> Applies to human-readable project documentation, development logs, and the
> boundary between `docs/readable/**`, `.trellis/spec/**`, `.trellis/tasks/**`,
> and personal Trellis journals.

---

## Goal

Keep project knowledge durable while implementation moves quickly.

Every task should leave behind enough readable context for another teammate to
understand what changed, how to use it, and what follow-up work remains without
reconstructing the work from chat history, local AI sessions, or commit diffs.

---

## Documentation Areas

### Human-Readable Project Docs

Team-authored explanatory documentation for people lives under:

```text
docs/readable/
```

This directory is for current project understanding:

- how the system is shaped
- how modules work
- how to run and configure the project
- what changed during development
- what decisions were made and why

It is not the place for raw source material, personal notes, or AI-only rules.

Language rule:

- All team-authored files under `docs/readable/**` must be written in Chinese.
- English technical identifiers, API paths, enum values, class names, commands,
  branch names, file paths, and error names may remain in English.
- Do not mix long English explanations into readable project docs unless quoting
  an upstream API, command output, or external source.

### Trellis Specs

Executable rules and coding contracts live under:

```text
.trellis/spec/
```

Use specs for rules that AI agents and developers must follow, such as:

- API and DTO contracts
- state transitions
- module boundaries
- branch and PR discipline
- documentation maintenance rules
- forbidden patterns and quality gates

If a readable doc contains a rule that future implementation must obey, mirror
or summarize that rule in `.trellis/spec/**`.

### Trellis Tasks

Task planning and acceptance criteria live under:

```text
.trellis/tasks/
```

Use task files for:

- PRD and task scope
- owner, assignee, status, branch metadata
- task-specific research artifacts
- implementation and check context

Do not use task PRDs as the only durable project documentation after a feature
lands. Important project behavior must be promoted into `docs/readable/**` and,
when it becomes enforceable, `.trellis/spec/**`.

### Personal Journals

Personal AI session history lives under:

```text
.trellis/workspace/<developer>/
```

These journals are useful session records, but they are not the project change
log and do not replace `docs/readable/dev-log/**`.

### Raw Reference Material

External or original reference material remains in existing source-material
folders, for example:

```text
docs/参考资料/
```

Do not mix raw source files with team-authored readable project docs.

---

## Required Directory Layout

Use this layout for human-readable project docs:

```text
docs/
  readable/
    README.md

    dev-log/
      index.md
      YYYY-MM.md

    architecture/
      overview.md
      decisions/
        YYYY-MM-DD-short-decision-title.md

    modules/
      backend/
        overview.md
        api.md
        config.md
        storage.md
        database.md

      worker/
        overview.md
        api.md
        config.md
        failure-handling.md
        adapters.md

      frontend/
        overview.md
        pages.md
        api-contract.md
        state-and-visibility.md

    operations/
      local-dev.md
      env-vars.md
      troubleshooting.md
```

Create files lazily when the first real content exists. Do not create empty
placeholder documents unless they contain a clear purpose, owner expectation, or
initial known content.

---

## Directory Responsibilities

### `docs/readable/README.md`

The entry point and navigation map.

Must include:

- what this documentation tree contains
- links to the main sections
- where raw reference material lives
- where enforceable specs live

### `docs/readable/dev-log/`

The project-level development change log.

Purpose:

- record what changed by task or PR
- capture verification performed
- record known issues and follow-ups
- make the project timeline readable without opening every PR

Rules:

- Use one file per month: `YYYY-MM.md`.
- Add entries by PR or task, not by individual commit.
- Append new entries. Do not rewrite history except for typo fixes.
- If older information was wrong, add a `Correction` line under the relevant
  entry or add a later entry that references it.

### `docs/readable/architecture/`

System-level explanation.

Use it for:

- system overview
- cross-service flow
- major boundaries between backend, Worker, frontend, storage, and AI providers
- architecture decisions that affect multiple modules

Decision records live under `architecture/decisions/`.

Decision records should be short and dated:

```text
YYYY-MM-DD-short-decision-title.md
```

### `docs/readable/modules/`

Module-level explanation.

Use it for docs that explain how a specific module currently works.

Examples:

- backend API and persistence behavior
- Worker polling and writeback behavior
- frontend page state and visibility behavior

Do not place module docs directly under `docs/readable/`. Keep them under:

```text
docs/readable/modules/<module>/
```

### `docs/readable/operations/`

Operational instructions for people.

Use it for:

- local development startup
- environment variables
- integration setup
- troubleshooting
- common commands

Do not put implementation contracts here. If a command, environment variable, or
deployment requirement is an enforceable rule, mirror it in `.trellis/spec/**`.

---

## Finish-Time Documentation Gate

When finishing any task, the AI and human owner must review documentation before
calling the work complete.

This gate applies during Phase 3 and `/finish-work`, after implementation and
quality checks, before task archival.

### Required Questions

For every task, answer these questions:

1. Did this task change user-visible behavior, API behavior, data flow, module
   responsibilities, configuration, deployment, or troubleshooting knowledge?
2. Did this task add, remove, or modify a backend, Worker, or frontend contract?
3. Did this task introduce a known limitation, follow-up, or operational gotcha?
4. Did this task produce a PR or meaningful milestone that future teammates
   should see in the project timeline?
5. Did this task create a rule that future AI agents must enforce?

### Required Actions

Use the answers to update docs:

| Condition | Required update |
|---|---|
| Any task reaches PR or merge-ready state | Add/update `docs/readable/dev-log/YYYY-MM.md` |
| API changed | Update `docs/readable/modules/<module>/api.md` |
| Config or env changed | Update `docs/readable/modules/<module>/config.md` or `docs/readable/operations/env-vars.md` |
| Database/schema changed | Update `docs/readable/modules/backend/database.md` |
| Storage behavior changed | Update `docs/readable/modules/backend/storage.md` |
| Worker polling, writeback, adapters, or failure behavior changed | Update `docs/readable/modules/worker/api.md`, `adapters.md`, or `failure-handling.md` |
| Frontend page, state, API use, or visibility changed | Update `docs/readable/modules/frontend/pages.md`, `api-contract.md`, or `state-and-visibility.md` |
| Cross-module design changed | Update `docs/readable/architecture/overview.md` or add an ADR |
| Enforceable rule changed | Update `.trellis/spec/**` |

If no readable docs need changes, say so explicitly in the final task summary
and explain why.

All readable documentation updates produced by this gate must be written in
Chinese, except for technical identifiers and quoted source text.

---

## Development Log Entry Contract

Each development log entry should use this shape:

```markdown
## YYYY-MM-DD - <short task or PR title>

- Branch: `<branch-name>`
- PR: #<number or N/A>
- Owner: `<trellis-developer-id>`
- Related tasks:
  - `.trellis/tasks/<task-dir>`
- Summary:
  - <what changed in project terms>
- Contract changes:
  - <API, schema, status, config changes, or "None">
- Documentation updates:
  - <docs/readable path(s), or "None">
- Verification:
  - <commands/checks run and result>
- Known issues:
  - <open risks, or "None">
- Follow-ups:
  - <next tasks, or "None">
```

Keep entries concise. The development log is a timeline, not a full design doc.
Link to module docs, architecture docs, PRs, and Trellis task directories for
details.

Entries must be written in Chinese. Keep field labels stable, but write the
actual descriptions, known issues, and follow-ups in Chinese.

---

## Architecture Decision Record Contract

Use an ADR when a decision affects more than one module or changes future
implementation direction.

ADR files under `docs/readable/architecture/decisions/` should use:

```markdown
# YYYY-MM-DD - <Decision Title>

## Status

Accepted | Proposed | Superseded

## Context

<problem and constraints>

## Decision

<chosen approach>

## Consequences

<trade-offs, follow-ups, and affected modules>

## Links

- PR: #<number>
- Task: `.trellis/tasks/<task-dir>`
- Spec: `.trellis/spec/<path>`
```

If an ADR becomes enforceable, add or update the relevant `.trellis/spec/**`
file in the same PR.

---

## Wrong vs Correct

### Wrong

- A PR changes backend API but only updates chat messages.
- A Worker failure behavior changes but `docs/readable/modules/worker/` remains
  stale.
- A cross-service DTO changes in code but `.trellis/spec/backend/` still
  documents the old shape.
- Personal `.trellis/workspace/<developer>/journal` is treated as the project
  change log.
- Module docs are placed directly under `docs/readable/backend/` instead of
  `docs/readable/modules/backend/`.

### Correct

- A PR updates code, `docs/readable/dev-log/YYYY-MM.md`, and the affected module
  doc.
- Contract changes update both human-readable docs and `.trellis/spec/**`.
- A finish-work pass explicitly says which readable docs were updated, or why no
  readable docs were needed.
- Architecture decisions that affect multiple modules are captured in
  `docs/readable/architecture/decisions/`.

---

## Review Checklist

Reviewers should check:

- Does the PR include a development log entry?
- If public or internal APIs changed, is the relevant module API doc updated?
- If config or env changed, is the operations or module config doc updated?
- If cross-service contracts changed, are readable docs and `.trellis/spec/**`
  synchronized?
- Are docs placed under the correct directory?
- Are readable docs written in Chinese, except for technical identifiers and
  quoted source text?
- Is the documentation concise enough to maintain, but detailed enough for a new
  teammate to continue work?
