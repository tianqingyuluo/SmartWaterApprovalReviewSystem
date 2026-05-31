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
- Allow `jpg`, `jpeg`, `png`, `pdf`, and `docx` in CP3.5 because the backend accepts DOCX and the Python document pipeline parses DOCX directly. Legacy `.doc` remains out of scope until a conversion path exists.
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
- CP3 initial-review handling result: `handlingStatus`, `handlingStatusLabel`,
  `reviewerRemark`, and action time.
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
- Browser-safe original material preview for uploaded PDF/JPG/JPEG/PNG files.
- Full issue list.
- Risk hints.
- Draft review opinion.
- Basis references.
- Manual review notice.
- CP3 initial-review action controls and action log after the backend exposes
  a reviewer result for the task.
- Failure category and redacted failure reason.

## Browser Material Preview

Result pages may embed original materials only through the Java task preview
endpoint. The frontend must never use object-storage keys or Worker download
APIs for browser display.

### 1. Scope / Trigger

- Trigger: reviewer/applicant result page, material slot status display, preview
  API adapter, or file-extension UI logic.

### 2. Signatures

```ts
getMaterialPreviewUrl(taskId: string, materialType: MaterialType): string
fetchMaterialPreview(taskId: string, materialType: MaterialType): Promise<AxiosResponse<Blob>>
```

Backend path:

```http
GET /api/task/{taskId}/material/{materialType}/preview
Authorization: Bearer <token>
```

Preview state:

```ts
export type MaterialPreviewKind = 'IMAGE' | 'PDF' | 'UNSUPPORTED'
```

### 3. Contracts

| Item | Contract |
|---|---|
| Blob fetch | Use axios `responseType: 'blob'`; preview API is binary, not `R<T>`. |
| URL construction | Encode `taskId` and `materialType` path segments. |
| Supported embed | `jpg`, `jpeg`, `png` render as `<img>`; `pdf` renders as `<iframe>` or equivalent viewer. |
| Unsupported embed | `docx` and unknown extensions show a clear unsupported-preview message. |
| Object URL lifecycle | Revoke old object URLs on task change and component unmount. |
| Auth | Rely on the existing request interceptor to send `Authorization: Bearer <token>`. |
| Secret boundary | Do not add `storageKey`, signed URLs, Worker token, or object-store credentials to frontend DTOs or state. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Uploaded image/PDF preview succeeds | Display the material beside task/result information. |
| Preview returns `415` for DOCX | Display unsupported-preview copy; task/result page remains usable. |
| Preview returns `401` / business auth failure | Existing auth handling clears token and redirects when required. |
| Preview returns `403` / `404` | Show per-material preview error, not a full-page crash. |
| User switches task while blob request is inflight | Ignore stale response and revoke any old object URL. |

### 5. Good/Base/Bad Cases

- Good: result page can show real uploaded business license image while also
  showing OCR fields and AI issues.
- Good: DOCX application form is parsed by backend/Worker but displayed as
  "browser preview unsupported".
- Base: applicant and reviewer result pages can share preview adapter behavior,
  while backend remains the authority for visibility.
- Bad: generate preview URLs from `storageKey`.
- Bad: treat binary preview errors as normal JSON `R<T>` responses.

### 6. Tests Required

- API adapter test for URL encoding and blob response type.
- Result page or state regression for image/PDF supported branch, DOCX
  unsupported branch, and object URL cleanup.
- Cross-layer E2E evidence for actual HTTP status, `Content-Type`, `inline`,
  and `nosniff` headers.

### 7. Wrong vs Correct

#### Wrong

```ts
const url = `/material/download?key=${slot.storageKey}`
```

#### Correct

```ts
const response = await fetchMaterialPreview(taskId, slot.materialType)
const objectUrl = URL.createObjectURL(response.data)
```

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
| Reviewer action submit | Reviewer/admin may call `POST /task/{taskId}/reviewer-action` with one of `APPROVE_INITIAL_REVIEW`, `RETURN_FOR_CORRECTION`, or `TRANSFER_MANUAL_REVIEW`. |

## CP2 MCP Demo Operations Boundary

The CP2 knowledge/MCP demo page is an operations visibility surface. It may show
real Java-backed health and ingest command data, but it must not imply the
browser directly executes Python ingest or real MCP tool calls unless a real
HTTP proxy exists.

### 1. Scope / Trigger

- Trigger: `/knowledge-mcp`, AI/MCP health status display, ingest demo display,
  or frontend CP2 demo copy.

### 2. Signatures

Frontend API calls:

```http
GET /api/ai/health
POST /api/ai/ingest
POST /api/ai/mcp/knowledge-search
POST /api/ai/mcp/check-completeness
```

Page route:

```text
/knowledge-mcp
```

### 3. Contracts

| Item | Contract |
|---|---|
| Health source | Page calls Java `/api/ai/health`; Java probes Python FastAPI and returns `reachable`, `healthUrl`, `mcpUrl`, `mcpTransport`, `checkedAt`, and `responseBody`. |
| Ingest demo source | Page calls Java `/api/ai/ingest`; Java returns reproducible Python CLI command, source directory, chunk parameters, rebuild flag, and verification command. |
| Tool source | Normal `knowledge_search` and `check_completeness` buttons call Java `/api/ai/mcp/*`; Java calls Python FastAPI `/api/mcp/tools/*`; Python invokes the registered MCP tool via `FastMCP.call_tool`. |
| Local-only demos | Local demo data is allowed only for explicitly labeled failure-demo buttons. It must never be the default success path for `knowledge_search` or `check_completeness`. |
| Auth | Route is admin-visible; Java remains the authority through normal bearer-token auth. |
| No fake execution | Browser must not claim ingest was executed when only the command was returned. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Java `/api/ai/health` succeeds and Python is reachable | Show real-interface status, MCP URL, transport, HTTP code, checked time, and response body. |
| Java `/api/ai/health` fails or returns business error | Show page-level retry/error; normal tool buttons still attempt the Java MCP proxy and surface real failures. |
| Java `/api/ai/ingest` succeeds | Show command, workdir, sourceDir, chunkSize/chunkOverlap, rebuild, verification command, and note. |
| Java `/api/ai/ingest` fails | Show retry/error; do not invent fallback command. |
| Java `/api/ai/mcp/knowledge-search` succeeds | Render the returned `results[]`, `topK`, `total`, and `knowledgePackVersion`; mark the last tool call as real API source. |
| Java `/api/ai/mcp/check-completeness` succeeds | Render returned `submitted/required/missing/complete/findings`; an empty material selection must still be sent to backend as `materials: []`. |
| Java MCP proxy fails | Show the backend error and retry action; do not replace it with local success data. |

### 5. Good/Base/Bad Cases

- Good: `/knowledge-mcp` button clicks produce `/api/ai/health`,
  `/api/ai/ingest`, `/api/ai/mcp/knowledge-search`, and
  `/api/ai/mcp/check-completeness` network requests.
- Good: empty `check_completeness` selection calls backend MCP and returns all
  required materials as missing.
- Bad: Page only displays hard-coded health/ingest values.
- Bad: Page says ingest completed after merely receiving an ops command.
- Bad: normal tool buttons build local `buildDemoKnowledgeSearch` or
  `buildDemoCompleteness` results instead of requesting Java.

### 6. Tests Required

- API adapter test maps Java AI health response into page status, including
  `source: "api"` and knowledge pack version parsing from response body.
- API adapter tests assert `knowledge_search` and `check_completeness` use the
  Java MCP proxy endpoints, including empty material selection.
- Frontend build must pass after page/template changes.
- Manual or E2E evidence should verify the page route and same-origin
  `/api/ai/health`, `/api/ai/ingest`, and `/api/ai/mcp/*` requests.

### 7. Wrong vs Correct

#### Wrong

```ts
status.value = buildDemoStatus(null, 'MCP 服务真实可用')
```

#### Correct

```ts
const health = await getAiHealth()
status.value = toKnowledgeStatusFromAiHealth(health)
```

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| No token and opening business route | Redirect to `/login?redirect=<path>`. |
| Stored user profile missing or malformed | Redirect to login; do not guess a role. |
| Applicant opens `/knowledge-mcp` | Redirect to application list. |
| Reviewer opens `/apply` | Redirect to application list. |
| Java returns business `401` with HTTP 200 | Clear auth state and redirect to login. |
| Reviewer action returns `409` | Treat as already handled or no longer actionable; refresh the task detail before enabling another submit. |
| Applicant result has `handlingStatus=CORRECTION_REQUIRED` | Show correction material upload controls in applicant view only. |
| Applicant correction upload succeeds | Refresh task status/result and hide the correction upload controls once handling snapshot is cleared. |
| Correction upload returns business error | Show the backend error on the correction panel; do not mutate local material state as if upload succeeded. |

### 5. Good/Base/Bad Cases

- Good: page code chooses applicant vs reviewer result projection based on the
  stored role and still relies on backend errors for authority.
- Good: adapters normalize unknown `extractedFields` payloads before rendering.
- Good: applicant correction panel posts fixed-slot `FormData` to Java and never exposes `storageKey`.
- Base: frontend role menu is minimal; CP4 can add richer workbench navigation.
- Bad: link applicants to reviewer result pages and hide fields after fetching.
- Bad: keep stale token after Java returns business `401`.
- Bad: show correction upload controls in reviewer/admin result projection or when handling status is not `CORRECTION_REQUIRED`.

### 6. Tests Required

- Request utility test for business `401` clearing auth state.
- Task adapter test for `extractedFields[]` array normalization.
- Result page/component test or equivalent regression that applicant flow uses
  applicant projection only.
- API adapter/FormData test for fixed material field names used by first
  submission and correction resubmission.

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

### Scenario: Applicant Correction Upload Visibility

#### 1. Scope / Trigger

- Trigger: result page, task adapter, material upload component, or backend correction API changes.

#### 2. Signatures

Frontend API:

```ts
resubmitCorrectionMaterials(taskId: string, formData: FormData): Promise<R<SubmitResponse>>
appendMaterialFiles(formData, files: Partial<Record<MaterialType, File | null | undefined>>): FormData
```

Backend path:

```http
POST /api/task/{taskId}/correction-materials
```

#### 3. Contracts

| Item | Contract |
|---|---|
| Visibility | Only render correction upload when `TaskResultView.viewMode === "APPLICANT"` and `handlingStatus === "CORRECTION_REQUIRED"`. |
| Material fields | Use shared `MATERIAL_FORM_FIELDS`, not string literals in page code. |
| Slot set | Render exactly `MATERIAL_SLOTS`: `APPLICATION_FORM`, `BUSINESS_LICENSE`, `ID_CARD`. |
| Validation | Frontend pre-checks extensions with `ACCEPTED_EXTENSIONS`; backend remains authoritative. |
| Success refresh | After upload succeeds, clear selected files and re-run task lookup so status/material/result state comes from Java. |
| Secret boundary | Do not expose `storageKey`, signed storage URLs, Worker token, or Python FastAPI URL in frontend state. |

#### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| No file selected | Show local panel error and do not call backend. |
| Unsupported extension | Mark that slot invalid and clear the selected input. |
| Backend returns `400/403/409/500` business error | Show error in correction panel and keep current page usable. |
| Upload succeeds and task returns `PROCESSING` | Refresh result; correction panel disappears because `handlingStatus` is cleared. |

#### 5. Good/Base/Bad Cases

- Good: applicant sees reviewer remark and uploads only the corrected material slot.
- Good: `appendMaterialFiles` is shared by new application submission and correction upload.
- Base: file input state stays page-local; no Pinia store is introduced.
- Bad: duplicate multipart field names in multiple pages.
- Bad: fetch reviewer result just to decide whether correction upload should show.

#### 6. Tests Required

- `api/task.spec.ts` asserts fixed material field mapping.
- `npm run build` must pass after result-page changes.
- If a page/component test harness is added later, cover applicant-visible and reviewer-hidden correction panel branches.

#### 7. Wrong vs Correct

##### Wrong

```ts
formData.append('business_license', file)
```

##### Correct

```ts
appendMaterialFiles(formData, { BUSINESS_LICENSE: file })
```

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
