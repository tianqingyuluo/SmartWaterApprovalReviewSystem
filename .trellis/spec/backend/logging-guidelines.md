# 日志规范

> SmartWater Java 服务与 Python Worker 当前的可执行日志约定。

---

## Java 日志

当前 Java 统一使用：

- `SLF4J + Logback`
- `@Slf4j`

### 当前实际记录点

- 任务提交、状态查询、状态更新、结果回写、材料下载
- Worker token 未配置/错误
- 文件上传成功/失败
- 对象存储 bucket 自动创建
- 全局未知异常

### 规则

- 使用参数化日志：`log.info("查询任务状态: taskId={}", taskId)`
- `ERROR` 必须带异常对象
- `WARN` 用于可恢复或可诊断的权限/配置问题
- 不记录 `sessionId` 明文之外的敏感凭证，不记录 Worker token、S3 secret、完整密钥文件内容

---

## Python Worker 日志

Python Worker 继续使用标准 `logging`。

当前需要重点记录：

- OCR / review adapter 调用开始与失败分类
- Java 后端交互失败原因（HTTP 失败 vs 业务 `code != 200`）
- 有界重试是否已耗尽
- 任务最终映射到 `PARTIAL_SUCCESS` 还是 `FAILED`

### 当前约束

- 可以记录 taskId、materialType、knowledgePackVersion、resultType
- 不记录原始密钥、完整材料正文、完整模型敏感输入
- AI 输出日志应以摘要或结构化字段为主，不把整段 prompt/response 无边界打到 INFO

---

## Scenario: Operational Logging For Task Processing

### 1. Scope / Trigger

- Trigger: 提交、轮询、状态流转、结果回写、材料下载、对象存储、OCR/LLM 调用、鉴权失败。

### 2. Signatures

Current Java logging entry points include:

- `ReviewTaskController`
- `MaterialController`
- `WorkerTokenInterceptor`
- `ReviewTaskServiceImpl`
- `S3StorageServiceImpl`
- `GlobalExceptionHandler`

### 3. Contracts

| Event | Minimum log contract |
|---|---|
| task submit | `taskId` after creation, not file binary content |
| status update | `taskId`, new status |
| worker auth failure | HTTP method + path, never token value |
| storage upload/download | storage key or task correlation id |
| unknown exception | stack trace |

### 4. Validation & Error Matrix

| Condition | Expected logging |
|---|---|
| Worker token 未配置 | `WARN`，说明 Worker API 被阻断。 |
| Worker token 错误 | `WARN`，记录 method/path。 |
| 文件上传 IO 异常 | `ERROR`，带文件名和异常。 |
| 结果 JSON 解析失败 | `ERROR`，带 taskId 和异常。 |
| S3 凭证缺失 | `WARN`，说明 storage degraded mode。 |

### 5. Good/Base/Bad Cases

- Good: `log.warn("Invalid worker token for {} {}", request.getMethod(), request.getRequestURI())`
- Base: controller 记录 taskId 和 status，不重复打印整个 request body。
- Bad: `log.info("worker token={}", token)` 或打印原始材料内容。

### 6. Tests Required

- 这类变更通常不需要断言日志内容本身，但必须保留业务行为测试。
- 若日志分支伴随鉴权/错误处理行为变化，测试应断言对应异常与返回码。

### 7. Wrong vs Correct

#### Wrong

```java
log.info("X-Worker-Token={}", token);
```

#### Correct

```java
log.warn("Invalid worker token for {} {}", request.getMethod(), request.getRequestURI());
```

---

## 禁止事项

- 不要把 token、secretKey、session cookie、完整材料正文写入日志。
- 不要在热点循环里无界打印 INFO。
- 不要为了调试把 OCR/LLM 原始完整输出长期保留在 INFO/WARN。
