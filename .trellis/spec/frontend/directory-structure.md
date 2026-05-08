# 目录结构

> SmartWater MVP 前端当前的真实代码组织方式。

---

## 当前布局

```text
frontend/src/
├── App.vue
├── main.ts
├── style.css
├── router/
│   └── index.ts
├── pages/
│   ├── ApplicantPage.vue
│   └── ReviewerPage.vue
├── components/
│   ├── common/
│   │   └── StatusBadge.vue
│   └── business/
│       ├── DraftOpinion.vue
│       ├── FieldExtraction.vue
│       ├── FindingList.vue
│       ├── ManualReviewNotice.vue
│       ├── MaterialSlotSummary.vue
│       ├── MaterialSummary.vue
│       ├── RiskHints.vue
│       └── StatusBanner.vue
├── composables/
│   └── usePolling.ts
├── api/
│   └── task.ts
├── types/
│   ├── common.ts
│   ├── index.ts
│   └── smartwater.ts
├── utils/
│   └── request.ts
└── assets/
    └── hero.png
```

---

## 当前组织规则

- `pages/` 只放路由页面，当前仅有提交页和结果页。
- `components/common/` 放跨页面复用的基础展示组件，目前以状态徽章为主。
- `components/business/` 放业务结果块，通常只负责渲染某个结果切片。
- `api/task.ts` 同时承担读取后端 DTO 和把 DTO 转成页面 view model 的职责。
- `composables/usePolling.ts` 是当前唯一共享 composable。
- `types/smartwater.ts` 是 SmartWater 业务类型的单一来源，`types/index.ts` 只做 re-export。

---

## 目录约束

| 目录 | 当前约束 |
|---|---|
| `pages/` | 页面负责提交、路由查询、轮询与组合展示，不再拆进额外布局层。 |
| `components/common/` | 共享原子/轻量组件，不能直接调用 API。 |
| `components/business/` | 业务结果块，保持 presentational，不接管页面状态流。 |
| `api/` | 统一调用 `@/utils/request`，并在此完成 DTO → view model 适配。 |
| `composables/` | 只放可复用的行为抽象，例如轮询。 |
| `types/` | 后端 DTO、前端 view model、union type 和常量都集中在这里。 |
| `utils/request.ts` | 唯一 axios 实例入口，负责统一错误消息。 |

---

## Scenario: Dual-Page MVP Layout

### 1. Scope / Trigger

- Trigger: 新增页面、业务结果块、轮询逻辑、API adapter 或类型定义时。

### 2. Signatures

- Routes:
  - `/` → `ApplicantPage.vue`
  - `/review` → `ReviewerPage.vue`
- Shared request layer:
  - `frontend/src/utils/request.ts`
- Adapter:
  - `frontend/src/api/task.ts`

### 3. Contracts

| Layer | Contract |
|---|---|
| pages | 负责用户交互、路由参数读取和调用 api/composable |
| components/business | 只接收 typed props，渲染 reviewer/applicant 结果片段 |
| composables | 对象返回值，通常包含状态和 start/stop 类操作 |
| types | 后端 DTO 与 view model 分离，字段名和联合类型统一维护 |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 页面组件直接写 axios 请求 | 视为结构违规，应改为 `api/` 文件。 |
| 业务组件自己拉接口或读路由 | 视为职责泄漏，应把状态留在 page。 |
| 新字段散落到多个文件重复定义 | 应优先放入 `types/smartwater.ts` 或 adapter。 |

### 5. Good/Base/Bad Cases

- Good: `ReviewerPage` 只调用 `getTaskStatus`/`getReviewerResult`，再喂给 `toReviewerResultView`。
- Base: 页面内 `ref/reactive` 维持 local UI 状态，路由仅用于 review 页的初始任务查询。
- Bad: 额外创建一个全局 store 只为保存当前一次提交的 `taskId/sessionId`。

### 6. Tests Required

- `api/task.spec.ts` 需要覆盖 adapter 映射字段。
- 页面/组件变动若影响 contract 文案，至少补一个 adapter 或 component 单测。
- `npm run build` 必须继续通过 `vue-tsc -b && vite build`。

### 7. Wrong vs Correct

#### Wrong

```ts
// 在组件中直接发请求
const res = await axios.get('/task/...')
```

#### Correct

```ts
// 统一从 api/task.ts 读取 DTO，再转成 view model
const res = await getReviewerResult(taskId, sessionId)
task.value = toReviewerResultView(statusRes.data.data, res.data.data)
```
