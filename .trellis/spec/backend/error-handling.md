# 错误处理规范

> Java + Python 的异常和错误处理策略。

---

## Java 错误处理

### 统一响应格式

```java
@Data
public class R<T> {
    private int code;
    private String message;
    private T data;

    public static <T> R<T> ok(T data) {
        R<T> r = new R<>();
        r.setCode(200);
        r.setMessage("success");
        r.setData(data);
        return r;
    }

    public static <T> R<T> fail(int code, String message) {
        R<T> r = new R<>();
        r.setCode(code);
        r.setMessage(message);
        return r;
    }
}
```

### 自定义业务异常

```java
@Getter
public class BusinessException extends RuntimeException {
    private final int code;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }
}
```

### 全局异常处理

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public R<?> handleBusiness(BusinessException e) {
        return R.fail(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public R<?> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining("; "));
        return R.fail(400, message);
    }

    @ExceptionHandler(Exception.class)
    public R<?> handleException(Exception e) {
        log.error("未知异常", e);
        return R.fail(500, "服务器内部错误");
    }
}
```

### 使用规则

- 业务错误抛 `BusinessException`，由全局处理器统一捕获
- Controller 层不写 try-catch，除非有特殊资源清理需求
- Service 层只捕获能处理的异常，其余向上抛
- **禁止**吞掉异常（空 catch 块）

---

## Python 错误处理

### FastAPI 异常处理

```python
from fastapi import HTTPException

class BusinessError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None}
    )
```

### 使用规则

- AI 服务调用失败时返回明确的错误信息，不返回原始堆栈
- 外部服务调用（OCR、向量数据库等）必须有超时和重试机制
- LangChain Agent 执行异常需记录完整上下文日志
- Python Worker 调用 Java 后端统一 `R<T>` 接口时，必须先执行 `raise_for_status()`，再解析 JSON 并要求 `code == 200` 才算成功
- 当 Java 后端返回 HTTP 200 但业务 `code != 200`（例如 403、404、409）时，Worker 必须按失败处理，进入现有重试、降级或失败路径，不能当作成功
- 二进制下载接口（例如 `/material/download`）不走 `R<T>` 包装时，可以只按 HTTP 状态码判断成功与否
