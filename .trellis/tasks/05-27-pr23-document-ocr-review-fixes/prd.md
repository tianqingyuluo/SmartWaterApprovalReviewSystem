# PR23 文档 OCR 审查问题修复

## Goal

修复 PR #23 审查暴露的两个可合并风险：前端仍拒绝 DOCX 上传，以及 PDF 已解析出短文本/表格时仍触发 OCR 并覆盖已解析字段。

## What I Already Know

- PR #23 目标分支为 `v1`，源分支为 `task/cp3-5-document-ocr-red-tests`。
- PR #23 已新增 Python `DocumentOcrPipeline`，并在 Java `ReviewTaskServiceImpl` 中放开 `docx`。
- 前端 `ACCEPTED_EXTENSIONS`、上传页面提示和错误文案仍只包含 `jpg/jpeg/png/pdf`。
- `DocumentOcrPipeline._parse_pdf` 当前只用 `total_text >= 20` 判断是否跳过 OCR，短文本表格 PDF 会继续触发 OCR。
- `_apply_ocr` 当前直接赋值 `result.extracted_fields = fields`，会覆盖已从 PDF 表格提取到的字段。

## Requirements

- 前端上传入口必须允许 `docx`，并同步提示文案和本地校验错误文案。
- PDF 解析只要已经得到结构化内容、表格或抽取字段，就不能因短文本阈值继续触发 OCR。
- OCR 追加结果时不得丢失已解析出的字段。
- 增加回归测试覆盖短文本 PDF 表格不调用 OCR、字段不丢失。
- 验证 Java/Python/前端相关测试和 lint。

## Acceptance Criteria

- [x] 从前端正常上传控件可选择并通过 `docx` 本地校验。
- [x] Java 后端仍接受 `docx` 并向 Python dispatch 传递 `docx` 扩展名。
- [x] 短文本 PDF 表格解析成功时不调用 OCR，保留表格字段。
- [x] OCR fallback 场景仍适用于空白/扫描 PDF。
- [x] 相关 Python、Java、前端检查通过或明确说明未能运行的原因。

## Verification Notes

- PR branch commit: `6b3b063 fix(cp3.5): align docx upload and pdf parser fallback`
- Python targeted tests: `uv run --extra dev python -m pytest -q tests/test_document_ocr_pipeline.py tests/test_field_extractor.py tests/test_ocr_adapter.py` passed (`14 passed, 4 subtests passed`).
- Python full tests: `uv run --extra dev python -m pytest -q` passed (`85 passed, 4 subtests passed`).
- Python lint: `uv run --extra dev ruff check src tests` passed.
- Frontend tests: `npm run test -- --run` passed (`19 passed`).
- Frontend build: `npm run build` passed.
- Java tests: `./mvnw test` passed (`93 passed`).
- Real component checks passed:
  - GLM OCR on `docs/参考资料/营业执照.jpg` succeeded and extracted `ocr_markdown`.
  - `docs/参考资料/申请书.docx` parsed with 5 blocks, 1 table, and 45 extracted fields.
  - `docs/参考资料/取水许可办理需资料及流程.docx` parsed with 50 blocks.
  - MCP demo `knowledge_search` sample completed.
- Real HTTP E2E passed for the document/OCR/writeback path:
  - Task ID: `SWD1D632319D3D48F0`.
  - Submitted materials: `申请书.docx` and `营业执照.jpg`; `ID_CARD` intentionally omitted.
  - Chain exercised: Java upload to RustFS -> Java dispatch to Python FastAPI -> Python download via Java -> DOCX parser -> real GLM OCR -> Java result writeback -> applicant/reviewer result query.
  - Final status: `PARTIAL_SUCCESS`.
  - Applicant/reviewer missing materials: `["ID_CARD"]`.
  - Reviewer extracted fields: `52`.
  - Reviewer field snapshot contains business-license code `91441303MA531L6K37`.
  - Reviewer issues include `MISSING_MATERIAL` and `MODEL_UNCERTAIN`.
- Real Review LLM limitation:
  - Direct LLM smoke reached the provider but returned schema-mismatched output.
  - E2E reviewer summary was `规则检查完成，Agent汇总不可用，已降级为规则结果`.
  - This proves the degradation path is honest, but does not prove full intelligent compliance reasoning success.

## Out Of Scope

- 不实现完整 `.doc` 转换链路。
- 不新增真实 OCR/LLM/MCP 端到端验收任务。
- 不改动 Java/Python 主动调度协议，除非修复上述问题必须触及。

## Technical Notes

- Backend specs: `.trellis/spec/backend/quality-guidelines.md`, `.trellis/spec/backend/ocr-adapter.md`, `.trellis/spec/backend/smartwater-mvp-contracts.md`, `.trellis/spec/backend/error-handling.md`
- Frontend specs: `.trellis/spec/frontend/index.md` and referenced upload/visibility conventions
- PR worktree: `/tmp/smartwater-pr23-review`
