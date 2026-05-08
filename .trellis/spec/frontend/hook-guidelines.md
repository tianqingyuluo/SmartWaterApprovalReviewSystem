# 组合式函数（Hooks）规范

> SmartWater MVP 前端当前的 composable 写法。

---

## 当前模式

当前项目只有一个共享 composable：`usePolling.ts`。

它的职责是：

- 接收一个 `fetcher`
- 按固定间隔轮询
- 通过 `shouldStop` 判断何时停止
- 通过 `onUpdate` 把最新结果回传给 page
- 在组件卸载时自动停止

---

## 真实约定

- composable 返回对象，不返回数组
- composable 只抽象可复用行为，不接管整页业务流
- `usePolling` 可以在 page 的一次性流程内使用，也可以在 setup 顶层使用
- transient polling error 默认吞掉，由页面状态和后续轮询继续收敛
- composable 不直接操作 DOM；需要 DOM 的逻辑留在 page 或 template

### 当前实现

```ts
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  shouldStop: (data: T) => boolean,
  onUpdate: (data: T) => void,
) {
  const isPolling = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null
  ...
}
```

---

## Scenario: Polling As Reusable Behavior

### 1. Scope / Trigger

- Trigger: 页面需要轮询 task status、查询结果，或者以后需要同类可停止的重复请求时。

### 2. Signatures

- `usePolling(fetcher, intervalMs, shouldStop, onUpdate)`

### 3. Contracts

| Contract | Rule |
|---|---|
| return value | 返回对象 `{ isPolling, start, stop }` |
| cleanup | 必须在 `onUnmounted(stop)` 中清理 |
| error handling | 暂时保留轮询，不因瞬时错误停止整个流程 |
| dependency injection | fetcher/stop/update 由调用方注入 |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 轮询请求偶发失败 | 不停止整个轮询，等待下一轮。 |
| 页面卸载 | 自动停止，防止定时器泄漏。 |
| 已到终态 | 立刻 stop，不再继续请求。 |

### 5. Good/Base/Bad Cases

- Good: `ApplicantPage` 在提交后启动轮询，终态后再拉申请人结果。
- Base: `ReviewerPage` 不需要轮询，因此不引入额外 composable。
- Bad: 为单个页面写一个只调用一次、完全不复用的 composable。

### 6. Tests Required

- 轮询行为变更至少要有一个 unit test 或页面回归说明。
- 若 composable 改动导致状态泄漏或停止条件变化，必须补测试。

### 7. Wrong vs Correct

#### Wrong

```ts
// 在 composable 里直接读 DOM
document.getElementById('...')!
```

#### Correct

```ts
const { isPolling, start, stop } = usePolling(fetcher, 3000, shouldStop, onUpdate)
```
