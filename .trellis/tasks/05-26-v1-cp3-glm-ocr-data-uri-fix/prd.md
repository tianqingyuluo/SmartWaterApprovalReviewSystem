# CP3-H 修正 GLM OCR data URI 请求格式

## Scope

修正 Python Worker 中 GLM OCR 适配器调用 `layout_parsing` 的请求格式。当前 Worker 能从 Java 下载对象存储中的 PDF/JPEG 材料，但发给 GLM OCR 的 `file` 字段是裸 base64，导致有效 PDF/JPG/PNG 也返回 `400 Bad Request`。本任务只修复 OCR 请求编码与相关测试、验收证据，使 CP3 的 AI 初审链路能够拿到真实 OCR 文本。

## Problem

- Java 材料上传、对象存储保存、Worker 下载链路均已验证成功。
- 实际任务 `SW4224F94D770A40AE` 中的 PDF/JPEG 文件头和大小均合法：
  - PDF 以 `%PDF-1.7` 开头。
  - JPEG 以 `FFD8` 开头。
  - 文件大小低于 GLM OCR 限制。
- GLM OCR 对裸 base64 返回 `400`，错误信息为“仅支持 PDF、JPG、PNG、JPEG 格式；文件大小限制...”
- 同一份营业执照图片改用 `data:image/jpeg;base64,<base64>` 后 GLM OCR 返回 `200`，并识别出营业执照正文、统一社会信用代码、企业名称、法人、住所等字段。

## Deliverables

- Python OCR adapter 根据文件类型生成 GLM 需要的 data URI：
  - `pdf` -> `data:application/pdf;base64,<payload>`
  - `jpg` / `jpeg` -> `data:image/jpeg;base64,<payload>`
  - `png` -> `data:image/png;base64,<payload>`
- 保留并校验现有扩展名白名单：`pdf`、`jpg`、`jpeg`、`png`。
- OCR 请求失败时记录 GLM 返回的业务错误摘要，但不泄露 API key 或完整文件内容。
- Python 单测覆盖：
  - data URI MIME 前缀生成。
  - PDF/JPEG/PNG 映射。
  - 不支持扩展名不调用 OCR。
  - GLM 成功返回 `md_results` 时仍能转换为 `ExtractedField(field_key="ocr_markdown")`。
- CP3 验收证据补充：
  - 至少一份营业执照样例能返回 `200` 并提取真实 OCR markdown。
  - 重新提交或重跑任务后，结果页不再出现 `ocr_error: 400 Bad Request`。

## Non-Goals

- 不更换 OCR 供应商。
- 不改 GLM API key、模型选择或外部 API 账号配置。
- 不做复杂结构化字段抽取规则；本任务只保证 OCR markdown 能稳定进入后续链路。
- 不修改 Java 材料下载接口和 Worker token 边界。
- 不处理前端材料原件预览；该能力归 `v1-cp3-material-safe-preview`。

## Acceptance Criteria

- 对 PDF/JPG/JPEG/PNG 调用 GLM OCR 时，`file` 字段带正确 data URI MIME 前缀。
- 有效营业执照 JPG 调用 GLM `layout_parsing` 不再因文件格式返回 `400`。
- Worker 处理三类材料时不再把 `ocr_error` 写入 `extractedFields`，除非 GLM API 实际不可用或材料真的非法。
- OCR 成功后，`reviewerResult.extractedFields` 中出现 `ocr_markdown` 或可用版式字段。
- Python 测试通过。
- CP3 测试证据记录修复前后差异。

## Dependencies

- `v1-cp3-python-fastapi-rules-agent`
- `v1-cp3-integration-stability-tests`

## Technical Notes

- 受影响文件预计为 `python-services/smart-water-approval-review-system-py/src/adapters/ocr_adapter.py` 及其测试。
- 当前 `_extract_document` 发送：
  - `{"model": "glm-ocr", "file": "<raw-base64>"}`
- 修复后应发送：
  - `{"model": "glm-ocr", "file": "data:<mime>;base64,<raw-base64>"}`
- 真实探测结果：
  - 裸 base64：GLM 返回 `400`。
  - `data:image/jpeg;base64,...`：GLM 返回 `200`，`md_results` 包含营业执照正文。

## CP3 Boundary

本任务归入 CP3，因为它直接影响“处理非结构化文档”和“初审 Agent 与系统集成”评分点。它是 CP3 OCR 主线的 bugfix，不应扩展到 CP4 的部署降级、报告导出或材料版本能力。
