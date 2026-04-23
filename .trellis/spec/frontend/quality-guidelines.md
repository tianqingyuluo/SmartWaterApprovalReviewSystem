# 前端代码质量规范

> 代码标准和禁止事项。

---

## 代码风格

- 使用 ESLint + Prettier
- 缩进：2 空格
- 引号：单引号
- 分号：不加

---

## 禁止事项

| 禁止 | 原因 |
|------|------|
| 使用 `any` 类型 | 失去类型安全 |
| 使用 Options API | 统一 Composition API |
| `console.log` 残留 | 生产代码不保留调试日志 |
| 内联样式 | 用 scoped CSS |
| 魔法数字/字符串 | 定义为常量或枚举 |
| 组件中直接发 HTTP 请求 | 通过 api 层封装 |

---

## API 请求封装

```typescript
// src/api/approval.ts
import request from '@/utils/request'
import type { R, PageResult } from '@/types/common'
import type { ApprovalRecord, ApprovalSubmitDTO } from '@/types/approval'

export function getApprovalList(params?: Record<string, any>) {
  return request.get<R<PageResult<ApprovalRecord>>>('/api/approval/list', { params })
}

export function submitApproval(data: ApprovalSubmitDTO) {
  return request.post<R<number>>('/api/approval/submit', data)
}
```

- 使用 Axios 实例，统一配置 baseURL、拦截器
- 请求和响应都标注类型
