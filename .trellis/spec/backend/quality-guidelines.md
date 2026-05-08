# 代码质量规范

> 后端代码质量标准和禁止事项。

---

## Java 代码规范

### 通用规则

- 使用 Lombok 减少样板代码（`@Data`、`@Slf4j`、`@Builder` 等）
- DTO 参数校验使用 `jakarta.validation` 注解（`@NotBlank`、`@Size` 等）
- 所有 API 返回统一 `R<T>` 响应格式
- 使用 `LocalDateTime` 处理时间，**禁止**使用 `Date`

### Controller 层规范

```java
@RestController
@RequestMapping("/api/approval")
@RequiredArgsConstructor
public class ApprovalController {

    private final ApprovalService approvalService;

    @PostMapping("/submit")
    public R<Long> submit(@RequestBody @Validated ApprovalSubmitDTO dto) {
        return R.ok(approvalService.submitApproval(dto));
    }
}
```

- Controller 只做参数接收和调用 Service，**禁止**包含业务逻辑
- 使用构造器注入（`@RequiredArgsConstructor`），**禁止** `@Autowired` 字段注入

### Service 层规范

- 当前 MVP 的 service 接口和实现都在 `service/` 包下，没有再拆 `impl/` 子包
- `ReviewTaskServiceImpl` 负责任务提交、状态流转、结果投影和 storage 边界协调
- 事务注解 `@Transactional` 只加在写入型 Service 方法上
- 一个 Service 方法只做一件事；如果方法同时读写状态和投影结果，说明边界还应该继续收敛

---

## Python 代码规范

### 通用规则

- 使用 Type Hints 标注所有函数签名
- 使用 Pydantic 做数据校验
- 长驻 Worker、adapter 和服务边界必须可单元测试；外部 HTTP、OCR、LLM、对象存储和后端 API 调用必须能被 mock 或替换。
- 异步接口使用 `async def`；同步 Worker 代码也必须保持依赖可注入或可替换。

### 示例

```python
async def parse_document(file_path: str) -> ParseResult:
    """解析文档并返回结构化结果。"""
    ...
```

---

## 禁止事项

| 禁止 | 原因 |
|------|------|
| Controller 中写业务逻辑 | 职责不清，难以测试 |
| `@Autowired` 字段注入 | 不利于测试和不可变性 |
| 使用 `java.util.Date` | 已过时，用 `java.time` |
| 硬编码配置值 | 放到 `application.yml` 或常量类 |
| 在循环中调用数据库 | N+1 性能问题 |
| 返回 `Map<String, Object>` | 使用明确的 VO/DTO 类型 |
| 普通单元测试连接真实 MySQL、RustFS、OCR、LLM 或外网 | PR 检查不稳定，无法在 clean checkout 下复现 |
| 在 `@PostConstruct` 中无条件初始化真实中间件客户端 | 会污染 Spring context 测试和本地启动 |

---

## Scenario: SmartWater PR Test And CI Gate

### 1. Scope / Trigger

- Trigger: backend, Python Worker, storage, database, API, DTO/schema, task status, or cross-service contract changes.
- Applies to every PR targeting `mvp/smartwater` or later integration branches.
- Bugfixes from code review must include a regression test for the behavior being fixed.

### 2. Signatures

Required local commands for affected modules:

```bash
cd java-services/water-approval
./mvnw test
```

```bash
cd python-services/smart-water-approval-review-system-py
python -m compileall src main.py
python -m pytest
```

If a command is not yet available, the PR must add the missing test runner configuration or state why the module has no executable test surface yet. `compileall` is a syntax check, not a substitute for unit tests.

### 3. Contracts

PR-level quality contract:

| Area | Contract |
|---|---|
| Java unit tests | Must run in clean checkout without real MySQL, RustFS, OCR, LLM, or secrets. |
| Python unit tests | Must mock backend HTTP, OCR provider, review LLM, and object download dependencies. |
| Integration tests | May use real MySQL/RustFS only under an explicit profile or command. |
| Secrets | `application-secrets.yaml`, `.env`, provider API keys, and local credentials are never committed. |
| Object storage | Production/local integration target is RustFS through S3-compatible APIs; ordinary tests use mock/fake storage. |
| Code review bugfix | Must include a regression assertion that fails before the fix and passes after it. |

Stable contract changes that should normally be tested first or with the same commit:

- `ProcessingStatus` allowed transitions.
- Worker `X-Worker-Token` authentication.
- Applicant/reviewer visibility filtering.
- Result writeback schema, including `materialCompleteness.missing` to API `missingMaterials`.
- File extension validation and material slot count.
- Object storage key persistence and backend-mediated material download.

### 4. Validation & Error Matrix

| Condition | Expected validation |
|---|---|
| `./mvnw test` requires missing secret files | Fail the PR; use optional import or test profile. |
| Java context test initializes real RustFS/S3 client | Fail the PR; use conditional bean, mock `StorageService`, fake implementation, or integration profile. |
| Python Worker downloads material without `X-Worker-Token` when token is configured | Unit test must fail; request must include the header. |
| Worker writes `materialCompleteness.missing` but Java API returns empty `missingMaterials` | Unit/service test must fail; mapping must read the canonical field. |
| Code review fix has no regression test | Request changes unless the fix is documentation-only or explicitly untestable. |
| PR has no CI/test evidence | Request changes or require a documented manual verification exception. |

### 5. Good/Base/Bad Cases

- Good: service tests mock `StorageService`, verify task creation, access checks, status transitions, and result mapping without external services.
- Good: Worker tests use mocked `httpx` responses and assert backend calls include `X-Worker-Token`.
- Base: `./mvnw test` and `python -m pytest` pass locally and in CI with no developer-only files.
- Bad: a Spring context test fails because `application-secrets.yaml` is missing or RustFS credentials are blank.
- Bad: a PR fixes a reviewer comment by changing implementation only, with no regression test proving the bug is fixed.

### 6. Tests Required

Minimum tests for backend/Worker PRs:

| Change | Required assertions |
|---|---|
| Material submission | 0-3 fixed slots create a task; invalid extension returns a controlled error; storage upload is mocked. |
| Access control | wrong or missing `sessionId` cannot read task/result; Worker API rejects missing/wrong token. |
| Status updates | valid transitions pass; invalid transitions fail deterministically. |
| Result writeback | applicant/reviewer payloads are saved separately; `materialCompleteness.missing` appears as API `missingMaterials`. |
| Storage integration boundary | unit tests do not construct a real RustFS client; integration tests use an explicit profile/command. |
| Worker material download | request includes `X-Worker-Token`; download failure maps to partial failure, not lost task state. |
| AI/OCR failures | retryable categories are retried within bounds; exhausted failures map to `PARTIAL_SUCCESS` or `FAILED`. |

### 7. Wrong vs Correct

#### Wrong

```java
@PostConstruct
public void init() {
    s3Client = S3Client.builder()
        .credentialsProvider(StaticCredentialsProvider.create(
            AwsBasicCredentials.create(properties.getAccessKey(), properties.getSecretKey())
        ))
        .build();
    createBucketIfNotExists();
}
```

This makes ordinary Spring tests require real object-storage credentials and network access.

#### Correct

```java
@Service
@ConditionalOnProperty(name = "storage.type", havingValue = "rustfs")
public class S3CompatibleStorageService implements StorageService {
    // RustFS/S3-compatible implementation for local integration and runtime.
}
```

Then tests use one of:

```java
@MockBean
private StorageService storageService;
```

or a test-only fake storage bean under a test profile. Real RustFS belongs in integration tests with an explicit command/profile.

#### Wrong

```python
resp = client.get(download_url)
```

#### Correct

```python
resp = client.get(download_url, headers={"X-Worker-Token": config.WORKER_TOKEN})
```

The unit test must assert the header is sent when `WORKER_TOKEN` is configured.
