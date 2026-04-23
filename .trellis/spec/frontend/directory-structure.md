# 目录结构

> 前端 Vue 项目的代码组织方式。

---

## 概述

- 框架：Vue 3 + Composition API
- 构建工具：Vite
- 语言：TypeScript

---

## 目录布局

```
src/
├── api/                    # API 请求封装
│   ├── approval.ts
│   ├── review.ts
│   └── user.ts
├── assets/                 # 静态资源（图片、字体等）
├── components/             # 通用组件
│   ├── common/             # 基础组件（按钮、表格、弹窗等）
│   └── business/           # 业务组件（审批卡片、文件上传等）
├── composables/            # 组合式函数（Hooks）
├── layouts/                # 布局组件
├── pages/                  # 页面（按路由对应）
│   ├── approval/
│   ├── review/
│   └── system/
├── router/                 # 路由配置
├── stores/                 # 状态管理（Pinia）
├── styles/                 # 全局样式
├── types/                  # TypeScript 类型定义
├── utils/                  # 工具函数
├── App.vue
└── main.ts
```

---

## 模块组织规则

- **pages**：按功能域分目录，每个页面一个 `.vue` 文件
- **components**：分 `common`（通用）和 `business`（业务）两层
- **api**：每个功能域一个文件，封装对应的 HTTP 请求
- **composables**：以 `use` 开头命名，如 `useApproval.ts`
- **stores**：每个功能域一个 store 文件

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件名 | 大驼峰 | `ApprovalList.vue` |
| 页面文件名 | 大驼峰 | `ApprovalDetail.vue` |
| 工具/API 文件名 | 小驼峰 | `approval.ts` |
| 组合式函数 | `use` + 大驼峰 | `useApproval.ts` |
| CSS 类名 | kebab-case | `approval-card` |
