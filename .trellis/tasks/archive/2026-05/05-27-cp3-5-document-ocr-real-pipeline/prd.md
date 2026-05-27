# CP3.5-C 生产级文档解析与 OCR

## Scope

交付真实文档处理管线，覆盖结构化文档和非结构化扫描件/图片材料。Python 必须从 Java 下载真实材料，按格式解析或 OCR，并把可用文本块与结构化字段交给后续 Agent。

## Problem

CP3 旧链路没有证明真实 OCR/LLM/对象存储联机 E2E。实际联机时，GLM OCR 因裸 base64 请求返回 400，说明此前测试没有覆盖真实外部 OCR 合同。CP3.5 需要修复这个问题，并把文档处理从“能跑测试”升级为“真实材料能产出可用内容”。

## Deliverables

- 文件类型识别和白名单：
  - PDF
  - DOCX
  - JPG/JPEG/PNG
- 结构化解析：
  - PDF 文本和表格提取。
  - DOCX 段落、表格、关键字段提取。
- 非结构化 OCR：
  - 图片和扫描 PDF 调用真实 OCR。
  - GLM `file` 字段使用 `data:<mime>;base64,<payload>`。
  - OCR 成功结果转换为统一文本块和 `extractedFields`。
- 统一输出模型：
  - `materialType`
  - `sourceFileName`
  - `contentBlocks`
  - `tables`
  - `extractedFields`
  - `ocrMetadata`
  - `errors`
- 失败语义：
  - 材料非法、OCR 服务不可用、解析失败分别记录明确错误。
  - 不用空文本或 mock 文本伪装解析成功。

## Acceptance Criteria

- 真实营业执照 JPG 调用 GLM OCR 返回 200，并提取企业名称、统一社会信用代码、法人或住所等文本。
- 真实 PDF/DOCX 样例能提取文本；有表格时能提取表格或等价结构化文本。
- 不支持文件类型不会调用 OCR/解析器，并返回明确错误。
- OCR 服务不可用时，任务进入失败/可重试状态，不生成假审查结论。
- `extractedFields` 不再出现由 GLM 请求格式导致的 `ocr_error: 400 Bad Request`。
- Python 测试覆盖 MIME data URI、文件类型分流、解析成功、解析失败和 OCR 成功转换。
- 真实 E2E 证据包含至少一份图片 OCR 和一份结构化文档解析结果。

## Non-Goals

- 不替换外部 OCR 供应商，除非现有供应商无法满足真实验收。
- 不做前端材料预览 UI；该能力属于材料安全预览任务。
- 不做最终合规推理；本任务只产出 Agent 可消费的真实内容。

## Dependencies

- `05-27-cp3-5-real-chain-guardrails`
- `05-26-v1-cp3-glm-ocr-data-uri-fix`
- `05-27-cp3-5-java-python-real-dispatch`
