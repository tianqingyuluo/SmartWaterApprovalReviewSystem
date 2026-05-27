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

## Scenario: CP3 Reviewer Action Types

### 1. Scope / Trigger

- Trigger: 接入审核员初审动作、处理快照、操作日志，或调整申请人/审批人员结果投影时。

### 2. Signatures

Frontend union types:

```ts
export type ReviewerActionCode =
  | 'APPROVE_INITIAL_REVIEW'
  | 'RETURN_FOR_CORRECTION'
  | 'TRANSFER_MANUAL_REVIEW'

export type HandlingStatus =
  | 'INITIAL_REVIEW_PASSED'
  | 'CORRECTION_REQUIRED'
  | 'MANUAL_REVIEW_REQUIRED'
  | null
```

Adapter/API signatures:

```ts
submitReviewerAction(taskId, { actionCode, reviewerRemark })
toApplicantTaskResultView(statusDto, applicantResultView)
toReviewerResultView(statusDto, reviewerResultDto)
```

### 3. Contracts

| Contract | Rule |
|---|---|
| reviewer action code | 只使用 `ReviewerActionCode` union，不在页面硬编码额外动作。 |
| handling status | 允许为空；空值表示尚未提交初审动作。 |
| action labels | 页面展示优先使用后端 label，缺失时回退到 `REVIEWER_ACTION_LABELS`。 |
| applicant projection | 只能由申请人 DTO + status snapshot 组合，不得读取 reviewer-only DTO。 |
| action logs | 后端主字段为 `actionLogs`；兼容旧别名 `reviewActionLogs` 时必须在 adapter 内归一化。 |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 未知 action code 出现在日志里 | 展示原始 code，不崩溃。 |
| 已存在 handling status | 视为已处理，禁用重复提交。 |
| 申请人视图需要处理结果 | 使用 `handlingStatus`、`handlingStatusLabel`、`reviewerRemark`、`reviewerActionAt`，不暴露日志和 OCR 字段。 |
| 本地存储 user profile 畸形 | 返回 `null`，不猜测角色。 |

### 5. Good/Base/Bad Cases

- Good: `ReviewResultPage` 调用 `toApplicantTaskResultView` 或 `toReviewerResultView` 后再渲染。
- Base: `ReviewResultPage` 按当前登录角色选择申请人/审批人员结果接口，仍依赖后端权限校验。
- Bad: 页面组件直接拼接 reviewer DTO、直接信任 localStorage 中的任意 `role` 字符串。

### 6. Tests Required

- `api/task.spec.ts` 覆盖处理快照、动作日志、申请人投影隔离和已处理状态判断。
- `utils/auth.spec.ts` 覆盖畸形 localStorage 用户资料不会产生角色。

### 7. Wrong vs Correct

#### Wrong

```ts
const role = JSON.parse(localStorage.getItem('smartwater-auth-user')!).role
```

#### Correct

```ts
const role = getCurrentRole()
```
