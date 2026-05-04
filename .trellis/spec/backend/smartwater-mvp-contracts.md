# SmartWater MVP Cross-Service Contracts

> Canonical MVP contracts shared by the Java backend, Python Worker, frontend, and regulation knowledge pack.

---

## Source Of Truth

This document hardens decisions from:

- `.trellis/tasks/archive/2026-04/04-24-smartwater-mvp-domain-contract/info.md`
- `.trellis/tasks/archive/2026-04/04-24-smartwater-review-inference-vendor-contract/prd.md`
- `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md`

Do not invent conflicting enum names or response shapes in child tasks. If implementation proves this contract wrong, update this spec and the affected task PRDs together.

---

## MVP Boundaries

The MVP is an AI-assisted review demo, not a full approval workflow.

- Applicant submits materials into fixed upload slots and receives a `taskId` / `sessionId` pair.
- Java backend owns submission records, material metadata, object storage references, task status, and query APIs.
- Python Worker owns OCR, field extraction, review reasoning, material summaries, and structured result writeback.
- Frontend polls status and renders applicant/reviewer projections.
- Regulation knowledge pack provides static material checklist, field rules, review basis entries, and prompt snippets.
- AI output is always assistive advice. It must not express final approval or rejection.

Out of scope for MVP:

- Account system, reviewer task list, workflow actions, correction loop, material versioning, or export.
- Free upload classification, multi-file slots, multi-applicant, or multi-water-source workflows. Word/Docx parsing is out of MVP implementation but required for the full version roadmap.

---

## Canonical Enums

### MaterialType

MVP fixed values:

```json
["APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"]
```

Rules:

- The frontend displays fixed slots for exactly these three material types in MVP.
- Each material type accepts at most one uploaded file in MVP.
- Missing materials are allowed at submission time and must produce explicit missing-material findings.
- The data model must keep a `material_type` field instead of hard-coding material semantics into table or column names.
- MVP persistence should store `material_type` as a string enum value. Do not introduce a dictionary table until material management becomes dynamic.
- The backend should be able to migrate from string enum values to a dictionary/config table when adding materials such as `WATER_RESOURCE_ASSESSMENT_REPORT`（水资源论证报告）.
- Do not design persistence or API paths that require schema changes for every future material type.

### AcceptedFileType

MVP accepted values:

```json
["jpg", "jpeg", "png", "pdf"]
```

Full-version required values include Word formats:

```json
["doc", "docx"]
```

Rules:

- Frontend and backend both validate extensions.
- Backend remains authoritative for accepted content type and file count validation.
- MVP may reject `doc` and `docx` while OCR/Word parsing is not implemented.
- Full version must support Word/Docx upload and parsing, so object storage metadata and material APIs must not assume every document is an image or PDF.

### ProcessingStatus

```json
[
  "SUBMITTED",
  "QUEUED",
  "PROCESSING",
  "PARTIAL_SUCCESS",
  "COMPLETED",
  "FAILED"
]
```

Allowed transitions:

```text
SUBMITTED -> QUEUED
SUBMITTED -> PROCESSING
QUEUED -> PROCESSING
PROCESSING -> COMPLETED
PROCESSING -> PARTIAL_SUCCESS
PROCESSING -> FAILED
QUEUED -> FAILED
SUBMITTED -> FAILED
```

Rules:

- `PARTIAL_SUCCESS`, `COMPLETED`, and `FAILED` are terminal for MVP result display.
- Terminal state does not imply legal approval or rejection.
- Re-upload or correction creates a new task in MVP.
- `CANCELLED` is intentionally not part of the MVP contract.

### FindingType

```json
[
  "MISSING_MATERIAL",
  "MISSING_FIELD",
  "INVALID_FORMAT",
  "INCONSISTENT_IDENTITY",
  "INCONSISTENT_CREDENTIAL",
  "WATER_SOURCE_INCOMPLETE",
  "WATER_AMOUNT_REVIEW_REQUIRED",
  "PERMIT_REQUIREMENT_REVIEW_REQUIRED",
  "PUBLIC_NOTICE_REVIEW_REQUIRED",
  "WATER_RESOURCE_ASSESSMENT_REVIEW_REQUIRED",
  "MULTI_APPLICANT_UNSUPPORTED",
  "MULTI_WATER_SOURCE_UNSUPPORTED",
  "OCR_LOW_CONFIDENCE",
  "MODEL_UNCERTAIN",
  "SYSTEM_ERROR"
]
```

### Severity

```json
["INFO", "WARNING", "BLOCKER"]
```

Rules:

- `BLOCKER` means manual review must address the item before relying on AI output.
- `WARNING` means review attention is needed but partial result remains useful.
- `INFO` is explanatory or low-risk.

### Audience

```json
["APPLICANT", "REVIEWER", "SYSTEM"]
```

Rules:

- Applicant projection only includes applicant-visible findings and basic upload/field hints.
- Reviewer projection includes full extraction results, issue list, risk hints, draft opinion, evidence references, and manual review notes.
- `SYSTEM` items must be mapped before display; do not expose raw debug details to users.

---

## Task Aggregate

`ReviewTask` is the lifecycle aggregate shared across services.

Required fields:

| Field | Type | Owner | Notes |
|---|---|---|---|
| `taskId` | string | Java | Public task identifier for MVP access. |
| `sessionId` | string | Java | Demo access token paired with `taskId`. |
| `status` | `ProcessingStatus` | Java | Current lifecycle status. |
| `submittedAt` | ISO-8601 datetime | Java | Backend server time. |
| `updatedAt` | ISO-8601 datetime | Java | Last state/result update time. |
| `materialSlots` | `MaterialSlot[]` | Java | Always contains the three fixed slots. |
| `resultSummary` | `ResultSummary` | Java/Python | Lightweight status/result counts. |
| `applicantResult` | `ApplicantResult` | Java projection | Filtered applicant-facing result. |
| `reviewerResult` | `ReviewerResult` | Java projection | Full reviewer-facing result. |
| `knowledgePackVersion` | string | Python/Knowledge | Version/hash used by Worker. |

Invariants:

- A task has exactly one processing lifecycle.
- A task can contain zero to three submitted materials.
- Submitted material files do not mutate after processing starts in MVP.
- Missing materials do not fail the task by themselves.

---

## Cross-Service Flow

1. Frontend applicant page uploads files by fixed `MaterialType` slot.
2. Java validates slots, file count, extension/content type, and creates a `ReviewTask`.
3. Java stores material metadata plus object storage references and returns `taskId`, `sessionId`, and initial `status`.
4. Python Worker receives or pulls `taskId`, material references, and knowledge pack version.
5. Python Worker performs OCR, field extraction, knowledge-constrained review reasoning, and structured result writeback.
6. Frontend polls Java task status and renders processing, partial success, failed, or completed states.
7. Applicant page renders only basic hints; reviewer page renders full read-only result.

---

## Material Storage Metadata

Java backend owns upload acceptance and object storage persistence. Python Worker reads materials through references and must not own archive policy.

Storage provider decision:

- Runtime/local integration target: RustFS.
- API style: S3-compatible object storage API, so Java may use an S3-compatible SDK/client behind `StorageService`.
- Business code must depend on object-storage abstractions and metadata, not RustFS-specific SDK classes.
- Ordinary unit tests must mock or fake `StorageService`; real RustFS belongs only in explicit integration tests or manual end-to-end verification.
- Config and docs must use project-neutral or RustFS-specific names consistently. Do not describe the required middleware as MinIO.

Material metadata must include enough information for both MVP and full-version parsing:

| Field | Notes |
|---|---|
| `materialId` | Backend material identifier. |
| `material_type` | String enum in MVP; future dictionary/config-table migration point. |
| `originalFileName` | Sanitized display name. |
| `contentType` | MIME type observed at upload. |
| `fileExtension` | Normalized extension, including future `doc` / `docx`. |
| `fileSize` | Uploaded file size for validation and auditing. |
| `storageKey` | Object storage key or internal reference. |
| `uploadedAt` | Backend upload timestamp. |

Rules:

- Store object references, not raw files, in task/result DTOs.
- Use short-lived access URLs or backend-mediated download when Python Worker needs file bytes.
- Do not design storage metadata that assumes every material is an image or PDF.
- File read, OCR, PDF parsing, and future Word parsing failures may be retried with bounded retry policy.
- Retry exhaustion must map to `PARTIAL_SUCCESS` or `FAILED` without losing task state.

---

## Validation Ownership

| Concern | Owner | Notes |
|---|---|---|
| Slot name and file count | Java backend | Frontend can pre-check, but backend is authoritative. |
| File extension and MIME | Java backend | Reject Word/Docx in MVP. |
| Object storage reference | Java backend | Python consumes references, not upload ownership. |
| OCR and extraction confidence | Python Worker | Return confidence and evidence references where available. Parsing/OCR failures may be retried with bounded retry policy. |
| Review result schema | Python Worker + Java backend | Worker validates before writeback; Java rejects invalid result snapshots. |
| Applicant/reviewer visibility | Java backend | Frontend should not filter from a full reviewer payload for applicant display. |
| Knowledge basis IDs | Knowledge pack + Python Worker | Model may only cite provided knowledge fragments. |

---

## Forbidden Patterns

- Do not introduce alternate enum names such as `WATER_INTAKE_APPLICATION` unless the contract is updated everywhere.
- Do not expose `reviewerResult` directly on applicant pages.
- Do not treat AI `draftOpinion` as a final administrative decision.
- Do not let Python Worker own object storage persistence policy.
- Do not make ordinary unit tests require a running RustFS instance or real object-storage credentials.
- Do not log raw OCR text, full prompts, ID-card numbers, or full business-license recognition text.
- Do not drop task state when file reading, OCR, PDF parsing, or future Word parsing fails; map failures to retryable processing errors, `PARTIAL_SUCCESS`, or `FAILED`.
