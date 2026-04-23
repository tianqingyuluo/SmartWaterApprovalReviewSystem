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

- 接口定义在 `service/功能/` 下，实现在 `impl/` 下
- 事务注解 `@Transactional` 加在 Service 实现方法上
- 一个 Service 方法只做一件事

---

## Python 代码规范

### 通用规则

- 使用 Type Hints 标注所有函数签名
- 使用 Pydantic 做数据校验
- 异步接口使用 `async def`

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
