# 日志规范

> Java + Python 的日志使用规范。

---

## Java 日志

### 框架

- 使用 SLF4J + Logback（Spring Boot 默认）
- 使用 `@Slf4j` 注解（Lombok）

### 日志级别

| 级别 | 用途 |
|------|------|
| `ERROR` | 系统异常、影响功能的错误 |
| `WARN` | 可恢复的异常、需要关注的情况 |
| `INFO` | 关键业务操作（审批提交、审查完成等） |
| `DEBUG` | 开发调试信息，生产环境关闭 |

### 规范

```java
@Slf4j
@Service
public class ApprovalServiceImpl {

    public void submitApproval(ApprovalSubmitDTO dto) {
        log.info("提交审批申请: userId={}, title={}", dto.getUserId(), dto.getTitle());
        // 业务逻辑
        log.info("审批申请提交成功: approvalId={}", record.getId());
    }
}
```

### 规则

- 使用参数化日志 `log.info("msg: {}", value)`，**禁止**字符串拼接
- ERROR 级别必须包含异常对象：`log.error("操作失败", e)`
- **禁止**在循环中打印 INFO 日志
- **禁止**记录敏感信息（密码、身份证号等）

---

## Python 日志

### 框架

- 使用 Python 标准 `logging` 模块

### 规范

```python
import logging

logger = logging.getLogger(__name__)

def parse_document(file_path: str):
    logger.info("开始解析文档", extra={"file_path": file_path})
    # 解析逻辑
    logger.info("文档解析完成", extra={"file_path": file_path, "pages": page_count})
```

### 规则

- 每个模块用 `logging.getLogger(__name__)` 获取 logger
- AI 服务调用需记录输入摘要和输出结果
- LangChain Agent 的每一步推理需记录 DEBUG 日志
