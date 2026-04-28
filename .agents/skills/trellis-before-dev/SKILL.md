---
name: trellis-before-dev
description: "Discovers and injects project-specific coding guidelines from .trellis/spec/ before implementation begins. Reads spec indexes, pre-development checklists, and shared thinking guides for the target package. Use when starting a new coding task, before writing any code, switching to a different package, or needing to refresh project conventions and standards."
---

Read the relevant development guidelines before starting your task.

Execute these steps:

0. **Check task branch discipline**:
   - Confirm a Trellis task is active.
   - Confirm Git is on a short task branch (`task/<task-name>`), not `main`, `mvp/smartwater`, or another integration branch.
   - If you are still on an integration branch, switch before implementing:
     ```bash
     git switch -c task/<task-name>
     python3 ./.trellis/scripts/task.py set-branch <task-dir> task/<task-name>
     ```
     On Windows, use `python` instead of `python3`.

1. **Discover packages and their spec layers**:
   ```bash
   python3 ./.trellis/scripts/get_context.py --mode packages
   ```
   On Windows, use `python` instead of `python3`.

2. **Identify which specs apply** to your task based on:
   - Which package you're modifying (e.g., `cli/`, `docs-site/`)
   - What type of work (backend, frontend, unit-test, docs, etc.)

3. **Read the spec index** for each relevant module:
   ```bash
   cat .trellis/spec/<package>/<layer>/index.md
   ```
   Follow the **"Pre-Development Checklist"** section in the index.

4. **Read the specific guideline files** listed in the Pre-Development Checklist that are relevant to your task. The index is NOT the goal — it points you to the actual guideline files (e.g., `error-handling.md`, `conventions.md`, `mock-strategies.md`). Read those files to understand the coding standards and patterns.

5. **Always read team workflow and shared guides**:
   ```bash
   cat .trellis/spec/team-collaboration.md
   ```
   This contains Trellis task assignment, short task branch, PR review, and integration branch discipline.

   ```bash
   cat .trellis/spec/guides/index.md
   ```

6. Understand the coding standards and patterns you need to follow, then proceed with your development plan.

This step is **mandatory** before writing any code.
