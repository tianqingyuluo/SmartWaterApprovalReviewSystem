# Fix OCR model selection

## Goal

把 Python Worker 的 OCR 调用从通用 GLM 视觉模型切到 GLM OCR 接口，避免当前字段抽取误用 `glm-4v`。

## What I already know

* OCR 入口在 `python-services/smart-water-approval-review-system-py/src/services/field_extractor.py`，实际请求实现位于 `src/adapters/ocr_adapter.py`。
* 当前 `GlmOcrAdapter` 在图片和 PDF 分支里都把请求模型写成了 `glm-4v`。
* `.env.example` 和 `src/config.py` 里已经有 OCR 专用配置项 `OCR_PROVIDER` / `OCR_GLM_API_KEY` / `OCR_GLM_BASE_URL`。
* 项目后端规范要求 Python Worker 的外部 OCR 调用必须可 mock，并且变更后要有回归测试。

## Assumptions (temporary)

* 这次改动只需要修正 OCR 供应商/模型选择，不改字段抽取结果格式。
* 仍然保留现有 `GlmOcrAdapter` 和 `FieldExtractor` 的职责边界。

## Open Questions

* 已关闭：官方 GLM OCR 合约使用 `POST /layout_parsing` + `model: "glm-ocr"`，不是当前的 `/chat/completions`。

## Requirements (evolving)

* OCR 请求不再使用 `glm-4v`。
* OCR 请求应调用 `{OCR_GLM_BASE_URL}/layout_parsing`，请求体使用顶层 `model: "glm-ocr"` 和 `file` 字段。
* Worker 继续通过配置读取 OCR API key 和 base URL。
* 现有 OCR 输出结构 `ExtractedField[]` 保持不变。
* 增加或更新测试，覆盖 OCR 请求模型名/接口路径的回归。

## Acceptance Criteria (evolving)

* [ ] OCR 适配器使用官方 GLM OCR 接口或其要求的模型名，而不是 `glm-4v`。
* [ ] 现有字段抽取调用链无需修改上层服务接口。
* [ ] Python Worker 测试通过，且有针对 OCR 请求配置的回归断言。
* [ ] 必要时同步更新 `.env.example` / `WORKER_API.md` 中的 OCR 说明。

## Definition of Done

* Tests added/updated.
* Lint / typecheck / CI green.
* Docs/notes updated if behavior changes.
* Rollout/rollback considered if risky.

## Out of Scope

* 重写字段抽取 prompt。
* 改造 review adapter 或知识包结构。
* 改 Java 后端任务/结果协议。

## Technical Notes

* 任务目录：`.trellis/tasks/05-11-fix-ocr-model-selection/`
* 调研结论：`.trellis/tasks/05-11-fix-ocr-model-selection/research/glm-ocr-api.md`
* 待检查文件：`python-services/smart-water-approval-review-system-py/src/adapters/ocr_adapter.py`
* 待检查文件：`python-services/smart-water-approval-review-system-py/src/config.py`
* 待检查文件：`python-services/smart-water-approval-review-system-py/.env.example`
* 待检查文件：`python-services/smart-water-approval-review-system-py/WORKER_API.md`
