# Review Reasoning Adapter Contract

> Provider-neutral contract for SmartWater AI review reasoning.

---

## Provider Decision

MVP provider selection:

- Primary: Alibaba Cloud Model Studio / DashScope / Qwen.
- Fallback: DeepSeek.

The adapter must hide provider differences from the rest of the Python Worker. Java backend, frontend, and knowledge pack must not depend on provider-specific request fields.

---

## Configuration Surface

Use environment-driven configuration:

| Variable | Required | Notes |
|---|---:|---|
| `REVIEW_LLM_PROVIDER` | Yes | Default `dashscope`; fallback `deepseek`. |
| `REVIEW_LLM_MODEL` | Yes | Team-confirmed Qwen model for primary; team-confirmed DeepSeek model for fallback. |
| `REVIEW_LLM_BASE_URL` | Yes | OpenAI-compatible endpoint. |
| `REVIEW_LLM_API_KEY` | Yes | Provider API key. |

Provider-specific behavior belongs inside the adapter wrapper:

- DashScope region/base URL details.
- Qwen `response_format` with `json_schema` and `strict: true` when supported.
- DeepSeek JSON Mode plus tool-calling strict handling when used as fallback.
- Provider request IDs, finish reasons, token usage, rate-limit errors, and retryable upstream failures.

---

## ReviewReasoningRequest

The Worker should call the adapter with structured inputs, not raw full-document prompts.

Required fields:

| Field | Type | Notes |
|---|---|---|
| `submissionId` | string | Backend task/submission ID. |
| `sessionId` | string | Query token paired with task ID. |
| `materialSlots` | array | Fixed `APPLICATION_FORM`, `BUSINESS_LICENSE`, `ID_CARD` slots. |
| `extractedFields` | array | OCR/extraction field values, confidence, source material, and evidence references. |
| `missingMaterials` | `MaterialType[]` | Missing fixed slots. |
| `knowledgeFragments` | array | Material checklist, field rules, legal basis, and prompt fragments. Each item must include `sourceId` and `sourceTitle`. |
| `reviewMode` | string | MVP fixed value: `ASSISTIVE_REVIEW`. |
| `outputLanguage` | string | MVP fixed value: `zh-CN`. |

Rules:

- Pass OCR summaries and evidence snippets instead of full raw OCR text whenever possible.
- Include only knowledge fragments that may be cited by `basisRefs`.
- Do not include secrets, signed URLs with long validity, or unnecessary personal data in the model prompt.

---

## ReviewReasoningResult

The adapter must return locally schema-valid JSON before the Worker writes results back.

Required top-level fields:

| Field | Type | Notes |
|---|---|---|
| `summary` | string | Concise material and review summary. |
| `issues` | array | Review findings. |
| `riskHints` | array | Manual attention hints. |
| `draftOpinion` | string | Assistive review wording only. |
| `materialCompleteness` | object | Received, missing, and unrecognized material status. |
| `extractedFields` | array | Reviewer-only OCR/extraction field snapshot; Java exposes it from `reviewerResult`, not `applicantResult`. |
| `basisRefs` | array | Cited basis references from input `knowledgeFragments`. |
| `manualReviewNotice` | string | Explicit notice that AI does not make final approval decisions. |
| `modelMetadata` | object | Provider, model, request ID, finish reason, token usage. |
| `toolCallTraces` | array | Reviewer-only MCP Client trace snapshot; required for CP3.5 real-chain evidence. |

`issues[]` fields:

- `code`
- `severity`
- `message`
- `materialType`
- `fieldKey`
- `basisRefs`
- `applicantVisible`

`riskHints[]` fields:

- `riskLevel`
- `description`
- `basisRefs`
- `requiresManualReview`

---

## Prompt And Output Constraints

- System prompt must state that the model is a water-permit material review assistant.
- The model must not output final approval, rejection, or administrative decision language.
- Output must use provider-native structured output when available.
- Always validate output locally against SmartWater review JSON schema before writeback.
- Run at most one repair prompt for invalid JSON or schema mismatch.
- If repair still fails, return `SCHEMA_MISMATCH` instead of writing partial invalid results.
- `basisRefs` may only cite input knowledge fragments. Do not allow invented regulation names, article numbers, or source IDs.
- The adapter should accept provider variations that are still semantically valid:
  fenced JSON, a single wrapper object such as `review_result` / `result` /
  `data`, camelCase keys, and observed Qwen Chinese labels such as
  `材料完整性`, `字段问题`, `一致性风险`, and `审核意见草稿`.
- Normalization may fill safe defaults for missing `summary`,
  `manualReviewNotice`, `riskHints`, or top-level `basisRefs`, but it must not
  accept invented `basisRefs` or partial invalid issue objects.

---

## Failure Categories

Use these categories at the Python Worker / Java boundary:

```json
[
  "AUTH_ERROR",
  "RATE_LIMIT",
  "TIMEOUT",
  "UPSTREAM_5XX",
  "INVALID_JSON",
  "SCHEMA_MISMATCH",
  "CONTENT_FILTERED",
  "UNSUPPORTED_CAPABILITY"
]
```

Retry policy:

- Retry: `TIMEOUT`, `RATE_LIMIT`, `UPSTREAM_5XX`.
- Do not retry: `AUTH_ERROR`, `CONTENT_FILTERED`, `UNSUPPORTED_CAPABILITY`.
- For `INVALID_JSON` / `SCHEMA_MISMATCH`, run one repair pass, then fail deterministically.
- Use bounded exponential backoff and preserve request IDs for debugging.

Logging policy:

- Log provider, model, provider request ID, token usage, finish reason, retry count, latency, and redacted input summary.
- Do not log raw ID-card numbers, full OCR text, full business-license text, or full prompts.
- Do not log `sessionId`, tokens, raw provider exception text, or signed download
  URLs. Log failure category and exception class instead.

---

## Scenario: Rules/RAG/Agent Orchestration Fallback

### 1. Scope / Trigger

- Trigger: changing `ReviewTaskOrchestrator`, Agent failure handling, RAG
  fragment assembly, or Worker/FastAPI shared processing.

### 2. Signatures

```python
ReviewTaskOrchestrator.process_task(task_data: dict[str, Any]) -> ProcessingResult
```

`task_data` uses Java/FastAPI camelCase keys:

```json
{
  "taskId": "SW123",
  "sessionId": "session-token",
  "materials": []
}
```

### 3. Contracts

| Item | Contract |
|---|---|
| Extraction | Uploaded material slots are downloaded/OCRed through `FieldExtractor`; extraction errors become reviewer-only issues. |
| Rules | Material completeness checks always run before Agent review. |
| RAG | Knowledge search may narrow fragments, but prompt fragments from the static pack can be appended for model constraints. |
| Agent success | Merge rule issues with Agent issues and keep only one deduped issue per semantic key. |
| Agent failure | Return rules fallback with `MODEL_UNCERTAIN`, `manualReviewNotice`, and `requiresManualReview=true` risk hint. |
| Status | Missing materials may produce `PARTIAL_SUCCESS`; CP3-era fallback used `PARTIAL_SUCCESS` for some technical failures, but CP3.5 code must map OCR/download/MCP/LLM technical failure to `FAILED`. |
| Applicant projection | Applicant result contains applicant-visible issues only and never contains `extractedFields`. |
| Reviewer projection | Reviewer result contains `extractedFields`, rules issues, Agent issues, risk hints, draft opinion, and manual review notice. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| No usable extracted fields | Fallback to rules result and mark `PARTIAL_SUCCESS`. |
| Adapter returns `AUTH_ERROR` / `RATE_LIMIT` / other failure issue | Fallback to rules result and add reviewer-only `MODEL_UNCERTAIN`. |
| OCR/download/extraction error field appears | Keep processing other materials and add reviewer-only issue. |
| Knowledge search returns no usable fragments | Fall back to normalized static pack fragments. |

### CP3.5 Guardrail

The fallback behavior above documents the CP3-era compatibility path. It is not sufficient as final CP3.5 real-chain acceptance evidence.

For CP3.5 real-chain runs:

- Agent, LLM, MCP, OCR, or Java writeback failure must be surfaced as failed, retryable, or blocked instead of being persisted or displayed as AI review success.
- Rules-only results may be retained as diagnostic context or manual-review hints, but the payload must explicitly say the intelligent review dependency was unavailable.
- A PR or evidence document must not claim real AI review success unless it includes model metadata, cited basis, tool-call trace, and real extracted material input.
- Unit tests may still mock the adapter to cover schema and error branches, but final CP3.5 E2E evidence must use real online dependencies.

### 5. Good/Base/Bad Cases

- Good: missing ID card produces applicant-visible missing-material issue, while
  Agent failure details stay reviewer-only.
- Good: fallback text names a sanitized failure category, not raw provider
  exception text.
- Base: if the Agent succeeds but materials are incomplete, result remains
  `PARTIAL_SUCCESS`.
- Bad: raise an exception from orchestrator and lose all rule findings.
- Bad: put raw OCR text or raw provider exception text into applicant result.

### 6. Tests Required

- Orchestrator unit test for Agent failure fallback.
- Orchestrator unit test for rules + Agent success merge.
- Result writer test that applicant/reviewer payloads serialize camelCase.

### 7. Wrong vs Correct

#### Wrong

```python
return ReviewResult(summary=f"审核推理失败: {exc}")
```

#### Correct

```python
return ReviewResult(
    summary="规则检查完成，Agent汇总不可用，已降级为规则结果",
    issues=[Issue(code="MODEL_UNCERTAIN", applicant_visible=False)],
    manual_review_notice="AI审核服务不可用或输出异常，已回退为规则检查结果，请人工复核。",
)
```

## Scenario: CP3.5 MCP Client Trace And Model Output Normalization

### 1. Scope / Trigger

- Trigger: changing `SmartWaterMcpClient`, `ReviewTaskOrchestrator`,
  `ReviewReasoningAdapter`, result writeback, Java reviewer projection, or
  frontend reviewer result display.
- Goal: prove that the Agent path calls MCP through a real client boundary and
  that provider-specific JSON variations are normalized before Java writeback.

### 2. Signatures

MCP client configuration:

```env
MCP_SERVER_COMMAND=python
MCP_SERVER_ARGS="-m src.mcp_server.app --transport stdio"
MCP_SERVER_CWD=/path/to/python-service
MCP_SERVER_ENV="KNOWLEDGE_PACK_DIR=./knowledge_pack,LOG_LEVEL=INFO"
```

Python model fields:

```python
class ToolCallTrace(BaseModel):
    tool_name: str
    input_summary: str = ""
    output_summary: str = ""
    source_refs: list[str] = Field(default_factory=list)
    status: str = "SUCCESS"
    latency_ms: int | None = None
    error: str | None = None
```

Worker reviewer payload:

```json
{
  "reviewerResult": {
    "modelMetadata": {
      "provider": "dashscope",
      "model": "qwen-max",
      "requestId": "chatcmpl-...",
      "finishReason": "stop",
      "tokenUsage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    },
    "toolCallTraces": [
      {
        "toolName": "knowledge_search",
        "inputSummary": "query='APPLICATION_FORM ...', top_k=8",
        "outputSummary": "total=8, ids=[...]",
        "sourceRefs": ["BASIS_FIELD_APPLICANT_IDENTITY"],
        "status": "SUCCESS",
        "latencyMs": 120,
        "error": null
      }
    ]
  }
}
```

Reviewer query:

```http
GET /api/task/{taskId}/result/reviewer?sessionId=<sessionId>
```

### 3. Contracts

| Item | Contract |
|---|---|
| MCP discovery | `ReviewTaskOrchestrator` must call `list_tools` and verify `knowledge_search` plus `check_completeness` exist before review. |
| Completeness | Material completeness checks go through `SmartWaterMcpClient.check_completeness_sync`; do not call `SmartWaterKnowledgeTools` directly in the orchestrator. |
| RAG | Knowledge fragments for the LLM come from `SmartWaterMcpClient.knowledge_search_sync` plus static prompt fragments when needed. |
| Trace storage | `toolCallTraces` are reviewer-only and serialized as camelCase in `reviewerResult`. |
| Trace redaction | Trace input/output summaries must be short summaries, not full material text, tokens, storage keys, or signed URLs. |
| Model metadata | Real AI review success must include provider, model, request ID, finish reason, and token usage where available. |
| Output normalization | The adapter may normalize fenced JSON, wrapper keys, camelCase keys, and known Chinese key aliases to the canonical snake_case schema. |
| Basis validation | Every normalized `basis_refs` value must still be in the supplied knowledge fragment ID set, or be a safe alias that maps back to one supplied ID. |
| Failure semantics | MCP/OCR/download/LLM technical failure maps to `FAILED`; missing materials alone may produce `PARTIAL_SUCCESS`. |

Basis reference alias normalization:

- Accept brackets around IDs, for example `[BASIS_FIELD_APPLICANT_IDENTITY]`
  and `【BASIS_FIELD_APPLICANT_IDENTITY】`.
- Accept `sourceTitle` aliases from the supplied knowledge fragments, including
  file-extension-stripped titles.
- Accept prefix aliases before `:` / `：` when the prefix maps to exactly one
  supplied fragment alias, for example `申请书: 申请人基本情况`.
- Accept strings that contain one of the supplied source IDs.
- Reject any value that cannot be canonicalized to the request's
  `knowledgeFragments[].sourceId`.

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| MCP server does not expose `knowledge_search` or `check_completeness` | Orchestrator raises a technical failure; do not internally fall back to direct function calls as success evidence. |
| MCP tool returns `isError=true`, empty content, non-JSON content, or an unexpected shape | Record an error trace and fail the intelligent review path. |
| LLM returns fenced JSON or a wrapper object | Extract and parse the JSON object before schema validation. |
| LLM returns Qwen Chinese keys observed in real runs | Normalize keys and issue/risk fields, then validate against canonical schema. |
| LLM returns bracketed or title-based `basis_refs` that map to supplied fragments | Canonicalize to the supplied `sourceId`, then validate. |
| LLM invents a `basisRef` outside the request fragments | Reject as `SCHEMA_MISMATCH`; do not write a polished result. |
| LLM/API/auth/schema failure remains after repair/retry | Persist failed/diagnostic result and mark task `FAILED`, not successful AI review. |
| Java reviewer result has no `toolCallTraces` | Treat as incomplete CP3.5 evidence even if unit tests pass. |

### 5. Good/Base/Bad Cases

- Good: real E2E reviewer result has `status=COMPLETED`,
  `modelMetadata`, `toolCallTraces` containing `list_tools`,
  `check_completeness`, and `knowledge_search`, plus non-empty
  `extractedFields`.
- Good: Qwen returns `材料完整性` / `字段问题` / `一致性风险`; the adapter
  normalizes them and still rejects invented basis IDs.
- Good: Qwen returns `[BASIS_FIELD_APPLICANT_IDENTITY]` or
  `申请书: 申请人基本情况`; the adapter maps the value back to the supplied
  `sourceId` before allow-list validation.
- Base: missing `ID_CARD` creates business issue and `PARTIAL_SUCCESS` while
  OCR/MCP/LLM still succeed.
- Bad: pass tests by injecting `SmartWaterKnowledgeTools` into the orchestrator
  and bypassing MCP stdio.
- Bad: display draft opinion and `COMPLETED` when the model output failed schema
  validation and no `modelMetadata` exists.

### 6. Tests Required

- Python `test_mcp_client.py`: start the local MCP stdio server, discover tools,
  call `knowledge_search`, call `check_completeness`, and assert traces exist.
- Python `test_review_adapter.py`: assert fenced JSON, wrapper objects,
  camelCase keys, Chinese Qwen keys, bracket/title basis aliases, and invented
  basis refs.
- Python orchestrator tests: assert MCP traces are attached to reviewer result
  and Agent/OCR technical failure maps to `FAILED`.
- Java service tests: assert `toolCallTraces` round-trip through stored reviewer
  JSON and `GET /result/reviewer`.
- Frontend adapter tests: assert reviewer view normalizes and exposes
  `toolCallTraces`; applicant view remains empty.
- CP3.5 final evidence: one real run crossing Java, RustFS, Python, OCR/parser,
  MCP, LLM, Java writeback, and reviewer API/frontend visibility.

### 7. Wrong vs Correct

#### Wrong

```python
completeness = SmartWaterKnowledgeTools().check_completeness(material_types)
knowledge = SmartWaterKnowledgeTools().knowledge_search(query)
```

This bypasses the MCP Client boundary and cannot be used as CP3.5 MCP evidence.

#### Correct

```python
client = SmartWaterMcpClient()
client.list_tools_sync()
completeness = client.check_completeness_sync(material_types)
knowledge = client.knowledge_search_sync(query, top_k=8)
reviewer_result.tool_call_traces = client.consume_traces()
```

The reviewer API then exposes the trace through `toolCallTraces`.

---

## Scenario: Worker Result Writeback And Field Snapshot

### 1. Scope / Trigger

- Trigger: changing Worker result writeback, Java result persistence, reviewer/applicant result projection, or OCR field snapshot shape.
- Goal: preserve the async AI review result chain from Worker callback to Java query APIs without leaking reviewer-only field data to applicant views.

### 2. Signatures

- Worker callback:

```http
PUT /api/task/{taskId}/result
X-Worker-Token: <configured token>
```

```json
{
  "status": "COMPLETED",
  "resultSummary": "材料审核完成",
  "knowledgePackVersion": "water-permit-mvp-2026-04-27",
  "applicantResult": {
    "summary": "材料审核完成",
    "issues": [],
    "materialCompleteness": {"received": [], "missing": [], "unrecognized": []}
  },
  "reviewerResult": {
    "summary": "材料审核完成",
    "issues": [],
    "riskHints": [],
    "draftOpinion": "建议人工复核。",
    "materialCompleteness": {"received": [], "missing": [], "unrecognized": []},
    "extractedFields": [
      {
        "fieldKey": "applicant.name",
        "fieldValue": "某某科技有限公司",
        "confidence": 0.93,
        "sourceMaterial": "APPLICATION_FORM",
        "evidence": "申请人：某某科技有限公司"
      }
    ],
    "manualReviewNotice": "AI审核结果为辅助建议，不构成最终审批意见。",
    "toolCallTraces": [
      {
        "toolName": "knowledge_search",
        "inputSummary": "query='营业执照', top_k=8",
        "outputSummary": "total=8, ids=[...]",
        "sourceRefs": ["BASIS_FIELD_CREDENTIAL_ID"],
        "status": "SUCCESS",
        "latencyMs": 120,
        "error": null
      }
    ]
  }
}
```

- Reviewer query:

```http
GET /api/task/{taskId}/result/reviewer?sessionId=<sessionId>
```

### 3. Contracts

| Field | Contract |
|---|---|
| `reviewerResult.extractedFields[]` | CamelCase field snapshot copied from Python `ExtractedField[]`. |
| `extractedFields[].fieldKey` | Stable logical field key, e.g. `applicant.name`. |
| `extractedFields[].fieldValue` | Extracted value; may be string, number, object, list, or null. |
| `extractedFields[].confidence` | Numeric confidence from OCR/extraction. |
| `extractedFields[].sourceMaterial` | MVP material type that produced the field. |
| `extractedFields[].evidence` | Short evidence snippet only; do not write full raw OCR text. |
| `reviewerResult.toolCallTraces[]` | CamelCase MCP Client trace snapshot copied from Python `ToolCallTrace[]`. |
| `toolCallTraces[].toolName` | MCP tool name, e.g. `list_tools`, `check_completeness`, `knowledge_search`. |
| `toolCallTraces[].inputSummary` | Short sanitized input summary; never raw prompt, token, storage key, or full material text. |
| `toolCallTraces[].outputSummary` | Short sanitized output summary. |
| `toolCallTraces[].sourceRefs` | Source IDs or knowledge refs returned by the tool when available. |
| `toolCallTraces[].status` | `SUCCESS` or `ERROR`. |
| `toolCallTraces[].latencyMs` | Integer latency in milliseconds when measured. |
| `toolCallTraces[].error` | Sanitized error class/category when the tool call fails. |
| `applicantResult` | Must not include `extractedFields`; applicant pages receive filtered issues and material completeness only. |
| `review_result` table | One row per `(task_id, result_type)`; callbacks update existing `APPLICANT` / `REVIEWER` rows. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Worker sends repeated result callback for same task/status | Java updates existing result rows; no duplicate `review_result` rows. |
| Worker sends `extractedFields` under `reviewerResult` | Java persists it inside reviewer JSON and returns it from reviewer result query. |
| Worker sends `toolCallTraces` under `reviewerResult` | Java persists it inside reviewer JSON and returns it from reviewer result query. |
| Worker omits `extractedFields` | Reviewer query returns `null` or absent field snapshot without failing result parsing. |
| Worker omits `toolCallTraces` | Reviewer query returns an empty list or absent trace snapshot; CP3.5 evidence is incomplete. |
| Worker sends `extractedFields` under `applicantResult` | Treat as contract violation in review; applicant projection must not depend on or expose it. |
| Worker sends `toolCallTraces` under `applicantResult` | Treat as contract violation in review; applicant projection must not expose tool traces. |
| Java cannot parse stored result JSON | Return controlled `BusinessException(500, "结果解析失败")`. |

### 5. Good/Base/Bad Cases

- Good: Worker builds applicant and reviewer result payloads separately; only reviewer payload includes `extractedFields` and `toolCallTraces`.
- Good: Java `saveResult` performs upsert by `(taskId, resultType)` and keeps duplicate callbacks idempotent.
- Base: Missing material findings still flow through `materialCompleteness.missing` to `missingMaterials`.
- Bad: Worker serializes Python snake_case keys such as `extracted_fields` into Java callback payload.
- Bad: Applicant APIs expose full OCR field values or evidence snippets.

### 6. Tests Required

- Python unit test: `_result_to_dict()` serializes `ReviewResult.extracted_fields` to camelCase `extractedFields`.
- Python unit test: `_result_to_dict()` serializes `ReviewResult.tool_call_traces` to camelCase `toolCallTraces`.
- Python Worker unit test: `_build_processing_result()` copies extracted fields to `reviewerResult` and leaves `applicantResult.extracted_fields` empty.
- Java service test: repeated `writeResult()` calls leave exactly two result rows (`APPLICANT`, `REVIEWER`) for the task and expose the latest content.
- Java service test: `getReviewerResult()` returns stored `extractedFields` and `toolCallTraces` from reviewer JSON.

### 7. Wrong vs Correct

#### Wrong

```python
payload["applicantResult"]["extracted_fields"] = fields
```

#### Correct

```python
payload["reviewerResult"]["extractedFields"] = [
    {
        "fieldKey": field.field_key,
        "fieldValue": field.field_value,
        "confidence": field.confidence,
        "sourceMaterial": field.source_material,
        "evidence": field.evidence,
    }
    for field in fields
]
payload["reviewerResult"]["toolCallTraces"] = [
    {
        "toolName": trace.tool_name,
        "inputSummary": trace.input_summary,
        "outputSummary": trace.output_summary,
        "sourceRefs": trace.source_refs,
        "status": trace.status,
        "latencyMs": trace.latency_ms,
        "error": trace.error,
    }
    for trace in traces
]
```
