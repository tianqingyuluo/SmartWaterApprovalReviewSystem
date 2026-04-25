# Research: inference-vendor-comparison

- Query: Compare 2-4 domestic China-accessible reasoning/chat model providers for SmartWater approval-review inference, map them to repo constraints, and recommend a primary vendor plus fallback.
- Scope: mixed
- Date: 2026-04-25

## Findings

### Repo constraints that drive the choice

- The task requires a domestic, stably accessible API provider; structured JSON output; basis citations and human-review hints; no final approval claim; and a replaceable adapter boundary: `.trellis/tasks/04-24-smartwater-review-inference-vendor-contract/prd.md:5`, `.trellis/tasks/04-24-smartwater-review-inference-vendor-contract/prd.md:17`, `.trellis/tasks/04-24-smartwater-review-inference-vendor-contract/prd.md:44`, `.trellis/tasks/04-24-smartwater-review-inference-vendor-contract/prd.md:52`.
- Parent PRD fixes the product shape to Chinese approval-assist for `申请书 + 营业执照 + 身份证`, asynchronous OCR + review inference, read-only result output, and AI as assistive advice only: `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:76`, `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:80`, `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:101`, `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:143`, `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:158`.
- OCR is already fixed to GLM OCR, but review reasoning must stay decoupled from OCR and should avoid unnecessary GLM vendor coupling: `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:127`, `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md:143`, `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md:11`, `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md:49`.
- The worker expects separate `OCR adapter` and `Review reasoning adapter`, partial-failure handling, env-based secrets, and explainable output fields: `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md:18`, `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md:43`, `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md:49`.
- The knowledge pack will provide static rule fragments and source-backed citations; the reasoning model should consume them, not replace them with opaque free-form judgment: `.trellis/tasks/04-24-smartwater-regulation-knowledge-pack-mvp/prd.md:5`, `.trellis/tasks/04-24-smartwater-regulation-knowledge-pack-mvp/prd.md:12`, `.trellis/tasks/04-24-smartwater-regulation-knowledge-pack-mvp/prd.md:49`.
- Backend specs already require explicit AI-call error messages, timeout/retry, no raw stack leaks, and log summaries without sensitive data: `.trellis/spec/backend/error-handling.md:107`, `.trellis/spec/backend/error-handling.md:108`, `.trellis/spec/backend/logging-guidelines.md:68`, `.trellis/spec/backend/logging-guidelines.md:69`.
- The Python service is still a clean skeleton with no vendor SDK committed yet, so OpenAI-compatible APIs materially reduce initial lock-in and implementation cost: `python-services/smart-water-approval-review-system-py/pyproject.toml:1`.

### Files found

- `.trellis/tasks/04-24-smartwater-review-inference-vendor-contract/prd.md`: this task's vendor-selection and adapter-contract requirements.
- `.trellis/tasks/04-23-smartwater-architecture-roadmap/prd.md`: parent product constraints and AI/OCR separation.
- `.trellis/tasks/04-24-smartwater-python-ocr-review-worker-mvp/prd.md`: worker-side adapter, failure, and secret-management expectations.
- `.trellis/tasks/04-24-smartwater-regulation-knowledge-pack-mvp/prd.md`: source-backed rules/citation packaging constraints.
- `.trellis/spec/backend/error-handling.md`: explicit timeout/retry and non-leaky error policy.
- `.trellis/spec/backend/logging-guidelines.md`: structured logging and no sensitive-data logging.
- `python-services/smart-water-approval-review-system-py/pyproject.toml`: confirms there is no existing SDK lock-in yet.

### Candidate comparison

| Provider | Evidence-backed strengths | Main risks | Fit |
|---|---|---|---|
| **Baidu Qianfan / ERNIE-4.5-Turbo-128K** | OpenAI-compatible `base_url=https://qianfan.baidubce.com/v2`; official `Function calling`; official `response_format` supports both `json_object` and `json_schema` with `strict`; `ernie-4.5-turbo-128k` exposes 128K context with high default flow control (`RPM=5000`, `TPM=400000`); pricing is low (`0.0008` yuan/1k input, `0.0032` yuan/1k output); docs position ERNIE-4.5-Turbo for Chinese knowledge QA and document understanding. | Slightly more platform ceremony than pure OpenAI-compatible vendors: API key + optional `appid` header; 128K is strong but not class-leading if full-text regulations are inlined naively. | **Recommended primary** |
| **Alibaba Cloud DashScope / Qwen family** | OpenAI-compatible endpoints including China mainland; official structured output (`response_format: {"type":"json_object"}`); official function calling; clear China-mainland deployment/data locality option; model lineup spans `qwen3-max` and 1M-context `qwen3.5-plus`/`qwen3.5-flash`; explicit rate-limit docs and pricing docs; account-level operational controls are clear. | In reviewed sources, structured output was explicit for `json_object`, but I did not find an equally explicit `json_schema`-strict page like Qianfan's; model choice is wider, so teams can over-optimize too early unless one production model is pinned. | **Best fallback / long-context fallback** |
| **Moonshot / Kimi K2.5-K2.6** | OpenAI-compatible API; official JSON Mode; official ToolCalls; 256K context; strong long-context/doc handling reputation in Chinese workflows; context caching supported. | Rate limits are tied to cumulative recharge; minimum paid top-up is required; official docs show thinking-mode tool restrictions (`tool_choice` limited to `auto`/`none` in some cases); reviewed docs expose JSON Mode but not schema-strict JSON comparable to Qianfan. | **Usable, but not first choice for schema-strict approval output** |
| **Tencent Hunyuan** | OpenAI-compatible endpoint; official function-calling examples; domestic cloud procurement fit; current text models include 128K/224K-class variants and low-cost Turbo/T1 options. | OpenAI-compatible docs explicitly mention default shared concurrency of 5; in reviewed official docs I did not find a dedicated `json_schema`/strict structured-output page comparable to Qianfan; common OpenAI-compatible examples focus more on chat/tool use than schema-constrained extraction. | **Enterprise alternative, not MVP default** |

### Why the recommendation is Qianfan first

- **Best match for the output contract**: SmartWater needs parse-safe review JSON with issue lists, citations, summaries, and human-review hints. Qianfan is the strongest reviewed option because it officially supports both `json_object` and `json_schema` with strict mode, reducing downstream parser fragility.
- **Best documented fit for Chinese document understanding**: Qianfan's model list explicitly positions `ERNIE-4.5-Turbo-128K` for Chinese knowledge QA and document understanding. No reviewed vendor published a water-approval-specific benchmark, so this part is still an inference, but Qianfan has the clearest official positioning closest to the task.
- **128K is enough for MVP if the prompt is assembled correctly**: the MVP only handles three material slots plus static knowledge snippets, not arbitrary case archives. With OCR text chunking and quote extraction, 128K is operationally sufficient.
- **Operationally easy for a new worker**: OpenAI-compatible SDK path, high default RPM/TPM, low token price, optional `appid` accounting, and permanent API-key flow are all practical for an async worker.
- **Vendor replacement risk stays acceptable**: the adapter can still stay provider-neutral because the worker only needs OpenAI-compatible chat completion, structured-output mode, and standardized retries.

### Recommended fallback

- **Fallback vendor: Alibaba Cloud DashScope / Qwen family**
- Use DashScope if one of these happens during evaluation:
  - ERNIE quality on Chinese regulation reasoning is acceptable but not best.
  - Long-context pressure becomes real after adding more regulation excerpts or multi-document history.
  - The team wants clearer China-mainland cloud operations and rate-limit controls on Alibaba Cloud.
- Suggested model policy:
  - Start evaluation with a quality-oriented Qwen model for review generation.
  - Drop to a cheaper long-context Qwen model only if latency/cost dominates and result quality is still acceptable.

### Reasons to reject or defer non-chosen options

- **Kimi not chosen as primary**: strong long-context and Chinese interaction quality, but the official docs reviewed expose JSON Mode rather than schema-strict JSON; rate limits are recharge-tier-based; thinking-mode tool restrictions add worker complexity.
- **Tencent Hunyuan not chosen as primary**: OpenAI compatibility and tool calling are there, but the reviewed docs were weaker on strict structured output, and the documented default shared concurrency of 5 is a practical MVP throughput constraint.
- **Zhipu GLM deferred even though it is capable**: official docs show OpenAI compatibility, function calling, and structured output, but using GLM for reasoning would increase the exact vendor coupling the task is trying to avoid because OCR is already GLM OCR.
- **Direct DeepSeek API deferred for first integration**: the API is OpenAI-compatible and inexpensive, but official docs explicitly note 429/503 overload scenarios and long waits under traffic pressure. It remains a good later benchmark target, but not the first production recommendation for a government-style review workflow.

### Adapter and operations implications

- Use a provider-neutral config surface:
  - `REVIEW_LLM_PROVIDER`
  - `REVIEW_LLM_MODEL`
  - `REVIEW_LLM_BASE_URL`
  - `REVIEW_LLM_API_KEY`
  - `REVIEW_LLM_APP_ID` (optional; Qianfan only)
- Keep the worker on OpenAI-compatible chat completions first; only the provider wrapper should know about Qianfan `appid`, DashScope region URL, or Kimi `extra_body.thinking`.
- Prefer provider-native structured output when available, but **always** validate locally against the SmartWater review JSON schema before writeback.
- Retry policy should be provider-neutral:
  - Retry: timeout, 429, 500, 503.
  - Do not retry: auth failure, schema validation failure after one repair pass, explicit content filter rejection.
  - Use bounded exponential backoff with request ID logging.
- Error categories for Java/Python boundary:
  - `AUTH_ERROR`
  - `RATE_LIMIT`
  - `TIMEOUT`
  - `UPSTREAM_5XX`
  - `INVALID_JSON`
  - `SCHEMA_MISMATCH`
  - `CONTENT_FILTERED`
  - `UNSUPPORTED_CAPABILITY`
- Logging should store provider/model/request ID, token usage, finish reason, retry count, and a redacted input summary; never log raw ID-card numbers or full OCR text.

### Related specs

- `.trellis/spec/backend/error-handling.md`
- `.trellis/spec/backend/logging-guidelines.md`

### External references

- Baidu Qianfan OpenAI SDK compatibility: https://cloud.baidu.com/doc/qianfan/s/Hmh4suq26
- Baidu Qianfan model list: https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j
- Baidu Qianfan structured output: https://cloud.baidu.com/doc/qianfan-docs/s/6m8r1x5hz
- Baidu Qianfan function calling: https://cloud.baidu.com/doc/qianfan-docs/s/xm95lyys5
- Baidu Qianfan pricing: https://cloud.baidu.com/doc/qianfan-docs/s/Jm8r1826a
- Alibaba Cloud Qwen API reference / OpenAI compatibility: https://www.alibabacloud.com/help/en/model-studio/use-qwen-by-calling-api
- Alibaba Cloud structured output: https://www.alibabacloud.com/help/en/model-studio/qwen-structured-output
- Alibaba Cloud function calling: https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling
- Alibaba Cloud supported models and context/pricing overview: https://www.alibabacloud.com/help/en/model-studio/getting-started/models
- Alibaba Cloud rate limits: https://www.alibabacloud.com/help/en/model-studio/rate-limit
- Kimi API overview: https://platform.kimi.ai/docs/api/overview
- Kimi JSON Mode: https://platform.kimi.ai/docs/guide/use-json-mode-feature-of-kimi-api
- Kimi Tool Calls: https://platform.kimi.ai/docs/guide/use-kimi-api-to-complete-tool-calls
- Kimi pricing and limits: https://platform.kimi.ai/docs/pricing/chat-k25 , https://platform.kimi.ai/docs/pricing/limits
- Tencent Hunyuan OpenAI-compatible examples: https://cloud.tencent.com/document/product/1729/111007
- Tencent Hunyuan product overview and model list: https://cloud.tencent.com/document/product/1729/104753
- Tencent Hunyuan pricing: https://cloud.tencent.com/document/product/1729/97731
- Zhipu OpenAI compatibility: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
- Zhipu structured output: https://docs.bigmodel.cn/cn/guide/capabilities/struct-output
- Zhipu tool calling: https://docs.bigmodel.cn/cn/guide/capabilities/function-calling
- DeepSeek quick start: https://api-docs.deepseek.com/
- DeepSeek chat completion / tool strictness: https://api-docs.deepseek.com/api/create-chat-completion
- DeepSeek pricing: https://api-docs.deepseek.com/quick_start/pricing
- DeepSeek rate-limit and error docs: https://api-docs.deepseek.com/quick_start/rate_limit/ , https://api-docs.deepseek.com/quick_start/error_codes

## Caveats / Not Found

- No reviewed vendor publishes an official benchmark specifically for Chinese water-approval regulations or government approval-review wording. Any claim about "better regulation understanding" is therefore an inference from Chinese-language positioning, document-understanding positioning, and tool/structured-output maturity.
- For Tencent Hunyuan, I found clear OpenAI-compatible and function-calling docs, but I did not find a Qianfan-style `json_schema` strict-output page in the reviewed official sources.
- For DashScope, I found explicit structured output with `json_object` and official function calling, but not a reviewed source as explicit as Qianfan's `json_schema` strict mode page.
- Kimi's pricing pages are partially JS-rendered in the docs UI; the product home page exposes current cache/input/output prices, and the docs confirm model capabilities, but the exact full pricing table was not fully visible in the reviewed page render.
