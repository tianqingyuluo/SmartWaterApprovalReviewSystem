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
    "manualReviewNotice": "AI审核结果为辅助建议，不构成最终审批意见。"
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
| `applicantResult` | Must not include `extractedFields`; applicant pages receive filtered issues and material completeness only. |
| `review_result` table | One row per `(task_id, result_type)`; callbacks update existing `APPLICANT` / `REVIEWER` rows. |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Worker sends repeated result callback for same task/status | Java updates existing result rows; no duplicate `review_result` rows. |
| Worker sends `extractedFields` under `reviewerResult` | Java persists it inside reviewer JSON and returns it from reviewer result query. |
| Worker omits `extractedFields` | Reviewer query returns `null` or absent field snapshot without failing result parsing. |
| Worker sends `extractedFields` under `applicantResult` | Treat as contract violation in review; applicant projection must not depend on or expose it. |
| Java cannot parse stored result JSON | Return controlled `BusinessException(500, "结果解析失败")`. |

### 5. Good/Base/Bad Cases

- Good: Worker builds applicant and reviewer result payloads separately; only reviewer payload includes `extractedFields`.
- Good: Java `saveResult` performs upsert by `(taskId, resultType)` and keeps duplicate callbacks idempotent.
- Base: Missing material findings still flow through `materialCompleteness.missing` to `missingMaterials`.
- Bad: Worker serializes Python snake_case keys such as `extracted_fields` into Java callback payload.
- Bad: Applicant APIs expose full OCR field values or evidence snippets.

### 6. Tests Required

- Python unit test: `_result_to_dict()` serializes `ReviewResult.extracted_fields` to camelCase `extractedFields`.
- Python Worker unit test: `_build_processing_result()` copies extracted fields to `reviewerResult` and leaves `applicantResult.extracted_fields` empty.
- Java service test: repeated `writeResult()` calls leave exactly two result rows (`APPLICANT`, `REVIEWER`) for the task and expose the latest content.
- Java service test: `getReviewerResult()` returns stored `extractedFields` from reviewer JSON.

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
```
