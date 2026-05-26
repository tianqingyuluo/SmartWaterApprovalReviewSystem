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

## Regulation Knowledge Pack Contract

The MVP regulation knowledge pack is a static Python Worker asset.

### 1. Scope / Trigger

- Trigger: any Python Worker implementation that assembles review prompts or validates model `basisRefs`.
- Asset path: `python-services/smart-water-approval-review-system-py/knowledge_pack/water_permit_mvp.json`.
- Loader: `knowledge_pack.load_knowledge_pack(path: str | Path | None = None) -> dict`.
- The Worker must copy `pack["version"]` into `ReviewTask.knowledgePackVersion` / Worker result callbacks.

### 2. Required JSON Sections

```json
[
  "version",
  "materialChecklist",
  "applicationFieldRules",
  "reviewBasis",
  "promptSnippets",
  "manualReviewRules"
]
```

Each fragment that can be sent to the review reasoning adapter must expose stable IDs:

| Section | Required ID fields | Purpose |
|---|---|---|
| `materialChecklist[]` | `id`, `materialType`, `basisRefs[]` | MVP slot checklist and missing-material messages. |
| `applicationFieldRules[]` | `id`, `fieldPath`, `basisRefs[]` | Field completeness, format, consistency, and manual-review hints. |
| `reviewBasis[]` | `id`, `sourceId`, `sourceTitle`, `summary` | Citable legal/process/field basis fragments. |
| `promptSnippets[]` | `id`, `kind`, `text` | Prompt assembly constraints and wording. |
| `manualReviewRules[]` | `id`, `findingCode`, `basisRefs[]` | Rules that must never become automatic final decisions. |

### 3. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Pack file missing | `load_knowledge_pack()` raises `KnowledgePackError`. |
| Invalid JSON | `load_knowledge_pack()` raises `KnowledgePackError`. |
| Required section missing | `load_knowledge_pack()` raises `KnowledgePackError`. |
| `basisRefs[]` points outside `reviewBasis[].id` | Unit test must fail before merge. |
| Model returns a `basisRef` not included in request fragments | Worker must reject/repair the model output before writeback. |

### 4. Good/Base/Bad Cases

- Good: Worker sends selected `reviewBasis` fragments and the model cites only those IDs.
- Base: Missing `BUSINESS_LICENSE` creates `MISSING_MATERIAL` with applicant-safe copy and reviewer copy.
- Bad: Model invents a regulation/article ID or uses final approval wording. The Worker must not write that result.

### 5. Tests Required

- Unit test loads `water_permit_mvp.json`.
- Unit test asserts the MVP material types are exactly `APPLICATION_FORM`, `BUSINESS_LICENSE`, and `ID_CARD`.
- Unit test asserts every configured `basisRefs[]` value is present in `reviewBasis[].id`.

### 6. Wrong vs Correct

#### Wrong

```text
Prompt: "参考相关法律审核"
Output basisRefs: ["浙江水法第999条"]
```

#### Correct

```text
Prompt fragment includes reviewBasis id BASIS_PUBLIC_NOTICE
Output basisRefs: ["BASIS_PUBLIC_NOTICE"]
```

---

## MCP Knowledge Tools Contract

The V1 MCP server exposes local knowledge tools over the Python service and must reuse the static MVP knowledge pack.

### 1. Scope / Trigger

- Trigger: adding or changing MCP tools, local knowledge search, material completeness checks, MCP demo commands, or future Java/agent integration with these tools.
- Runtime module: `python-services/smart-water-approval-review-system-py/src/mcp_server/`.
- Core logic module: `python-services/smart-water-approval-review-system-py/src/services/knowledge_tools.py`.
- Dependency: official Python `mcp` SDK with `FastMCP`.

### 2. Signatures

- Server startup:

```bash
uv run python -m src.mcp_server.app --transport stdio
uv run python -m src.mcp_server.app --transport streamable-http
uv run python -m src.mcp_server.app --transport sse
```

- Demo commands:

```bash
uv run python -m src.mcp_server.demo --list-tools
uv run python -m src.mcp_server.demo --run-samples --query "营业执照" --top-k 3 --materials-json '["APPLICATION_FORM","BUSINESS_LICENSE"]'
```

- Tool signatures:

```python
knowledge_search(query: str, top_k: int = 5) -> dict
check_completeness(materials: list | dict | str | None = None) -> dict
```

### 3. Contracts

`knowledge_search` response fields:

| Field | Contract |
|---|---|
| `query` | Original stripped query string. |
| `topK` | Clamped effective result limit, minimum `1`, maximum `50`. |
| `requestedTopK` | Caller-provided `top_k` value before clamping/coercion. |
| `knowledgePackVersion` | Exact `water_permit_mvp.json` `version`. |
| `total` | Number of returned result rows after filtering and limit. |
| `results[]` | Ranked match objects from `materialChecklist`, `applicationFieldRules`, `reviewBasis`, `promptSnippets`, or `manualReviewRules`. |
| `results[].section` | Knowledge pack section name. |
| `results[].id` | Stable item ID from the knowledge pack. |
| `results[].title` | Display name, source title, snippet kind, or item ID. |
| `results[].materialType` | Material type when present, else `null`. |
| `results[].fieldPath` | Field path when present, else `null`. |
| `results[].excerpt` | Summary/instruction/text or referenced basis summary. |
| `results[].score` | Local lexical match score. |
| `results[].rank` | 1-based rank after score sorting. |
| `results[].sourceRefs` | Direct source references from the item. |
| `results[].sourceIds` | Normalized source IDs, including IDs derived from referenced `reviewBasis`. |
| `results[].basisRefs` | Direct basis refs from the item. |

`check_completeness` input contract:

- Accepts MVP material strings such as `"APPLICATION_FORM"`.
- Accepts lists of strings or material objects with `materialType`, `material_type`, `type`, or `name`.
- Accepts dictionaries whose values are strings, booleans, or material objects.
- Ignores unknown material types; Java remains authoritative for upload validation.

`check_completeness` response fields:

| Field | Contract |
|---|---|
| `knowledgePackVersion` | Exact `water_permit_mvp.json` `version`. |
| `required` | Required MVP material type list from `materialChecklist`. |
| `submitted` | Deduplicated recognized submitted material types. |
| `missing` | Required material types absent from `submitted`. |
| `complete` | `true` only when `missing` is empty. |
| `findings[]` | One finding per missing required material. |
| `findings[].code` | Missing finding code, normally `MISSING_MATERIAL`. |
| `findings[].severity` | Configured severity from `materialChecklist[].missingFinding`. |
| `findings[].message` | Reviewer message from the knowledge pack. |
| `findings[].applicantMessage` | Applicant-safe message from the knowledge pack. |
| `findings[].sourceRefs` | Source refs for the checklist item. |
| `findings[].basisRefs` | Basis refs for the checklist item. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Knowledge pack missing or structurally invalid | Construction raises `KnowledgePackError`; do not start MCP with a silent empty pack. |
| `query` is empty | Return structured response with zero or default-ranked matches, not an exception. |
| `top_k` is non-numeric | Coerce to default `5`. |
| `top_k < 1` | Clamp effective `topK` to `1`. |
| `top_k > 50` | Clamp effective `topK` to `50`. |
| `materials` is `None` | Treat as no submitted materials and report all missing required items. |
| `materials` includes unknown values | Ignore unknown values and do not mark required materials as present. |
| Demo `--materials-json` is invalid JSON | CLI may fail fast with JSON parse error; tests should cover valid examples. |

### 5. Good/Base/Bad Cases

- Good: MCP tool handlers are thin wrappers around `SmartWaterKnowledgeTools`, so tests call core logic without starting a server.
- Good: `knowledge_search("营业执照", 3)` returns ranked matches with `sourceIds`, `sourceRefs`, `basisRefs`, and `knowledgePackVersion`.
- Base: `check_completeness(["APPLICATION_FORM", "BUSINESS_LICENSE"])` returns `missing=["ID_CARD"]` and one `MISSING_MATERIAL` finding.
- Bad: Tool handlers duplicate checklist logic inside `mcp_server/server.py`, making CLI and future API behavior drift.
- Bad: MCP tools call OCR, LLM, Java backend, object storage, or network services during local knowledge lookup.

### 6. Tests Required

- Unit tests for `knowledge_search` response shape, rank/score behavior, `top_k` clamping, and `sourceIds` derivation.
- Unit tests for `check_completeness` list/dict/string inputs, unknown materials, duplicate materials, and missing finding payloads.
- Registration test that `build_mcp_server().list_tools()` exposes `knowledge_search` and `check_completeness`.
- Demo test or command evidence for `--list-tools` and `--run-samples`.
- Verification commands for Python MCP changes:

```bash
uv run python -m compileall src main.py knowledge_pack
uv run python -m pytest
uv run ruff check .
uv run mypy src main.py knowledge_pack
```

### 7. Wrong vs Correct

#### Wrong

```python
@server.tool()
def check_completeness(materials: list) -> str:
    return "缺少身份证"
```

#### Correct

```python
@server.tool(name="check_completeness")
def check_completeness(materials: list | dict | str | None = None) -> dict:
    return SmartWaterKnowledgeTools().check_completeness(materials)
```

---

## Java AI Ops Contract

Java exposes CP2 operational visibility for the Python AI/MCP service without pretending that a Python REST ingest API exists before it is implemented.

### 1. Scope / Trigger

- Trigger: Java-side AI service configuration, health visibility, MCP endpoint documentation, ingest trigger/evidence support, or future Java integration with Python AI service.
- Java package: `java-services/water-approval/src/main/java/com/tianqingyuluo/waterapproval/ai/`.
- Controller: `GET /api/ai/health`, `POST /api/ai/ingest`.
- Python current surface: MCP native transport and ingest CLI, not a formal REST ingest endpoint.

### 2. Signatures

Java config keys:

```yaml
water-approval:
  ai-service:
    base-url: http://localhost:8000
    health-path: /health
    internal-token: ""
    timeout: 3s
    mcp-transport: streamable-http
    mcp-path: /mcp
    ingest:
      workdir: ../../python-services/smart-water-approval-review-system-py
      source-dir: ../../docs/参考资料
      chunk-size: 512
      chunk-overlap: 64
      rebuild: false
```

Java endpoints:

```http
GET /api/ai/health
POST /api/ai/ingest
```

Python ingest command emitted by Java:

```bash
uv run python -m src.ingest.cli --source-dir <source-dir> --chunk-size <n> --chunk-overlap <n> [--rebuild]
```

### 3. Contracts

`GET /api/ai/health` response fields:

| Field | Contract |
|---|---|
| `baseUrl` | Normalized Python AI base URL with trailing slash removed. |
| `healthUrl` | `baseUrl + healthPath`. |
| `reachable` | `true` only when the configured health endpoint returns a non-error HTTP response. |
| `statusCode` | HTTP status when available, else `null`. |
| `message` | Short operational summary; must not include token values. |
| `responseBody` | Truncated response body for evidence/debugging. |
| `mcpTransport` | Configured MCP transport label such as `streamable-http`. |
| `mcpUrl` | Configured MCP URL for documentation/evidence. |
| `internalTokenConfigured` | Boolean only; never echo the secret. |
| `checkedAt` | Java server time of the check. |

`POST /api/ai/ingest` response fields:

| Field | Contract |
|---|---|
| `mode` | Must be `ops-command` until Python exposes a formal REST ingest API. |
| `workdir` | Directory where the command should be run. |
| `command[]` | Tokenized CLI command. |
| `verificationCommand` | MCP demo command for post-ingest verification. |
| `note` | Explicitly states Java does not execute Python ingest in-process. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Python health endpoint reachable | Return `code=200`, `data.reachable=true`, and status summary. |
| Python health endpoint returns 4xx/5xx | Return `code=200`, `data.reachable=false`, `data.statusCode=<status>`. |
| Python health endpoint unavailable/timeouts | Return `code=200`, `data.reachable=false`, short error class in `message`. |
| Internal token configured | Send `X-Internal-Token` on health probe; response only shows `internalTokenConfigured=true`. |
| Python REST ingest not available | `/api/ai/ingest` returns ops command, not a fake success of remote execution. |

### 5. Good/Base/Bad Cases

- Good: Java health check returns a structured degraded response when Python is offline, so CP2 operators can diagnose config without crashing Java.
- Good: `/api/ai/ingest` shows the exact `uv run python -m src.ingest.cli ...` command and MCP verification command.
- Base: MCP URL/transport are displayed as configured evidence fields.
- Bad: Java starts a local Python process on a web request or claims ingest ran successfully without Python confirmation.
- Bad: Java logs or echoes `AI_SERVICE_INTERNAL_TOKEN`.

### 6. Tests Required

- Controller tests for `/ai/health` and `/ai/ingest` response shape.
- Unit test for URL/path normalization and token configured flag.
- Unit test that ingest command includes chunk settings and only includes `--rebuild` when configured.
- Java verification command:

```bash
./mvnw test
```

### 7. Wrong vs Correct

#### Wrong

```java
return R.ok(Map.of("ingestTriggered", true));
```

when Python only has a CLI and no REST ingest endpoint.

#### Correct

```java
return R.ok(aiOpsService.getIngestOperation());
```

The response contains `mode=ops-command`, `command[]`, and `verificationCommand`.

---

## CP2 Python Ingest And ChromaDB Contract

Python CP2 ingest must be able to rebuild a knowledge base from an empty ChromaDB
directory using an OpenAI-compatible embedding endpoint.

### 1. Scope / Trigger

- Trigger: Python ingest CLI, ChromaDB persistence, embedding provider wiring, or
  CP2 evidence scripts.
- Python package: `python-services/smart-water-approval-review-system-py`.
- Primary command: `uv run python -m src.ingest.cli`.

### 2. Signatures

Ingest CLI:

```bash
uv run python -m src.ingest.cli \
  --source-dir <source-dir> \
  --chunk-size <n> \
  --chunk-overlap <n> \
  [--rebuild]
```

Evidence CLI:

```bash
uv run python -m src.cp2_evidence [--no-rebuild]
```

Embedding environment:

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
EMBEDDING_BASE_URL=https://router.tumuer.me/v1
EMBEDDING_API_KEY=<secret>
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=knowledge_base
KNOWLEDGE_SOURCE_DIR=<source-dir>
```

### 3. Contracts

| Item | Contract |
|---|---|
| `EMBEDDING_BASE_URL` | OpenAI-compatible API root only, not a full `/embeddings` path. |
| `EMBEDDING_API_KEY` | Required for real ingest/evidence; never committed or logged. |
| `--rebuild` | Clear the Chroma persist directory before opening a Chroma `PersistentClient`. |
| Chroma IDs | Stable per source file, block index, and chunk index so repeat ingest can upsert without duplicates. |
| Output stats | Print document count, text block count, chunk count, vector count, and source file list. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| `source-dir` missing | Return non-zero or stats with `Source directory not found`. |
| `EMBEDDING_API_KEY` missing in `cp2_evidence` | Abort before ingest and name the missing key. |
| Embedding provider unavailable | Record embedding batch errors and produce `0` vectors; evidence must not claim success. |
| `--rebuild` requested | Chroma persist directory is removed and recreated before client creation. |
| Chroma write fails | Test must expose the failure; do not hide it as a successful ingest. |

### 5. Good/Base/Bad Cases

- Good: `--rebuild` from a fresh or existing Chroma directory stores a positive
  vector count and prints all CP2 source files.
- Good: OpenAI-compatible router base URL is `https://router.tumuer.me/v1`, while
  the SDK call appends `/embeddings` internally.
- Base: image-only source samples can produce zero chunks when OCR is not part of
  CP2 ingest; this is acceptable if document/PDF sources generate vectors.
- Bad: set `EMBEDDING_BASE_URL=https://router.tumuer.me/v1/embeddings`, causing
  the SDK to construct an invalid endpoint.
- Bad: instantiate `chromadb.PersistentClient` and then delete its persist
  directory during `--rebuild`; this can leave SQLite handles in a read-only or
  invalid state.

### 6. Tests Required

- Unit test that `rebuild=True` clears the Chroma persist directory before
  constructing `ChromaStore`.
- Unit test that repeat ingest/upsert does not duplicate vectors.
- Unit test that embedding batch failures keep chunk/embedding pairs aligned.
- CP2 verification commands:

```bash
uv run python -m pytest -q tests/test_ingest_pipeline.py tests/test_chroma_store.py tests/test_embedding_client.py tests/test_cp2_evidence.py
uv run python -m src.ingest.cli --source-dir <source-dir> --chunk-size 512 --chunk-overlap 64 --rebuild
uv run python -m src.cp2_evidence --no-rebuild
```

### 7. Wrong vs Correct

#### Wrong

```python
store = ChromaStore()
if rebuild:
    store.rebuild()  # deletes the directory after the PersistentClient opened it
```

#### Correct

```python
if rebuild:
    ChromaStore.clear_persist_dir()
store = ChromaStore()
```

---

## CP3 Minimal RBAC And Task Visibility Contract

CP3 adds the minimum identity boundary required for a real applicant/reviewer
flow. This is not a full user-management subsystem.

### 1. Scope / Trigger

- Trigger: Java auth/login APIs, Sa-Token configuration, `user_account`
  persistence, frontend token state, task submission/list/status/result
  visibility, or Worker endpoint annotations.
- Goal: applicants can only operate on their own tasks; reviewers see review
  work only after AI processing reaches a reviewer-visible state; admins can
  inspect all tasks for demonstration and troubleshooting.

### 2. Signatures

Auth APIs:

```http
POST /api/auth/login
Content-Type: application/json

{"username": "applicant", "password": "<password>"}
```

```json
{
  "code": 200,
  "data": {
    "token": "<sa-token>",
    "user": {
      "userId": 1,
      "username": "applicant",
      "displayName": "默认申请人",
      "role": "APPLICANT"
    }
  }
}
```

```http
GET /api/auth/me
Authorization: Bearer <sa-token>
```

Authenticated business APIs:

```http
Authorization: Bearer <sa-token>
GET /api/task/list?page=1&size=20
POST /api/task/submit
GET /api/task/{taskId}/status
GET /api/task/{taskId}/result/applicant
GET /api/task/{taskId}/result/reviewer
```

Worker APIs remain token-protected and do not require a user session:

```http
X-Worker-Token: <configured worker token>
GET /api/task/pending
PUT /api/task/{taskId}/status
PUT /api/task/{taskId}/result
GET /api/material/download?key=<storageKey>
```

### 3. Contracts

| Item | Contract |
|---|---|
| Roles | Canonical values are `APPLICANT`, `REVIEWER`, and `ADMIN`. |
| Login token | Sa-Token value returned by `/auth/login`; frontend sends it as `Authorization: Bearer <token>`. |
| Public API | Only endpoints annotated with `@PublicApi`, currently `/auth/login`, bypass login. |
| Worker API | Endpoints annotated with `@WorkerApi` bypass user login but keep `X-Worker-Token` validation when token is configured. |
| Task owner | `review_task.owner_user_id` is set from the logged-in applicant/admin submitting the task. |
| Applicant visibility | Applicant lists and reads only tasks where `owner_user_id` equals the current user ID. |
| Reviewer visibility | Reviewer task list/status/result access is limited to reviewer-visible statuses: `PARTIAL_SUCCESS`, `COMPLETED`, `FAILED`. |
| Admin visibility | Admin can list and read all tasks; admin may submit for demo/troubleshooting. |
| Applicant result | `APPLICANT` result projection only; never expose `reviewerResult.extractedFields`, `riskHints`, or `draftOpinion`. |
| Reviewer result | Only `REVIEWER` or `ADMIN` can call `/result/reviewer`. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Missing or expired user token on business API | Return business `401`, and frontend clears auth state. |
| Wrong login credentials or disabled account | Return business `401` with a generic credential error. |
| Applicant A reads applicant B's task | Return `403`. |
| Applicant calls reviewer result endpoint | Return `403`. |
| Reviewer opens `SUBMITTED`, `QUEUED`, or `PROCESSING` task directly | Return `403`. |
| Reviewer submits a new application | Return `403`; frontend must hide the action. |
| Worker callback without configured/valid worker token when required | Return worker-token auth error; do not require Sa-Token login. |

### 5. Good/Base/Bad Cases

- Good: frontend login stores the backend token and user profile, then routes by
  role without treating the menu as the authority.
- Good: backend enforces the same role boundary even when a user crafts direct
  API calls.
- Base: seed users are acceptable for CP3 local/demo flow; CP4 can add full
  admin user management.
- Bad: let applicants query `/result/reviewer` and rely on frontend hiding
  fields.
- Bad: require a human login token for Python Worker polling or result callback.

### 6. Tests Required

- Java controller/service tests for login success/failure and `/auth/me`.
- Java tests for unauthenticated business API rejection.
- Java tests that applicant A cannot see applicant B's task/result.
- Java tests that reviewer sees only reviewer-visible statuses and cannot
  submit an applicant-owned task.
- Java tests that Worker endpoints still work with `X-Worker-Token`.
- Frontend tests that business `401` clears auth state.
- Frontend adapter/page tests that applicant result flow uses applicant
  projection and reviewer result preserves `extractedFields[]`.

### 7. Wrong vs Correct

#### Wrong

```java
@GetMapping("/{taskId}/result/reviewer")
public R<ReviewerResultResponse> getReviewerResult(...) {
    return R.ok(reviewTaskService.getReviewerResult(taskId, sessionId));
}
```

without checking the current role.

#### Correct

```java
ReviewerResultResponse response =
    reviewTaskService.getReviewerResult(taskId, sessionId, authService.currentUser());
```

and the service rejects non-reviewer/non-admin users with `403`.

---

## CP3 Python FastAPI Review Task Contract

CP3-B adds a FastAPI task entry while keeping the existing Worker polling and
Java callback contract as the source of truth.

### 1. Scope / Trigger

- Trigger: Python FastAPI routes, `INTERNAL_API_TOKEN`, review task DTOs,
  background processing, shared Worker/FastAPI orchestration, or Java-to-Python
  task dispatch.
- Python package: `python-services/smart-water-approval-review-system-py`.

### 2. Signatures

FastAPI service:

```bash
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

Health:

```http
GET /health
```

Create task:

```http
POST /api/review/tasks
X-Internal-Token: <INTERNAL_API_TOKEN, if configured>
Content-Type: application/json
```

```json
{
  "taskId": "SW123",
  "sessionId": "session-token",
  "materials": [
    {
      "materialType": "APPLICATION_FORM",
      "originalFileName": "apply.pdf",
      "storageKey": "SW123/APPLICATION_FORM/file.pdf",
      "fileExtension": "pdf",
      "uploaded": true
    }
  ],
  "idempotencyKey": "optional"
}
```

```json
{
  "aiTaskId": "SW123",
  "status": "QUEUED",
  "createdAt": "2026-05-26T03:00:00Z"
}
```

Query task:

```http
GET /api/review/tasks/{aiTaskId}
X-Internal-Token: <INTERNAL_API_TOKEN, if configured>
```

### 3. Contracts

| Item | Contract |
|---|---|
| `INTERNAL_API_TOKEN` | Optional internal token for FastAPI review-task APIs; when empty, only local/dev unauthenticated calls are allowed. |
| `X-Internal-Token` | Required only when `INTERNAL_API_TOKEN` is non-empty. |
| JSON casing | FastAPI wire contract uses camelCase; Python internals may use snake_case with Pydantic aliases. |
| `aiTaskId` | CP3 uses Java `taskId` as the FastAPI task ID for traceability. |
| Task store | In-memory only for CP3; Java persistence remains authoritative. |
| Background work | `POST /api/review/tasks` returns `202` after queuing processing. |
| Status sync | Background processing first tries Java `/task/{taskId}/status` -> `PROCESSING`. |
| Result writeback | Final result still goes through Java `/task/{taskId}/result` with `X-Worker-Token`. |
| Worker polling | Existing `SmartWaterWorker` keeps `/task/pending` polling and reuses the same orchestrator. |
| Knowledge pack | FastAPI loads the static MVP knowledge pack and copies its version into result callbacks. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Wrong `X-Internal-Token` when configured | FastAPI returns HTTP `403`; do not start background processing. |
| Unknown `aiTaskId` on query | FastAPI returns HTTP `404`. |
| Knowledge pack missing on `/health` | Return `status=degraded`; do not crash the service process. |
| Java status sync fails | Continue processing but log a warning; final callback may still succeed. |
| Java result callback fails after retries | Mark FastAPI in-memory task `FAILED` and attempt Java status `FAILED`. |
| Agent/LLM returns failure category or throws | Return `PARTIAL_SUCCESS` with rules fallback and reviewer-only manual-review notice. |

### 5. Good/Base/Bad Cases

- Good: Java can dispatch a task to FastAPI, while frontend still polls Java and
  never calls Python directly.
- Good: Worker polling and FastAPI dispatch share `ReviewTaskOrchestrator`, so
  fallback and callback behavior do not diverge.
- Base: FastAPI task state is process-local; restart loses FastAPI query history
  but Java remains authoritative.
- Bad: create a separate FastAPI result schema that cannot be written to Java
  `/task/{taskId}/result`.
- Bad: let ordinary tests require a live OCR/LLM/backend service.

### 6. Tests Required

- FastAPI tests for health, task creation, status query, camelCase aliases,
  `403` token rejection, and `404` unknown task.
- Orchestrator tests for rule issue merge, Agent failure fallback, applicant vs
  reviewer result separation, and `knowledgePackVersion` propagation.
- Worker/result writer tests remain green after reusing the orchestrator.
- Lock and dependency check after adding FastAPI/uvicorn:

```bash
uv lock --check
uv run ruff check src tests
uv run mypy src
uv run python -m compileall src main.py
uv run pytest -q tests/test_fastapi_app.py tests/test_review_orchestrator.py tests/test_result_writer.py tests/test_review_adapter.py tests/test_ocr_adapter.py
```

### 7. Wrong vs Correct

#### Wrong

```python
class CreateReviewTaskRequest(BaseModel):
    task_id: str
```

and require Java to send `task_id`.

#### Correct

```python
class CreateReviewTaskRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    task_id: str = Field(alias="taskId")
```

so the wire contract remains camelCase.

---

## Forbidden Patterns

- Do not introduce alternate enum names such as `WATER_INTAKE_APPLICATION` unless the contract is updated everywhere.
- Do not expose `reviewerResult` directly on applicant pages.
- Do not treat AI `draftOpinion` as a final administrative decision.
- Do not let Python Worker own object storage persistence policy.
- Do not make ordinary unit tests require a running RustFS instance or real object-storage credentials.
- Do not log raw OCR text, full prompts, ID-card numbers, or full business-license recognition text.
- Do not drop task state when file reading, OCR, PDF parsing, or future Word parsing fails; map failures to retryable processing errors, `PARTIAL_SUCCESS`, or `FAILED`.
