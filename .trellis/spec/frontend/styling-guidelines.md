# 前端样式规范

> SmartWater 前端 TailwindCSS 样式体系约定。

---

## 当前模式

前端样式体系基于 TailwindCSS 3：

- `frontend/tailwind.config.js` 存放 SmartWater 设计 token。
- `frontend/postcss.config.js` 接入 `tailwindcss` 和 `autoprefixer`。
- `frontend/src/style.css` 只保留 Tailwind 入口、基础全局规则和少量共享组件 class。
- 页面和组件优先使用 Tailwind utility class 表达布局、间距、状态和响应式规则。

---

## 设计 Token

`tailwind.config.js` 中的 `sw` token 是后台管理界面的样式来源：

| Token group | Usage |
|---|---|
| `colors.sw.primary` / `primary-strong` | 主按钮、选中态、重点操作 |
| `colors.sw.sidebar` / `sidebar-deep` | 深蓝侧栏和导航背景 |
| `colors.sw.bg` / `card` | 页面浅灰背景与白色业务容器 |
| `colors.sw.line` / `line-strong` | 卡片、表单、分隔线 |
| `colors.sw.success` / `warning` / `danger` / `info` | 状态标签和提示 |
| `boxShadow.sw-*` | 卡片、轻阴影、主按钮阴影 |
| `borderRadius.sw` | 通用业务卡片圆角 |

新增颜色、阴影或圆角前，先检查 `tailwind.config.js` 是否已有可复用 token。

---

## 真实规则

- 页面级布局、卡片、按钮、状态标签、上传槽和表格样式优先使用 Tailwind class。
- `style.css` 只放全局基础规则、Tailwind `@tailwind` 入口和少量复用 class；不要重新堆页面级 scoped CSS。
- 复用样式如果跨多个页面重复出现，优先放到共享组件或 `@layer components` 中的 `sw-*` class。
- 不使用 Tailwind 不存在的 utility；需要特殊 CSS 属性时使用明确的 arbitrary property，例如 `[overflow-wrap:anywhere]`。
- 不使用额外 `tracking-*` 或任意 `letter-spacing` 做装饰；后台界面文字保持默认字距。
- 视觉迁移不能新增当前 API 不支持的伪功能，例如 Word/Docx 上传、审批通过动作、PDF/证照预览。

---

## Scenario: Tailwind Style Migration

### 1. Scope / Trigger

- Trigger: 新增或重构前端页面、共享组件、后台管理界面样式、Tailwind token 或全局样式时。

### 2. Signatures

- Config:
  - `frontend/tailwind.config.js`
  - `frontend/postcss.config.js`
- Global CSS:
  - `frontend/src/style.css`
- Verification:
  - `cd frontend && npm run test`
  - `cd frontend && npm run build`

### 3. Contracts

| Contract | Rule |
|---|---|
| Tailwind content scan | 必须覆盖 `index.html` 和 `src/**/*.{vue,js,ts,jsx,tsx}` |
| theme tokens | SmartWater 色彩、阴影、圆角和字体应沉淀到 `theme.extend` |
| global CSS | 只允许基础规则和少量共享 class，不承载页面级大块样式 |
| components | 组件保持 presentational，不因样式迁移改变 API 请求或 DTO 适配边界 |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 使用不存在的 Tailwind utility | 改成合法 utility、arbitrary property 或 `@layer components` class。 |
| 新增页面级大段 scoped CSS | 优先迁移到 utility class 或复用组件边界。 |
| 样式迁移引入伪功能 | 删除伪功能，保持现有 API 支撑范围。 |
| 改动 token 后视觉明显回退 | 恢复设计稿对应的颜色、阴影或间距 token。 |

### 5. Good/Base/Bad Cases

- Good: 卡片使用 `rounded-sw border border-sw-line bg-sw-card shadow-sw-card`。
- Base: 复杂复用按钮保留 `sw-btn sw-btn-primary` 这类 `@layer components` class。
- Bad: 在多个页面复制相同的 100 行 scoped CSS 或使用不存在的 `overflow-wrap-anywhere` class。

### 6. Tests Required

- 页面/组件样式迁移后必须通过 `npm run build`。
- 如果样式迁移同时改到 adapter、DTO、状态或材料字段，必须补 `api/task.spec.ts` 或等价 contract 测试。
- 提交前运行 `npm run test`，确认现有请求层和 adapter 回归测试仍通过。

### 7. Wrong vs Correct

#### Wrong

```vue
<template>
  <div class="overflow-wrap-anywhere tracking-[-0.02em]">
    {{ value }}
  </div>
</template>
```

#### Correct

```vue
<template>
  <div class="[overflow-wrap:anywhere]">
    {{ value }}
  </div>
</template>
```
