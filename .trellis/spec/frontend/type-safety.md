# 类型安全规范

> SmartWater MVP 前端当前的 TypeScript 约定。

---

## 类型文件组织

真实类型入口：

```text
src/types/
├── common.ts
├── smartwater.ts
└── index.ts
```

### 当前模式

- `common.ts`：只放通用响应 `R<T>`
- `smartwater.ts`：放业务 union type、后端 DTO、前端 view model、常量映射
- `index.ts`：统一 re-export

---

## 真实约定

- 后端 DTO 和页面 view model 分开定义
- API 层在 `api/task.ts` 做 DTO → view model 适配
- `unknown` 只在确实无法直接断言的字段上使用，随后尽快归一化
- 枚举值使用字面量联合类型，不依赖 `any`
- 任务状态、材料类型、严重级别、受众等核心 contract 都必须有明确 union type

### 当前例子

```ts
export type MaterialType = 'APPLICATION_FORM' | 'BUSINESS_LICENSE' | 'ID_CARD'

export type ProcessingStatus =
  | 'SUBMITTED'
  | 'QUEUED'
  | 'PROCESSING'
  | 'PARTIAL_SUCCESS'
  | 'COMPLETED'
  | 'FAILED'
```

---

## Scenario: DTO And View Model Separation

### 1. Scope / Trigger

- Trigger: 新增后端字段、调整任务状态、结果 schema、reviewer visibility 或 adapter 输出时。

### 2. Signatures

- Backend DTO:
  - `TaskStatusResponse`
  - `ApplicantResultResponse`
  - `ReviewerResultResponse`
- View models:
  - `ApplicantResultView`
  - `ReviewerResultView`
- Adapter:
  - `toApplicantResultView`
  - `toReviewerResultView`

### 3. Contracts

| Contract | Rule |
|---|---|
| backend DTO | 保留后端原始字段形状 |
| view model | 只保留页面需要的数据形态 |
| extractedFields | 仍以 `unknown` 接入，再由 adapter 归一化 |
| material fields | multipart field name 统一来自 `MATERIAL_FORM_FIELDS` |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 新字段只加在页面组件里 | 不接受；应优先进入 `smartwater.ts`。 |
| 同一个状态字符串在多处手写 | 应提取到 union type 或常量 map。 |
| `any` 作为兜底 | 不接受；优先 `unknown` + 明确归一化。 |

### 5. Good/Base/Bad Cases

- Good: `manualReviewNotice?: string | null` 加入 DTO，适配后变成页面字符串。
- Base: `types/index.ts` 只 re-export，页面从 `@/types` 一次性引入。
- Bad: 组件直接依赖后端原始 DTO 的 `unknown` 字段并在各处重复解析。

### 6. Tests Required

- DTO 变化必须补 `api/task.spec.ts` 或页面回归测试。
- 任何 status / materialType / severity 变更都要确认前端的 union type 和 label map 同步更新。

### 7. Wrong vs Correct

#### Wrong

```ts
const fields: any = dto.extractedFields
```

#### Correct

```ts
const fields = normalizeExtractedFields(dto.extractedFields)
```

---

## 禁止事项

- 不要用 `any` 去绕过后端 contract。
- 不要在多个文件重复定义 status / materialType 字符串。
- 不要让页面组件直接理解后端原始 DTO 细节。
