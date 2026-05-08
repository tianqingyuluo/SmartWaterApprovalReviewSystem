# 状态管理规范

> SmartWater MVP 前端当前的状态存放方式。

---

## 当前模式

`main.ts` 里已经注册了 Pinia：

```ts
app.use(createPinia())
```

但当前 MVP 并没有实际使用全局 store。真实状态主要放在页面组件内部：

- `ApplicantPage`：上传槽位、提交中状态、轮询状态、申请人结果
- `ReviewerPage`：任务 ID / 会话 ID 查询、查询中状态、结果视图

---

## 真实规则

- 页面级状态放在 `ref` / `reactive`
- 服务端状态通过 `api/task.ts` 拉取并由页面决定何时刷新
- 可复用轮询逻辑抽到 `composables/usePolling.ts`
- 不要因为项目安装了 Pinia 就默认创建 store
- 只有当跨页面共享、持久化或多组件共享成为真实需求时，才引入 store

### 当前页面状态示例

```ts
const submitting = ref(false)
const result = ref<SubmitResponse | null>(null)
const taskStatus = ref<ProcessingStatus>('SUBMITTED')
const taskData = ref<ApplicantResultView | null>(null)
```

---

## Scenario: Local State First

### 1. Scope / Trigger

- Trigger: 双页 MVP 页面、轮询、查询表单、局部交互或单次结果展示时。

### 2. Signatures

- `createPinia()` 已存在于 `main.ts`
- 当前没有正式 store 文件

### 3. Contracts

| State type | Current place |
|---|---|
| page UI state | `pages/*.vue` |
| reusable behavior | `composables/*.ts` |
| backend DTO / view model | `types/*.ts` + `api/task.ts` |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 为了保存一次提交结果而新建全局 store | 不推荐；继续用 page refs。 |
| 把服务端 DTO 直接塞进页面所有组件 | 先经 adapter 转成 view model。 |
| 多处需要同一状态标签或材料标签 | 放入 `types/smartwater.ts` 常量。 |

### 5. Good/Base/Bad Cases

- Good: `ApplicantPage` 用 local state 管理上传与轮询。
- Base: `ReviewerPage` 用 local state 管理查询表单和查回的结果。
- Bad: 把 `taskId/sessionId` 放到全局 store 里再由多个页面读写。

### 6. Tests Required

- 如果 state 边界变化会影响 adapter 或视图模型，要更新 `api/task.spec.ts`。
- 若引入 store，必须补 store 行为测试或至少说明为什么需要全局状态。

### 7. Wrong vs Correct

#### Wrong

```ts
// 为单次页面流程创建全局 store
export const useTaskStore = defineStore('task', () => ...)
```

#### Correct

```ts
// 状态留在页面，跨页需要时再升级
const taskId = ref('')
const sessionId = ref('')
```
