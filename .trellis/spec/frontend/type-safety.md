# 类型安全规范

> TypeScript 类型定义的约定。

---

## 类型文件组织

```
src/types/
├── approval.ts      # 审批相关类型
├── review.ts        # 审查相关类型
├── user.ts          # 用户相关类型
└── common.ts        # 通用类型（分页、响应等）
```

---

## 通用类型定义

```typescript
// 统一 API 响应
interface R<T> {
  code: number
  message: string
  data: T
}

// 分页请求
interface PageParams {
  page: number
  size: number
}

// 分页响应
interface PageResult<T> {
  records: T[]
  total: number
  page: number
  size: number
}
```

---

## 规则

- 每个功能域的类型定义在 `src/types/` 对应文件中
- API 请求参数和响应都要定义类型
- Props 使用 `interface` 定义
- **禁止**使用 `any`，确实无法确定时用 `unknown`
- **禁止**使用 `// @ts-ignore`
- 枚举值用 `const enum` 或字面量联合类型
