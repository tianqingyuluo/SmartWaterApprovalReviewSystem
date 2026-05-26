# CP3-G 材料安全预览接口与前端嵌入

## Scope

为 CP3 审核结果页补齐网页登录用户可安全预览已上传 PDF/图片材料的能力。当前系统可以上传材料、存入对象存储、供 Python Worker 下载并回写 OCR/抽取结果，但面向浏览器的任务状态和结果接口只返回材料元数据与抽取字段，不返回可嵌入的材料预览地址。该任务在不泄露 Worker token 或原始 `storageKey` 的前提下，让审批人员在 AI 初审结果页直接查看原始材料证据。

## Problem

- `TaskStatusResponse.MaterialStatus` 只包含 `materialType`、`originalFileName`、`uploaded`，前端无法知道如何预览文件。
- `/api/material/download?key=<storageKey>` 是 `@WorkerApi`，只允许 Python Worker 通过 `X-Worker-Token` 下载，不适合作为网页登录用户的浏览器预览接口。
- 前端结果页目前只能展示“材料与任务信息”占位提示，无法把 OCR/抽取字段和原始 PDF/图片证据放在同一屏对照。

## Deliverables

- Java 后端新增面向网页登录用户的材料预览接口，例如：
  - `GET /api/task/{taskId}/material/{materialType}/preview`
- 预览接口复用现有登录态和任务可见性规则：
  - 申请人只能预览自己提交任务的材料。
  - 审批人员只能预览审批可见任务的材料。
  - 管理员可预览全部任务材料。
- 后端按 `taskId + materialType` 查找材料，不让浏览器传入或看到原始 `storageKey`。
- 后端返回 PDF/图片二进制流，设置合适的 `Content-Type`、`Content-Disposition: inline`、缓存与安全响应头。
- 前端结果页用安全预览接口替换“不提供伪造证照预览”占位区：
  - PDF 使用嵌入预览或打开新标签的登录态接口。
  - 图片使用受控预览区域。
  - 未上传、下载失败、格式不支持时展示明确状态。
- 类型与 API adapter 更新，避免页面直接消费后端原始 DTO。
- 文档或开发日志补充材料预览接口边界。

## Non-Goals

- 不开放公开对象存储 URL。
- 不把 `storageKey`、S3/RustFS 访问密钥或 Worker token 暴露给前端。
- 不做材料补正重传、版本差异对比或历史版本预览；这些仍属于 CP4。
- 不做复杂 PDF 标注、框选 OCR 坐标或在线批注。
- 不改 Python Worker 下载接口的内部 token 边界。

## Acceptance Criteria

- 未登录访问材料预览接口返回登录错误。
- 申请人 A 不能预览申请人 B 的材料。
- 审批人员只能预览其任务列表/审核结果可见范围内的材料。
- 浏览器可预览已上传的 PDF、jpg、jpeg、png 材料。
- 预览接口不接受 `storageKey` 参数，响应体和前端状态中也不暴露 `storageKey`。
- 材料缺失、材料类型非法、对象存储下载失败时返回明确错误，不导致结果页整体崩溃。
- 前端结果页不再显示“不提供伪造证照预览”的固定占位文案，改为真实预览或明确失败态。
- Java 测试覆盖权限、材料类型校验和二进制响应关键路径。
- Frontend 测试覆盖预览 URL 生成、缺失材料态和结果页渲染分支。

## Dependencies

- `v1-cp3-minimal-rbac-task-visibility`
- `v1-cp3-reviewer-actions-applicant-result`
- `v1-cp3-frontend-review-workbench`

## Technical Notes

- 当前内部下载接口：`GET /api/material/download?key=<storageKey>`，由 `@WorkerApi` 和 `X-Worker-Token` 保护，只给 Python Worker 使用。
- 当前前端结果页占位文案位于 `frontend/src/pages/ReviewResultPage.vue`。
- 当前材料状态 DTO 未携带预览 URL；建议由前端根据 `taskId + materialType` 调用固定预览接口，或由后端返回不含密钥的相对 `previewPath`。
- 推荐后端接口仍放在 `/api/task/**` 下，以便复用登录拦截与任务访问控制语义。

## CP3 Boundary

本任务归入 CP3，因为它直接支撑“初审 Agent 与系统集成”的审核结果工作台：审批人员需要在 AI 结论、抽取字段和原始材料之间建立可核验的证据链。CP4 继续负责补正材料重传、版本差异、报告导出和最终答辩材料收口。
