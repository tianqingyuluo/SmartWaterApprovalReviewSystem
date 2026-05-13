# 前端 Tailwind 样式体系重构

## Goal

在已完成的三页审核流程 UI 基础上，将前端样式体系迁移到 TailwindCSS，使后台管理界面的布局、间距、颜色、状态标签、卡片和响应式规则更模块化、更易维护。目标是样式体系重构，不扩展业务功能。

## Background

* 当前三页 UI 已按 `docs/UI设计/` 设计稿用 Vue scoped CSS 重构：
  * `docs/UI设计/申请列表.png`
  * `docs/UI设计/申请.png`
  * `docs/UI设计/AI初审结果.png`
* 当前项目尚未接入 TailwindCSS，`frontend/package.json` 没有 Tailwind 相关依赖，也没有 `tailwind.config.*`。
* 当前前端已抽取部分复用组件：`PageCard`、`EmptyState`、`FileUploadSlot`、`TaskMaterialSummary`。
* 这次重构应保留现有 UI 视觉和业务行为，只迁移样式实现与设计 token。

## Requirements

### Tailwind 接入

* 在 `frontend` 内安装并配置 TailwindCSS 及必要的 PostCSS/Vite 集成。
* 配置扫描路径覆盖 Vue、TS 和相关入口文件。
* 保持现有 `npm run test`、`npm run build` 命令可用。
* 不引入与 Tailwind 迁移无关的 UI 框架。

### 样式迁移

* 将三页和新增复用组件的大段 scoped CSS 迁移为 Tailwind utility class。
* 保留少量必要的全局 CSS，例如基础字体、body 背景、无障碍基础规则；避免继续堆叠页面级重复 CSS。
* 抽取可复用的 class 组合或组件边界，减少按钮、卡片、状态标签、表单控件、表格、上传槽等样式重复。
* Tailwind theme 中应沉淀设计稿常用 token：主蓝、深蓝侧栏、浅灰背景、卡片边框/阴影、状态色、圆角和间距。

### 视觉与功能边界

* 三页视觉仍需对齐 `docs/UI设计`：深蓝侧栏、顶部工具栏、浅灰内容背景、白色业务卡片、蓝色主操作。
* 不重新引入当前功能无法支撑的伪功能：
  * 列表中的申请人、项目名称、申请类型、当前节点等无数据字段。
  * Word/Docx 上传支持。
  * 伪 PDF/证照预览。
  * 不可用的审批通过动作。
* 不改变 API contract、后端接口、任务状态语义或请求/轮询逻辑。

## Acceptance Criteria

* [ ] `frontend` 成功接入 TailwindCSS，并提交必要依赖锁文件变更。
* [ ] 三个页面和核心复用组件主要使用 Tailwind class 表达布局与视觉。
* [ ] `frontend/src/style.css` 不再承载大量页面级样式，只保留基础全局规则或 Tailwind 入口。
* [ ] 设计稿视觉方向保持不退化，桌面和移动端布局可用。
* [ ] 没有展示当前功能无法支撑的伪功能。
* [ ] `cd frontend && npm run test` 通过。
* [ ] `cd frontend && npm run build` 通过。

## Out of Scope

* 改动 Java 后端、Worker 或 API contract。
* 重新设计 UI 视觉方向。
* 引入 Element Plus、Ant Design Vue 等组件库。
* 新增账号、RBAC、正式审批动作、PDF 在线预览或 Word/Docx 支持。

## Technical Notes

* Frontend app: `frontend/`
* Main pages:
  * `frontend/src/pages/ApplicationListPage.vue`
  * `frontend/src/pages/NewApplicationPage.vue`
  * `frontend/src/pages/ReviewResultPage.vue`
* Shared layout/component candidates:
  * `frontend/src/layouts/AppLayout.vue`
  * `frontend/src/components/common/PageCard.vue`
  * `frontend/src/components/common/EmptyState.vue`
  * `frontend/src/components/business/FileUploadSlot.vue`
  * `frontend/src/components/business/TaskMaterialSummary.vue`
* Specs:
  * `.trellis/spec/frontend/index.md`
  * `.trellis/spec/frontend/component-guidelines.md`
  * `.trellis/spec/frontend/type-safety.md`
  * `.trellis/spec/frontend/quality-guidelines.md`
