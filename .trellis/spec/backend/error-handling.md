# 错误处理规范

> SmartWater Java 服务与 Python Worker 的实际错误契约。

---

## Java 错误模型

当前 Java 服务统一使用 `R<T>` 作为 JSON 响应包裹：

```java
@Data
public class R<T> {
    private int code;
    private String message;
    private T data;
}
```

业务错误使用 `BusinessException`：

```java
@Getter
public class BusinessException extends RuntimeException {
    private final int code;
}
```

全局异常处理入口是 `GlobalExceptionHandler`：

- `BusinessException`：保留业务 code 返回
- `MethodArgumentNotValidException`：返回 `400`
- 其他异常：记录 `ERROR` 日志并返回 `500`

### 当前约定

- HTTP 状态通常仍是 `200`，业务成败由 `R.code` 判断。
- 只有材料下载这类二进制接口走 HTTP 语义，不包 `R<T>`。
- Worker 调用 Java JSON API 时，必须同时判断：
  - `raise_for_status()` 成功
  - JSON 中 `code == 200`

---

## Worker 鉴权错误

带 `@WorkerApi` 注解的端点必须经过 `WorkerTokenInterceptor`：

- 缺少服务端配置 token：抛 `BusinessException(403, ...)`
- 请求头 `X-Worker-Token` 缺失或错误：抛 `BusinessException(403, ...)`

当前受保护路径由 `MybatisPlusConfig#addInterceptors` 注册：

- `/task/**`
- `/material/**`

是否真正受保护，取决于 controller 或方法上是否打了 `@WorkerApi`。

---

## 状态流转错误

`ProcessingStatus.validateTransition` 是当前唯一权威状态流转校验点：

- 当前状态非法：`400`
- 目标状态非法：`400`
- 流转不允许：`409`
- 相同状态重复写入：允许直接返回，不报错

这部分 contract 变更必须同步更新：

- Java 单测
- Worker 处理逻辑
- 前端状态展示文案
- `.trellis/spec/backend/smartwater-mvp-contracts.md`

---

## Scenario: JSON API Error Contract

### 1. Scope / Trigger

- Trigger: 新增/修改 Java API、Worker 回写、结果查询、状态流转、下载接口或 session/token 校验时。

### 2. Signatures

- JSON API response:

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

- Binary response:
  - `GET /material/download?key=...`

### 3. Contracts

| Interface type | Success contract | Failure contract |
|---|---|---|
| Java JSON API | HTTP 200 and `code == 200` | HTTP 200 with business `code != 200`, or HTTP 4xx/5xx if framework-level failure |
| Material download | HTTP 200 with stream body | HTTP 4xx/5xx |
| Worker internal processing | bounded retry, then map to terminal task status | never silently swallow final task outcome |

### 4. Validation & Error Matrix

| Condition | Expected result |
|---|---|
| `sessionId` 与 `taskId` 不匹配 | 返回业务失败，不泄露他人任务结果。 |
| Worker token 未配置 | Worker API 返回 `403` 业务错误。 |
| Worker token 错误 | Worker API 返回 `403` 业务错误。 |
| 状态流转非法 | 返回 `409` 业务错误。 |
| 结果 JSON 解析失败 | 记录错误并返回 `500` 业务错误。 |
| 文件上传扩展名非法 | 返回 `400` 业务错误。 |

### 5. Good/Base/Bad Cases

- Good: `getReviewerResult` 解析失败时抛 `BusinessException` 或进入全局 `500`，而不是返回半结构化脏数据。
- Base: 重复写入相同状态允许幂等通过。
- Bad: controller 自己 `try/catch` 后吞掉错误，再返回一个“看似成功”的 `R.ok()`。

### 6. Tests Required

- Worker token：拦截器测试覆盖未配置、缺失、错误、正确四类。
- 状态流转：`400/409` 业务码必须有断言。
- 结果映射：解析失败、缺字段默认值、`manualReviewNotice` 等字段透传要有断言。
- 下载接口：至少覆盖鉴权边界和内容类型解析。

### 7. Wrong vs Correct

#### Wrong

```python
resp = client.get(url)
data = resp.json()
return data["data"]
```

#### Correct

```python
resp = client.get(url)
resp.raise_for_status()
payload = resp.json()
if payload["code"] != 200:
    raise RuntimeError(payload["message"])
return payload["data"]
```

---

## Scenario: CP3.5 Real-Chain Failure Semantics

### 1. Scope / Trigger

- Trigger: CP3.5 Java 主动调度、对象存储材料读取、文档解析/OCR、MCP Client、LLM Agent、Python 回写 Java 或真实联机验收证据发生变化时。
- Goal: 关键智能依赖失败时，系统保留明确失败、阻塞或待重试状态，不产出看似成功的智能审查结论。

### 2. Signatures

Affected boundaries:

```http
POST /api/review/tasks
PUT /api/task/{taskId}/status
PUT /api/task/{taskId}/result
GET /api/task/{taskId}/status
GET /api/task/{taskId}/result/reviewer
```

Runtime dependencies:

```text
Frontend -> Java -> RustFS -> Python FastAPI -> OCR/parser -> MCP Client -> LLM Agent -> Java callback -> Frontend
```

### 3. Contracts

| Dependency | Success contract | Failure contract |
|---|---|---|
| Java dispatch to Python | Python accepts the task and returns traceable task status | Java records dispatch failure and exposes failed/retryable state; no AI result is created |
| Object storage download | Python reads the real uploaded bytes through controlled Java/storage boundary | Download/auth/storage failure maps to failed/retryable processing state |
| OCR/parser | Real PDF/DOCX/image content becomes text blocks, tables, or extracted fields | Parser/OCR failure is explicit; no mock text or empty success payload |
| MCP Client | Agent discovers and calls tools, preserving tool-call trace | MCP unavailable means failed/blocked/retryable, not internal-function fake success |
| LLM Agent | Structured result passes local schema validation and includes model metadata | LLM/auth/rate/schema failure is explicit; rules-only output is diagnostic only |
| Java callback | Java persists status, result, metadata, and sanitized errors | Callback retry exhaustion writes failed/retryable state and queryable error summary |

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|---|---|
| Python FastAPI unavailable | Java task enters `FAILED`, `RETRYABLE_FAILED`, or equivalent retryable state; frontend shows failure summary. |
| Object storage download fails | Python does not fabricate fields; task result records storage/download failure. |
| OCR returns auth/400/5xx after retry | No fake `extractedFields`; reviewer sees sanitized OCR failure. |
| MCP Server unavailable | Agent does not call internal function fallback as final success evidence. |
| LLM returns invalid JSON after repair | Worker records schema failure and does not write partial invalid AI result. |
| Java callback retries exhausted | Python marks task failed when possible and keeps queryable local failure state. |

### 5. Good/Base/Bad Cases

- Good: OCR provider failure is logged as `dependency=OCR`, `failureCategory=UPSTREAM_5XX`, `retryable=true`, then surfaced as failed/retryable.
- Good: rules checks remain available as reviewer-only diagnostic context with copy that says intelligent review was unavailable.
- Base: missing materials can still produce explicit business findings; this is not the same as a technical OCR/LLM/MCP outage.
- Bad: return `PARTIAL_SUCCESS` with polished draft opinion when OCR, MCP, or LLM never succeeded.
- Bad: use mock/stub text, hard-coded issues, static screenshots, or hidden frontend state as CP3.5 final evidence.

### 6. Tests Required

- Java tests for Python unavailable, callback failure, status query, and frontend-visible failure summary.
- Python tests for OCR/parser/MCP/LLM failure classification and no fake result writeback.
- Cross-service or integration tests for bounded retry and sanitized error propagation.
- CP3.5 final manual or automated E2E evidence with real OCR/LLM/MCP plus failure-injection cases.

### 7. Wrong vs Correct

#### Wrong

```python
if llm_failed:
    return build_success_result_from_rules()
```

#### Correct

```python
if llm_failed:
    return ProcessingFailure(
        dependency="LLM",
        failure_category="SCHEMA_MISMATCH",
        retryable=False,
        user_summary="智能审查输出结构异常，未生成AI审查结论。",
    )
```

---

## 禁止事项

- 不要把业务错误编码塞进 `message`，却让 `code` 永远是 `200`。
- 不要让 Worker 把 HTTP 200 但业务 `code != 200` 的响应当成功。
- 不要让最终失败既不回写 `PARTIAL_SUCCESS`，也不回写 `FAILED`。
