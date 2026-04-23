# 组合式函数（Hooks）规范

> Vue Composables 的编写模式。

---

## 命名

- 文件名：`use` + 功能名，如 `useApproval.ts`
- 函数名：与文件名一致

---

## 模板

```typescript
import { ref, computed } from 'vue'
import { getApprovalList } from '@/api/approval'
import type { ApprovalRecord } from '@/types/approval'

export function useApprovalList() {
  const list = ref<ApprovalRecord[]>([])
  const loading = ref(false)

  async function fetchList(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await getApprovalList(params)
      list.value = res.data
    } finally {
      loading.value = false
    }
  }

  return {
    list,
    loading,
    fetchList,
  }
}
```

---

## 规则

- 返回值使用对象解构（不用数组）
- 内部管理 `loading` / `error` 状态
- 一个 composable 聚焦一个功能
- **禁止**在 composable 中直接操作 DOM
