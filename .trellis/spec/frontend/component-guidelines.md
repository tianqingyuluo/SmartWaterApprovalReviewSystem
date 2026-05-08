# 组件规范

> SmartWater MVP 前端当前的组件边界与写法。

---

## 当前模式

前端组件分成两类：

- `components/common/`：跨页面复用的基础展示组件
- `components/business/`：面向 reviewer/applicant 结果页的业务展示块

页面负责数据获取、轮询与拼装；组件负责渲染。

---

## 真实约定

- 所有组件使用 Vue 3 Composition API + `<script setup lang="ts">`
- Props 使用 `interface` 定义
- 组件内不要直接发 HTTP 请求
- 组件内不要自己管理后端 DTO 适配，适配应该先在 `api/task.ts` 做完
- 业务组件保持 presentational，必要时通过 typed props 接收已经规范化的数据
- 共享状态标签/材料标签统一来自 `types/smartwater.ts`

### 当前例子

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus } from '@/types'
import { STATUS_LABELS_APPLICANT, STATUS_LABELS_REVIEWER } from '@/types'

interface Props {
  status: ProcessingStatus
  audience?: 'applicant' | 'reviewer'
}

const props = withDefaults(defineProps<Props>(), {
  audience: 'applicant',
})
</script>
```

---

## 组件分层

| 层级 | 当前职责 | 示例 |
|---|---|---|
| common | 共享原子展示 | `StatusBadge.vue` |
| business | 页面结果块 | `FindingList.vue`、`MaterialSlotSummary.vue`、`RiskHints.vue` |
| page | 页面 orchestration | `ApplicantPage.vue`、`ReviewerPage.vue` |

---

## Scenario: SmartWater Component Boundaries

### 1. Scope / Trigger

- Trigger: 新增 UI 片段、拆分结果块、补充 reviewer/applicant 展示或变更已有提示文案时。

### 2. Signatures

Current typed component props include:

- `StatusBadge({ status, audience? })`
- `StatusBanner({ status, resultSummary })`
- `FindingList({ findings })`
- `MaterialSlotSummary({ slots })`

### 3. Contracts

| Contract | Rule |
|---|---|
| props | 必须 typed，避免 `any` |
| events | 只有真正可交互的组件才暴露 emit |
| styles | 使用 scoped CSS 或 class，不写内联样式 |
| data | 业务组件只接收已经适配好的对象，不再自己拼 DTO |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 组件自己请求后端 | 拒绝；把请求移动到 page 或 api 层。 |
| 组件同时负责获取数据和渲染 | 只有极少数特例可接受；当前 MVP 不需要。 |
| 业务结果结构变更导致多处重复格式化 | 先看 `api/task.ts` 是否能统一适配。 |

### 5. Good/Base/Bad Cases

- Good: `ReviewerPage` 只把 `ReviewerResultView` 拆给 `StatusBanner`、`MaterialSlotSummary`、`FindingList` 等组件。
- Base: 组件接收 `string[]` / `Record<string, string>` 这类已格式化结果。
- Bad: 每个组件都自己判断 `PARTIAL_SUCCESS` 文案或自己拼审核依据字符串。

### 6. Tests Required

- adapter 单测必须覆盖组件依赖的字段映射。
- 组件样式或结构变化若会影响结果页可读性，至少要有人类可读的回归说明或截图检查。

### 7. Wrong vs Correct

#### Wrong

```vue
<script setup lang="ts">
// 在组件里直接 fetch
</script>
```

#### Correct

```vue
<script setup lang="ts">
// 组件只负责展示已经准备好的 props
</script>
```
