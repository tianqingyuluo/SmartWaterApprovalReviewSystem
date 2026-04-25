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
