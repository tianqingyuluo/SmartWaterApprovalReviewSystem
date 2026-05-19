# 前端 API 契约说明

## CP2 MCP 演示台

CP2 前端新增独立页面 `/mcp-demo`，用于演示 AI 知识库与 MCP 工具调用。该页面不进入 CP3 审批待办链路，也不输出正式审批结论。

### 页面调用边界

- 页面只调用 `frontend/src/api/mcpDemo.ts` 暴露的适配函数。
- `components/` 不直接发起 HTTP 请求。
- 页面状态使用局部 `ref` / `reactive` 管理，不新增全局 store。
- MCP HTTP 适配服务可用时，页面调用真实服务；服务不可用且勾选“允许演示数据兜底”时，页面展示本地演示数据并明确标识来源为“演示兜底”。

### knowledge_search

约定 HTTP 适配路径：

```http
POST /mcp/tools/knowledge_search
```

请求示例：

```json
{
  "query": "取水许可 材料",
  "top_k": 5
}
```

响应核心字段：

| 字段 | 说明 |
|---|---|
| `query` | 服务端归一后的查询文本。 |
| `requestedTopK` | 调用方请求的 `top_k` 原始值。 |
| `topK` | 实际使用的返回上限，按 MCP 工具契约限制在 1 到 50。 |
| `knowledgePackVersion` | 当前知识包版本。 |
| `results[]` | 检索结果列表。 |
| `results[].section` | 来源知识段落类型，例如 `materialChecklist`、`reviewBasis`。 |
| `results[].id` | 知识片段稳定 ID。 |
| `results[].basisRefs` | 结果引用的审查依据 ID。 |
| `results[].sourceIds` | 归一化后的来源 ID。 |

### check_completeness

约定 HTTP 适配路径：

```http
POST /mcp/tools/check_completeness
```

请求示例：

```json
{
  "materials": ["APPLICATION_FORM", "BUSINESS_LICENSE"]
}
```

响应核心字段：

| 字段 | 说明 |
|---|---|
| `submitted` | 被识别为已提交的 MVP 材料类型。 |
| `required` | MVP 必需材料类型。 |
| `missing` | 缺失材料类型。 |
| `complete` | `missing` 为空时为 `true`。 |
| `findings[]` | 缺失材料产生的结构化问题提示。 |
| `findings[].applicantMessage` | 面向申请人的补充材料提示。 |

### 演示模式限制

- 页面固定展示“演示模式 / 非正式审批结论”。
- 本地演示兜底数据只用于 CP2 展示，不代表 MCP 服务真实返回。
- 当前前端只约定 HTTP 适配路径，MCP Server 原生 transport 仍由 Python 服务负责。
