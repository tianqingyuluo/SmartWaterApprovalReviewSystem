# 前端代码质量规范

> SmartWater MVP 前端的 build / test / contract 门禁。

---

## 质量命令

当前 `frontend/package.json` 提供的质量命令只有两个：

```bash
npm run test
npm run build
```

`build` 实际会执行：

```bash
vue-tsc -b && vite build
```

---

## 真实规则

- 页面和 API 适配要分开：页面调用 `api/task.ts`，adapter 在同文件内把 DTO 变成 view model
- `components/` 不能直接发 HTTP 请求
- `api/task.spec.ts` 是当前最重要的 contract 回归文件
- 任何 DTO、status 或 field mapping 变化都要补测试
- `console.log`、`any`、`// @ts-ignore` 不应该留在提交里

---

## 当前门禁

| Scope touched | Required evidence |
|---|---|
| adapter / DTO mapping | `api/task.spec.ts` 断言映射字段 |
| 页面 / 组件改动 | `npm run build` 通过 |
| contract 变更 | 至少一个字段或状态回归断言 |

---

## Forbidden Patterns

| 禁止 | 原因 |
|---|---|
| 在 `components/` 里直接写 HTTP 请求 | 破坏分层 |
| 在页面里直接复制后端 DTO 结构 | 视图层会被 API 细节污染 |
| 重复定义状态标签/材料标签 | 容易漂移 |
| 使用 `any` 或 `// @ts-ignore` 绕过类型 | 丢失 contract 保证 |
| 提交时保留调试 `console.log` | 污染生产代码 |

---

## Scenario: Adapter Regression Gate

### 1. Scope / Trigger

- Trigger: 新增后端字段、调整状态枚举、修改材料表单字段名、调整 reviewer visibility 或变更页面文案时。

### 2. Signatures

- `api/task.ts`
  - `submitTask`
  - `getTaskStatus`
  - `getApplicantResult`
  - `getReviewerResult`
  - `toApplicantResultView`
  - `toReviewerResultView`
- Test:
  - `api/task.spec.ts`

### 3. Contracts

| Contract | Rule |
|---|---|
| backend DTO change | 先改 `types/smartwater.ts` 再改 adapter |
| adapter output | 必须稳定成页面 view model |
| tests | 断言关键字段，不只断言“没有报错” |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| `manualReviewNotice` 没有透传 | 测试应失败。 |
| `MATERIAL_FORM_FIELDS` 和后端字段名不一致 | 测试应失败。 |
| reviewer result 的 `extractedFields` 仍是未知结构 | 必须先归一化再交给页面。 |

### 5. Good/Base/Bad Cases

- Good: `ReviewerPage` 只拿 `ReviewerResultView` 渲染。
- Base: `api/task.ts` 负责 DTO → view model。
- Bad: 每个组件或页面都自己重复格式化风险提示和依据字符串。

### 6. Tests Required

- `api/task.spec.ts` 至少覆盖：
  - reviewer `manualReviewNotice`
  - risk hint 格式化
  - applicant suggestion 生成
  - material form field 映射

### 7. Wrong vs Correct

#### Wrong

```ts
const dto = res.data.data
task.value = dto
```

#### Correct

```ts
task.value = toReviewerResultView(statusRes.data.data, resultRes.data.data)
```
