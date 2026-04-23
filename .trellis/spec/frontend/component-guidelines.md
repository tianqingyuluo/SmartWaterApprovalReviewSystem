# 组件规范

> Vue 组件的编写模式和约定。

---

## 概述

- 使用 Vue 3 Composition API + `<script setup>`
- 使用 TypeScript
- 单文件组件 `.vue`

---

## 组件模板

```vue
<template>
  <div class="approval-card">
    <h3>{{ title }}</h3>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  status?: number
}

const props = withDefaults(defineProps<Props>(), {
  status: 0,
})

const emit = defineEmits<{
  submit: [id: number]
}>()
</script>

<style scoped>
.approval-card {
  /* 样式 */
}
</style>
```

---

## 规则

### Props
- 使用 TypeScript `interface` 定义 Props 类型
- 使用 `withDefaults` 设置默认值
- Props 命名用小驼峰

### 事件
- 使用 `defineEmits` 并声明类型
- 事件名用 kebab-case（模板中）或小驼峰（script 中）

### 组件拆分原则
- 超过 200 行的组件考虑拆分
- 可复用的 UI 片段提取为 `components/common/`
- 特定业务的提取为 `components/business/`

---

## 禁止事项

| 禁止 | 原因 |
|------|------|
| 使用 Options API | 统一用 Composition API |
| 组件中直接调用 API | 通过 composable 或 store 调用 |
| 使用 `any` 类型 | 使用明确的类型定义 |
| 内联样式 | 使用 scoped CSS 或 class |
