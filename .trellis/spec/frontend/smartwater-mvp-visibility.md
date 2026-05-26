# SmartWater MVP Frontend Visibility Contract

> Frontend-specific contract for the applicant submission page and reviewer result page.

---

## MVP Pages

The MVP started as a two-page demo application and CP3 extends it into a
minimal authenticated workflow:

1. Applicant submission page.
2. Reviewer read-only result page.
3. Login page backed by Java `/auth/login`.
4. Role-scoped application list / review entry.

Out of scope:

- Full role management UI, workflow actions, correction loop, or result export.
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

## CP3 Role Routing And Token State

Frontend auth state is a convenience layer over backend enforcement. It must not
be the only permission boundary.

### 1. Scope / Trigger

- Trigger: login page, request interceptor, role-based routing/menu, task list
  links, applicant/reviewer result lookup, or auth error handling.

### 2. Signatures

```ts
login({ username, password }) -> R<LoginResponse>
getCurrentUser() -> R<UserProfile>
```

```ts
export type UserRole = 'APPLICANT' | 'REVIEWER' | 'ADMIN'
```

### 3. Contracts

| Item | Contract |
|---|---|
| Token storage | Store only the Sa-Token value and current user profile in localStorage. |
| Request header | Send `Authorization: Bearer <token>` for normal business APIs. |
| Business `401` | Clear token/user state and redirect to `/login`. |
| Applicant menu | Show application list and new application entry; hide CP2 MCP demo. |
| Reviewer menu | Hide new application; route result/list actions to reviewer workflow. |
| Admin menu | May see all entries needed for demo and troubleshooting. |
| Applicant result link | Must call `/task/{taskId}/result/applicant`, not reviewer result APIs. |
| Reviewer result link | May call `/task/{taskId}/result/reviewer` only for reviewer/admin roles. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| No token and opening business route | Redirect to `/login?redirect=<path>`. |
| Stored user profile missing or malformed | Redirect to login; do not guess a role. |
| Applicant opens `/knowledge-mcp` | Redirect to application list. |
| Reviewer opens `/apply` | Redirect to application list. |
| Java returns business `401` with HTTP 200 | Clear auth state and redirect to login. |

### 5. Good/Base/Bad Cases

- Good: page code chooses applicant vs reviewer result projection based on the
  stored role and still relies on backend errors for authority.
- Good: adapters normalize unknown `extractedFields` payloads before rendering.
- Base: frontend role menu is minimal; CP4 can add richer workbench navigation.
- Bad: link applicants to reviewer result pages and hide fields after fetching.
- Bad: keep stale token after Java returns business `401`.

### 6. Tests Required

- Request utility test for business `401` clearing auth state.
- Task adapter test for `extractedFields[]` array normalization.
- Result page/component test or equivalent regression that applicant flow uses
  applicant projection only.

### 7. Wrong vs Correct

#### Wrong

```ts
getReviewerResult(taskId, sessionId)
```

for applicant result display.

#### Correct

```ts
role === 'APPLICANT'
  ? getApplicantResult(taskId, sessionId)
  : getReviewerResult(taskId, sessionId)
```

with reviewer-only panels hidden unless reviewer data was fetched.

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
