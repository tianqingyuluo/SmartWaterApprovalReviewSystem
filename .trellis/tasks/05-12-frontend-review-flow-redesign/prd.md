# 前端审核流程重构

## Goal

在 MVP 收尾前重构 SmartWater 前端，并补齐申请列表所需的前端可用后端接口，把当前双页演示应用升级为可正常承载审核辅助流程的前端界面。重构目标不是只美化页面，而是让后端任务状态、AI 审核结果、部分失败、模型失败、人工复核提示、申请列表和附件上传流程都能被准确、友好地展示。

## What I Already Know

* 当前前端是 Vue 3 + Vite + TypeScript，路由只有 `/` 申请人提交页和 `/review` 审批人员结果页。
* 当前 API 已接真实 Java 后端：提交材料、查询状态、查询申请人结果、查询审批人员结果。
* 当前前端结果解释层过于简化：`COMPLETED` 会固定展示“完整审核辅助结果已生成”，没有识别 `BLOCKER`、`SYSTEM_ERROR`、`AUTH_ERROR`、`SCHEMA_MISMATCH` 等结果级失败。
* 当前 MVP 暂无账号体系和 RBAC；访问依赖 `taskId + sessionId`。
* 当前后端没有明显的普通用户“申请列表”公共 API；已有 `/api/task/pending` 是 Worker 内部拉取待处理任务接口，受 `X-Worker-Token` 保护，不适合作为前端申请列表数据源。
* 用户已选择方案 B：本任务同步新增后端申请列表 API，让申请列表页展示真实后端数据。
* 工作区当前存在既有无关改动：`frontend/package-lock.json`。实现前需要先明确处理方式，避免误纳入本任务。

## Requirements

### 页面结构

前端至少包含三个主页面：

* 申请列表页面：作为用户进入系统后的任务/申请总览页。
* 新建申请页面：创建一次取水许可材料预审任务，包含附件上传功能。
* 初审结果页面：展示一次任务的完整状态、材料、AI 初审辅助结果、异常和人工复核提示。

### 新建申请页面

* 支持上传附件。
* 首批材料仍遵守 MVP 固定槽位：`申请书 + 营业执照 + 身份证`。
* 支持 `jpg`、`jpeg`、`png`、`pdf`；不把 Word/Docx 伪装成已支持能力。
* 允许缺失材料提交，但必须在页面上明确说明会得到部分结果或缺失材料提示。
* 提交成功后清晰展示 `taskId` 和 `sessionId`，并引导进入初审结果页。

### 申请列表页面

* 必须展示真实后端申请列表，不使用浏览器本地记录冒充真实列表。
* 必须新增前端可调用的 Java 后端列表 API；不能调用 Worker 内部 `/api/task/pending`。
* 列表项至少展示任务 ID、材料提交情况、当前处理状态、更新时间或提交时间、进入结果页入口。
* MVP 没有登录和 RBAC，所以列表 API 不能声称是“当前用户待办”。可接受的 MVP 语义是“演示环境申请列表”或“最近申请列表”，并在 UI 文案中说明访问边界。

### 后端列表 API

* 新增前端可用的申请列表接口，建议形态：
  * `GET /api/task/list`
  * 可选分页参数：`page`、`size`
  * 返回任务 ID、sessionId、状态、提交时间、更新时间、知识包版本、三类材料上传状态。
* 列表接口不得要求 `X-Worker-Token`。
* 列表接口不得复用 `/api/task/pending` 的“抢占任务并置为 PROCESSING”语义。
* 若返回 `sessionId`，必须在 PRD/实现说明这是 MVP 无账号模式下为了让前端结果页可跳转；V1/RBAC 后应改为按登录用户授权查询。

### 初审结果页面

* 必须完整、准确展示后端状态，不只做固定成功文案。
* 必须区分：
  * 正常完成：结果完整生成。
  * 部分成功：材料缺失、OCR 部分失败或某些步骤失败。
  * 失败：任务无法生成结果。
  * 需人工复核：存在 `BLOCKER` 或系统/模型类错误，即使后端状态是 `COMPLETED` 也不能误导为完全成功。
* 必须展示材料状态、缺失材料、问题清单、风险提示、审核意见草稿、人工复核提示。
* 对 `SYSTEM_ERROR`、`AUTH_ERROR`、`RATE_LIMIT`、`TIMEOUT`、`UPSTREAM_5XX`、`INVALID_JSON`、`SCHEMA_MISMATCH`、`CONTENT_FILTERED` 等审核模型失败类别给出明确但不过度暴露内部细节的文案。
* 申请人可见内容和审批人员/内部诊断内容要有清晰边界；MVP 无 RBAC 时，不能声称已经完成真实角色权限控制。

### 交互和视觉质量

* 页面样式完整，不能停留在表单堆叠或空壳状态。
* 交互要覆盖加载中、提交中、轮询中、空状态、错误态、部分成功、成功、重新查询、重新提交等状态。
* 设计应有明确视觉方向，遵守 `frontend-design` 技能要求，避免通用模板感。
* 桌面和移动端都要可用。

### 设计稿对齐

用户已补充三张 UI 设计稿，前端页面布局需要按设计稿重构：

* `docs/UI设计/申请列表.png`
* `docs/UI设计/申请.png`
* `docs/UI设计/AI初审结果.png`

实现要求：

* 三页统一使用设计稿中的后台管理系统骨架：深蓝左侧导航、顶部工具栏、浅灰内容背景、白色卡片式业务区域。
* 申请列表页以筛选栏 + 表格 + 分页为主体；只显示当前真实功能能支撑的数据，不展示无后端或无交互支撑的申请人、项目名称、申请类型、审批流节点等伪数据。
* 新建申请页以申请信息表单 + 附件上传区 + 底部操作按钮为主体；设计稿中未被当前提交接口支持的业务字段可以作为本地 UI 字段展示，但不得伪装成已经提交到后端的能力。
* AI 初审结果页以左侧材料预览/附件信息区 + 右侧 AI 分析面板/合规检查清单为主体；当前无法真实预览 PDF 图片时，不要硬造证照预览，应展示真实材料列表、抽取字段、问题、风险和审核意见。
* 设计稿没有涉及到的既有 UI 功能不要继续展示在页面上；保留必要的 MVP 访问边界说明、状态错误提示和人工复核提示。
* 重构时要做好页面与组件解耦，抽取共用布局、表单控件、业务卡片、状态标签、空状态/错误态等可复用组件，避免三个页面复制大段结构和样式。

## Assumptions

* 本任务是 fullstack 范围：前端重构 + Java 后端申请列表 API。
* 本任务不扩展正式审批流，只补齐前端列表页所需的只读查询能力。
* 初审结果页可以在 MVP 中同时承载申请人和审批辅助视角，但必须清楚标注 AI 只提供辅助建议，不构成最终审批决定。

## Open Questions

* 列表 API 是否需要分页默认值和最大 `size` 限制？建议默认 `page=1,size=20`，最大 `size=100`。

## Acceptance Criteria

* [ ] 前端路由至少包含申请列表、新建申请、初审结果三个页面。
* [ ] 新建申请页可以上传附件并调用现有提交接口。
* [ ] 任务状态展示覆盖 `SUBMITTED`、`QUEUED`、`PROCESSING`、`PARTIAL_SUCCESS`、`COMPLETED`、`FAILED`。
* [ ] 审核模型失败或 schema 错误不会被展示成“完整审核辅助结果已生成”。
* [ ] 初审结果页能展示材料状态、缺失材料、问题清单、风险提示、审核意见草稿、人工复核提示。
* [ ] Java 后端提供前端可调用的申请列表 API，且不会抢占 Worker 任务。
* [ ] 申请列表页调用真实后端列表 API，不调用 Worker 内部接口。
* [ ] 列表 API 覆盖后端测试，至少断言不会把任务状态改为 `PROCESSING`。
* [ ] `api/task.spec.ts` 或等价前端测试覆盖状态/错误语义映射。
* [ ] 三个前端页面布局与 `docs/UI设计` 中的对应设计稿保持一致，同时不展示当前功能无法支撑的伪功能。
* [ ] 前端页面和组件完成模块化拆分，公共布局/控件/业务展示逻辑有明确复用边界。
* [ ] Java `./mvnw test` 通过。
* [ ] `npm run test` 和 `npm run build` 通过。

## Definition of Done

* 前端 UI/交互完成并可端到端手动验证。
* 后端列表 API 有测试覆盖并记录契约。
* DTO 到 view model 的映射有回归测试。
* 相关前端 spec 或 readable docs 更新。
* 未混入既有无关 `frontend/package-lock.json` 改动，除非本任务确实需要更新依赖锁文件并说明原因。

## Out of Scope

* 完整账号体系、登录、RBAC、组织角色和权限菜单。
* 正式审批流：受理、初审、复核、退回补正、办结。
* 多轮补传、历史版本、差异对比。
* Word/Docx 解析支持。
* 法规知识包在线维护后台。
* 用列表页实现真实审批人员待办分派；这需要账号/RBAC 后再做。

## Technical Notes

* Current router: `frontend/src/router/index.ts`
* Current pages: `frontend/src/pages/ApplicantPage.vue`, `frontend/src/pages/ReviewerPage.vue`
* API adapter: `frontend/src/api/task.ts`
* Types: `frontend/src/types/smartwater.ts`
* Frontend specs:
  * `.trellis/spec/frontend/index.md`
  * `.trellis/spec/frontend/smartwater-mvp-visibility.md`
  * `.trellis/spec/frontend/component-guidelines.md`
  * `.trellis/spec/frontend/quality-guidelines.md`
* Backend contracts:
  * `.trellis/spec/backend/smartwater-mvp-contracts.md`
  * `.trellis/spec/backend/database-guidelines.md`
  * `.trellis/spec/backend/error-handling.md`
  * `.trellis/spec/backend/quality-guidelines.md`
  * `java-services/water-approval/src/main/java/com/tianqingyuluo/waterapproval/controller/ReviewTaskController.java`
  * `java-services/water-approval/src/main/java/com/tianqingyuluo/waterapproval/service/ReviewTaskServiceImpl.java`
