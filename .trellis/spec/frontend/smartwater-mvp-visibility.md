# SmartWater MVP Frontend Visibility Contract

> Frontend-specific contract for the applicant submission page and reviewer result page.

---

## MVP Pages

The MVP frontend is a two-page demo application:

1. Applicant submission page.
2. Reviewer read-only result page.

Out of scope:

- Login, role management, task list, workflow actions, correction loop, or result export.
- Editing AI review output.
- Free material upload classification.

---

## Applicant Submission Page

The page must render exactly three fixed material slots:

| MaterialType | Display intent | Required for complete review |
|---|---|---:|
| `APPLICATION_FORM` | 取水许可申请书 | Yes |
| `BUSINESS_LICENSE` | 营业执照 | Yes |
| `ID_CARD` | 身份证 | Yes |

Rules:

- Allow submitting with missing materials.
- Allow at most one file per slot.
- Allow only `jpg`, `jpeg`, `png`, and `pdf` in MVP; display Word/Docx as a full-version requirement, not an MVP-supported upload type.
- Show frontend validation as a convenience, but treat backend validation errors as authoritative.
- After successful submission, store/display `taskId` and `sessionId` for result lookup.

---

## Status Rendering

Frontend status labels must map from canonical `ProcessingStatus`:

| Status | Applicant display | Reviewer display |
|---|---|---|
| `SUBMITTED` | 已提交 | 已提交 |
| `QUEUED` | 等待处理 | 等待 Worker 处理 |
| `PROCESSING` | 智能审核处理中 | OCR/抽取/审核处理中 |
| `PARTIAL_SUCCESS` | 部分结果已生成 | 部分材料或步骤处理失败 |
| `COMPLETED` | 审核辅助结果已生成 | 完整审核辅助结果已生成 |
| `FAILED` | 暂无法生成结果 | 处理失败，查看失败原因 |

Rules:

- Poll Java backend for status; do not call Python Worker directly from frontend.
- Terminal states for MVP are `PARTIAL_SUCCESS`, `COMPLETED`, and `FAILED`.
- Do not infer final approval/rejection from any status.

---

## Visibility Boundary

Applicant view may show:

- Missing materials.
- Obvious upload or field issues marked `applicantVisible`.
- Basic retry or resubmission guidance for a new task.
- Short AI-assist disclaimer.

Applicant view must not show:

- Full reviewer result payload.
- Detailed risk analysis.
- Draft reviewer opinion.
- System/debug failure details.
- Full OCR text or sensitive credential extraction details.

Reviewer view may show:

- Extracted fields and confidence.
- Material summaries.
- Full issue list.
- Risk hints.
- Draft review opinion.
- Basis references.
- Manual review notice.
- Failure category and redacted failure reason.

---

## Type Safety

Frontend types must reuse the canonical enum strings from `../backend/smartwater-mvp-contracts.md`.

Recommended TypeScript representation:

```ts
export type MaterialType = 'APPLICATION_FORM' | 'BUSINESS_LICENSE' | 'ID_CARD'
// Future full-version examples: 'WATER_RESOURCE_ASSESSMENT_REPORT'

export type ProcessingStatus =
  | 'SUBMITTED'
  | 'QUEUED'
  | 'PROCESSING'
  | 'PARTIAL_SUCCESS'
  | 'COMPLETED'
  | 'FAILED'

export type Severity = 'INFO' | 'WARNING' | 'BLOCKER'
```

Rules:

- Do not duplicate different string literals in page components.
- Keep API DTO types in a shared `types` module once the frontend package exists.
- Avoid `any`; use `unknown` for untrusted backend payloads until parsed or narrowed.
