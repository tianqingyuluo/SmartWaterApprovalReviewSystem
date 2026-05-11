# Research: GLM OCR API contract

- Query: Official GLM OCR / Zhipu BigModel OCR API contract for replacing the Python Worker OCR call that currently posts `model: "glm-4v"` to `/chat/completions`.
- Scope: mixed
- Date: 2026-05-11

## Findings

### Short Answer

The official GLM OCR model id is `glm-ocr`, and its documented API path is `POST https://open.bigmodel.cn/api/paas/v4/layout_parsing`. The GLM-OCR request body is not the OpenAI-style chat schema used by the current adapter. It takes a top-level `model` and `file` string, where `file` is a URL or base64 document/image payload.

The current adapter is therefore not a drop-in model-name fix. It currently sends `messages`, `image_url` / `file_url`, and reads `choices[0].message.content`, but the official layout parsing response returns top-level OCR fields such as `md_results`, `layout_details`, `data_info`, `usage`, and `request_id`.

### Files Found

- `python-services/smart-water-approval-review-system-py/src/adapters/ocr_adapter.py` - `GlmOcrAdapter` builds image/PDF OCR payloads and calls BigModel.
- `python-services/smart-water-approval-review-system-py/src/config.py` - existing `OCR_GLM_BASE_URL` default already points at `https://open.bigmodel.cn/api/paas/v4`.
- `python-services/smart-water-approval-review-system-py/src/services/field_extractor.py` - downloads material bytes, calls `GlmOcrAdapter.extract_fields(...)`, and expects `ExtractedField[]`.
- `python-services/smart-water-approval-review-system-py/.env.example` - documents OCR provider, key, and base URL.
- `python-services/smart-water-approval-review-system-py/WORKER_API.md` - user-facing Worker startup docs and processing flow mention GLM OCR.
- `.trellis/tasks/05-11-fix-ocr-model-selection/prd.md` - task requires stopping use of `glm-4v` while keeping `ExtractedField[]`.

### Code Patterns

- `ocr_adapter.py:49` and `ocr_adapter.py:67` hard-code `model: "glm-4v"` for both image and PDF.
- `ocr_adapter.py:55` sends image bytes as an OpenAI-style `image_url` content block with a `data:image/png;base64,...` URL.
- `ocr_adapter.py:73` sends PDF bytes as an OpenAI-style `file_url` content block with a `data:application/pdf;base64,...` URL.
- `ocr_adapter.py:91` posts to `{OCR_GLM_BASE_URL}/chat/completions`.
- `ocr_adapter.py:97` reads `data["choices"][0]["message"]["content"]`, which matches chat completions, not GLM-OCR layout parsing.
- `config.py:13` already uses the correct BigModel v4 base URL. The path suffix should change for GLM-OCR.
- `field_extractor.py:29-36` is the boundary to preserve: it passes file bytes/name into OCR and adds `source_material`/`evidence` to each `ExtractedField`.
- `.env.example:8-11` and `WORKER_API.md:121-125`, `WORKER_API.md:199-201` should stay OCR-specific if docs are updated.

### Official GLM-OCR Contract

Primary API:

```http
POST https://open.bigmodel.cn/api/paas/v4/layout_parsing
Authorization: Bearer <token>
Content-Type: application/json
```

Request body:

```json
{
  "model": "glm-ocr",
  "file": "<url-or-base64>"
}
```

Documented request details:

- `model` is required and the available option is `glm-ocr`.
- `file` is required and supports URL or base64.
- Supported input formats are `PDF`, `JPG`, and `PNG`.
- Limits: image <= 10 MB, PDF <= 50 MB, maximum 100 pages.
- Optional parameters include `return_crop_images`, `need_layout_visualization`, `start_page_id`, `end_page_id`, `request_id`, and `user_id`.

Response body shape:

```json
{
  "id": "task_123456789",
  "created": 1727156815,
  "model": "GLM-OCR",
  "md_results": "# document title\nrecognized content...",
  "layout_details": [
    [
      {
        "index": 1,
        "label": "text",
        "bbox_2d": [0.1, 0.1, 0.5, 0.3],
        "content": "recognized text",
        "height": 800,
        "width": 600
      }
    ]
  ],
  "layout_visualization": ["<string>"],
  "data_info": {
    "num_pages": 5,
    "pages": [{"width": 600, "height": 800}]
  },
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 123,
    "total_tokens": 123
  },
  "request_id": "req_123456789"
}
```

This is not the `choices[].message.content` schema used by `/chat/completions`.

### Other Official OCR-Labeled API

There is also `POST https://open.bigmodel.cn/api/paas/v4/files/ocr`, under Tool API. It is multipart form-data and takes:

- `file`: uploaded image file such as JPG/PNG
- `tool_type`: only documented available option is `hand_write`
- `language_type`: e.g. `CHN_ENG`, `AUTO`, `ENG`, etc.
- `probability`: whether to return confidence data

Its response contains `task_id`, `message`, `status`, `words_result_num`, and `words_result[]` entries with `location`, `words`, and optional `probability`.

For this repo, `files/ocr` is a weaker fit than `layout_parsing` because the MVP accepts PDF as well as JPG/PNG, and `layout_parsing` is the documented GLM-OCR model endpoint with PDF support.

### OpenAI / Chat Completions Compatibility

Zhipu documents OpenAI SDK compatibility for chat models at base URL `https://open.bigmodel.cn/api/paas/v4/`, and examples use `client.chat.completions.create(...)` or `POST /chat/completions`.

Official multimodal chat model docs such as `glm-5v-turbo` and `glm-4.6v-flash` do show `/chat/completions` requests with `image_url` and `file_url` content blocks, including PDF file examples. That is a chat-compatible VLM path, not the documented GLM-OCR path.

I did not find an official `glm-ocr` example using `/chat/completions`. The GLM-OCR model guide and API reference show `layout_parsing` / `client.layout_parsing.create(model="glm-ocr", file=...)`, and the chat completions API reference does not expose `glm-ocr` as the OCR contract. Treat `glm-ocr` as not OpenAI-chat-compatible unless Zhipu publishes a contrary contract.

### External References

- GLM-OCR model guide: https://docs.bigmodel.cn/cn/guide/models/vlm/glm-ocr
  - Lists GLM-OCR as a professional OCR model.
  - Inputs: PDF and JPG/PNG images, with 10 MB image and 50 MB PDF limits, up to 100 pages.
  - Shows `POST https://open.bigmodel.cn/api/paas/v4/layout_parsing` and SDK `client.layout_parsing.create(model="glm-ocr", file=...)`.
- Layout parsing API reference: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E7%89%88%E9%9D%A2%E8%A7%A3%E6%9E%90
  - Authoritative request/response schema for `glm-ocr`.
  - Documents `Authorization: Bearer <token>`, JSON body, file limits, page range fields, and top-level OCR response fields.
- OCR service API reference: https://docs.bigmodel.cn/api-reference/%E5%B7%A5%E5%85%B7-api/ocr-%E6%9C%8D%E5%8A%A1
  - Multipart image OCR tool endpoint at `/files/ocr`; useful for image line recognition, but not the best fit for PDF MVP materials.
- OpenAI API compatibility: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
  - Confirms the BigModel OpenAI-compatible base URL and `chat.completions.create(...)` usage for chat models.
- GLM-5V-Turbo guide: https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5v-turbo
  - Shows chat-compatible multimodal `image_url` and `file_url` examples, including a PDF file example, for `model: "glm-5v-turbo"`.
- GLM-4.6V-Flash guide: https://docs.bigmodel.cn/cn/guide/models/free/glm-4.6v-flash
  - Shows chat-compatible multimodal examples for `model: "glm-4.6v-flash"`.

### Related Specs

- `.trellis/spec/backend/index.md` - Python Worker and backend boundary changes must follow SmartWater backend specs.
- `.trellis/spec/backend/smartwater-mvp-contracts.md:57-63` - MVP accepted file types are JPG/JPEG/PNG/PDF.
- `.trellis/spec/backend/smartwater-mvp-contracts.md:187-193` - Python Worker owns OCR, field extraction, review reasoning, and writeback.
- `.trellis/spec/backend/smartwater-mvp-contracts.md:224-230` - OCR/PDF parsing failures must not lose task state.
- `.trellis/spec/backend/smartwater-mvp-contracts.md:241` - Python Worker owns OCR/extraction confidence.
- `.trellis/spec/backend/smartwater-mvp-contracts.md:329-330` - Do not log raw OCR text or drop task state on OCR/PDF parsing failure.
- `.trellis/tasks/05-11-fix-ocr-model-selection/prd.md:19-21` - Open question asks whether the OCR API is compatible with `/chat/completions`; answer: no for the documented GLM-OCR contract.

### Recommendation For This Repo

For the stated task goal, replace the OCR adapter's BigModel call with `POST {OCR_GLM_BASE_URL}/layout_parsing`, request body `{"model": "glm-ocr", "file": <base64-or-url>}`, and parse the top-level layout parsing response. Keep `OCR_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`; only the endpoint suffix and payload/response parser need to change.

Because the official GLM-OCR API reference does not list `messages`, `prompt`, `response_format`, `image_url`, or `file_url` request parameters, preserving the current single-call prompt-driven `{"fields": [...]}` output is not guaranteed. Implementation options:

1. Use `glm-ocr` layout parsing as the OCR step, then map `md_results`/`layout_details` into the existing `ExtractedField[]` contract.
2. If custom field extraction must remain prompt-driven in one model call, use a supported chat-compatible VLM such as `glm-5v-turbo` or `glm-4.6v-flash`, but that is not the GLM-OCR interface requested by the task.
3. If high-quality OCR plus custom field JSON is required, use a two-step flow: GLM-OCR layout parsing first, then a text/chat extraction step over OCR text. That preserves the domain field schema but is broader than a pure endpoint/model selection fix.

Regression tests should assert:

- OCR requests no longer contain `glm-4v`.
- OCR requests no longer post to `/chat/completions` when using GLM-OCR.
- The GLM-OCR request body uses top-level `model: "glm-ocr"` and `file`.
- Mocked GLM-OCR responses with `md_results` / `layout_details` are converted into `ExtractedField[]` without leaking raw OCR text to logs.

## Caveats / Not Found

- I found no official `glm-ocr` `/chat/completions` request schema.
- The GLM-OCR model guide mentions structured JSON extraction as a capability/example, but the API reference for `layout_parsing` does not document a `prompt`, `messages`, or `response_format` parameter. Do not assume the current `_STANDARD_PROMPT` can be sent to GLM-OCR unless Zhipu documents another endpoint.
- The layout parsing docs say `file` supports base64, but the examples use URLs. They do not explicitly confirm whether a `data:<mime>;base64,...` prefix is accepted. Safest implementation is to send the base64 string form expected by the API, or use a URL if available.
- No live API call was made; this research is based on official documentation only.
