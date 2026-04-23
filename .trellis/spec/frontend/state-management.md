# 状态管理规范

> 使用 Pinia 进行状态管理。

---

## 概述

- 状态管理库：Pinia
- 每个功能域一个 Store

---

## Store 模板

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!userInfo.value)

  function setUser(user: UserInfo) {
    userInfo.value = user
  }

  function logout() {
    userInfo.value = null
  }

  return {
    userInfo,
    isLoggedIn,
    setUser,
    logout,
  }
})
```

---

## 状态分类

| 类型 | 存放位置 | 示例 |
|------|----------|------|
| 全局状态 | Pinia Store | 用户信息、权限、系统配置 |
| 页面状态 | 组件内 `ref` | 表单数据、列表筛选条件 |
| 服务端状态 | Composable | API 请求结果、分页数据 |

---

## 规则

- 使用 Setup Store 语法（Composition API 风格）
- Store 命名：`use` + 功能 + `Store`，如 `useUserStore`
- **禁止**在 Store 中直接调用路由跳转
- **禁止**把所有状态都放到全局 Store，页面级状态留在组件内
