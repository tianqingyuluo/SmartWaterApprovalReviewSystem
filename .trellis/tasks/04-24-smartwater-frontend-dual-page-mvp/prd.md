# 前端双页演示 MVP

## Goal

实现 SmartWater MVP 的演示型前端：一个申请人材料提交页和一个审批人员只读结果页，支持固定槽位上传、任务状态轮询和 AI 审核结果展示。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* 前端尚未创建，第一版是双页演示应用，不做完整产品信息架构。
* 无账号体系，审批人员通过任务 ID / 会话 ID 访问结果页。
* 申请人侧只展示基础 AI 提示，审批侧展示完整只读审核结果。

## Scope

### In Scope

* 申请人提交页：固定上传位、文件格式提示、缺失材料允许提交、提交后显示任务 ID / 会话 ID。
* 处理中状态：轮询任务状态，展示 OCR/审核进行中、部分失败、失败和完成。
* 审批人员结果页：通过任务 ID / 会话 ID 查询并展示完整结果。
* 结果展示：抽取字段、缺失材料、问题清单、风险提示、审核意见草稿、材料摘要、人工复核提示。
* 申请人基础结果：缺失材料、明显字段问题、重新上传建议。

### Out of Scope

* 不做登录、角色权限、提交列表、待办和流程动作。
* 不做人工编辑、人工改写、补正闭环和导出。
* 不做多轮补传、版本对比、多文件材料和自动分类上传。
* 不在本任务中最终决定长期前端技术栈，除非实现需要先做最小工程选择。

## Inputs

* `smartwater-mvp-domain-contract` 输出的状态和结果结构。
* `smartwater-backend-submission-storage-mvp` 输出的 API 契约。
* 父任务 PRD 中的用户可见范围和前端形态。

## Outputs

* 前端工程骨架或页面实现。
* 申请人提交页。
* 审批人员结果页。
* API client、轮询逻辑和状态展示。
* 基础错误与空状态展示。

## Requirements

* 材料上传位必须固定为申请书、营业执照、身份证。
* 每个上传位只允许一个文件。
* 支持 `jpg/jpeg/png/pdf`，明确提示不支持 `doc/docx`。
* 缺失材料可提交，但 UI 要明确提示缺失项。
* 审批人员结果页只读，不提供编辑或流程提交按钮。
* 申请人页不得展示审批侧详细问题清单、推理过程或结论草稿。

## Acceptance Criteria

* [ ] 申请人可上传 0–3 个固定槽位文件并提交任务。
* [ ] 提交成功后显示任务 ID / 会话 ID 和查看入口。
* [ ] 前端可轮询任务状态并展示处理中、失败、部分成功和完成。
* [ ] 审批人员结果页可按任务 ID / 会话 ID 展示完整只读结果。
* [ ] 申请人基础提示与审批人员完整结果有明确展示差异。
* [ ] UI 不包含账号、待办、流程动作、编辑和导出能力。

## Dependencies

* Depends on `smartwater-mvp-domain-contract` for result shape.
* Depends on `smartwater-backend-submission-storage-mvp` for API contract.
* Can start with mock API if backend implementation is not ready, but must switch to real contract before completion.

## Definition of Done

* 前端可演示完整提交、轮询和结果查看流程。
* 双页范围保持收敛，未提前引入完整审批系统复杂度。
* 错误、空状态和部分失败对用户可理解。
