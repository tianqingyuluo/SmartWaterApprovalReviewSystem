# OCR Adapter Contract

> SmartWater Python Worker OCR boundary and GLM OCR layout parsing contract.

---

## Scope

This guide covers `python-services/smart-water-approval-review-system-py/src/adapters/ocr_adapter.py` and the OCR portion of the Worker pipeline.

The OCR adapter is responsible for turning downloaded material bytes into `ExtractedField[]` for downstream field extraction and review writeback.

---

## Current Contract

- OCR uses the official GLM OCR layout parsing endpoint, not chat/completions.
- Request shape:
  - `POST {OCR_GLM_BASE_URL}/layout_parsing`
  - `model: "glm-ocr"`
  - `file: data URI payload with MIME prefix, for example `data:image/jpeg;base64,...` or `data:application/pdf;base64,...``
- Supported MVP extensions: `jpg`, `jpeg`, `png`, `pdf`
- `md_results` takes precedence when present and should map to a single markdown field.
- `layout_details` is the fallback structure and should map to `ExtractedField[]`.
- Unsupported file extensions return an empty extraction result and log a warning.
- Request / response failures should return a deterministic OCR error field instead of crashing the Worker boundary.
- HTTP 4xx/5xx failures should preserve a sanitized upstream error summary when possible, but must not leak API keys, bearer tokens, raw base64 payloads, or full material content.

---

## Implementation Rules

- Do not route OCR through `/chat/completions` or a vision-chat model such as `glm-4v`.
- Keep OCR provider-specific parsing inside the adapter; `FieldExtractor` should only orchestrate download plus adapter call.
- Preserve the `ExtractedField[]` contract for downstream worker logic.
- Keep OCR request logging redacted; do not log raw material content or full OCR text at INFO/WARN.

---

## Testing Rules

- Unit tests must mock `httpx.Client`.
- Tests must assert the request path and `model` value, not only the final parsed result.
- Tests must assert MIME-specific data URI encoding for `jpg` / `jpeg` / `png` / `pdf`.
- Regression coverage should fail if `glm-4v` or `/chat/completions` reappears in the OCR path.
- Response parsing tests should cover both `md_results` and `layout_details`.
- Error-path regression tests should assert sanitized OCR summaries rather than raw exception strings.
