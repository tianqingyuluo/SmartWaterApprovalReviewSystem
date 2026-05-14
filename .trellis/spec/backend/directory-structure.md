# 目录结构

> SmartWater MVP 当前后端实现的真实目录与分层约定。

---

## 概述

本项目当前有两个后端运行面：

- `java-services/water-approval/`：Spring Boot Java 服务，负责任务提交、状态查询、结果投影、材料下载、对象存储接入。
- `python-services/smart-water-approval-review-system-py/`：Python Worker，负责 OCR、字段抽取、审核推理与结果回写。

本文件主要约束 Java 服务的目录组织；Python Worker 的 adapter/服务边界由 [Review Reasoning Adapter](./review-reasoning-adapter.md) 和跨服务契约补充说明。

---

## Java 目录布局

当前真实目录：

```text
java-services/water-approval/
├── pom.xml
├── src/main/java/com/tianqingyuluo/waterapproval/
│   ├── WaterApprovalApplication.java
│   ├── common/           # R<T>、BusinessException、ProcessingStatus、全局异常处理
│   ├── config/           # MyBatis-Plus、拦截器注册
│   ├── controller/       # ReviewTaskController、MaterialController、WorkerApi
│   ├── dto/              # 所有请求/响应 DTO
│   ├── entity/           # review_task / material_slot / review_result 实体
│   ├── mapper/           # MyBatis-Plus BaseMapper 接口
│   ├── service/          # ReviewTaskService 与其实现
│   └── storage/          # StorageService 抽象与 S3-compatible 实现
├── src/main/resources/
│   ├── application.yaml
│   ├── application.yaml.example
│   ├── application-secrets.yaml.example
│   └── db/
│       ├── schema.sql
│       ├── init.sql
│       ├── init-db.sh
│       └── init-db.bat
└── src/test/
    ├── java/...          # 控制器、状态、服务、拦截器测试
    └── resources/        # test profile、H2 schema、mockito-extensions
```

### 当前分层职责

| 目录 | 职责 | 当前约束 |
|---|---|---|
| `common/` | 通用协议与基础错误模型 | 只放跨控制器/服务共享的基础类型，不能塞业务流程。 |
| `config/` | 框架装配和拦截器注册 | 只负责注册组件和中间件，不写业务判断。 |
| `controller/` | HTTP 边界 | 只接收参数、调用 service、返回 `R<T>` 或二进制响应。 |
| `dto/` | HTTP 请求/响应载荷 | 当前项目没有单独 `vo/`，返回模型也放在 `dto/`。 |
| `entity/` | 数据库行结构 | 与 `schema.sql` 保持同步，字段命名对应表字段语义。 |
| `mapper/` | 持久化接口 | 简单 CRUD 直接继承 `BaseMapper`。 |
| `service/` | 核心业务流转 | `ReviewTaskService` 是当前唯一业务入口。 |
| `storage/` | 对象存储边界 | 业务代码只能依赖 `StorageService` 抽象，不能直接 new S3 client。 |

---

## Python Worker 目录布局

当前真实目录：

```text
python-services/smart-water-approval-review-system-py/src/
├── config.py
├── adapters/
│   ├── ocr_adapter.py
│   └── review_adapter.py
├── mcp_server/
│   ├── app.py
│   ├── demo.py
│   └── server.py
├── models/
└── services/
    ├── field_extractor.py
    ├── knowledge_tools.py
    ├── result_writer.py
    └── worker.py
```

当前 Worker 约定：

- `adapters/` 只处理外部 OCR/推理供应商差异。
- `mcp_server/` 只放 MCP Server 启动、工具注册和本地 demo CLI，不能写知识库检索或材料完整性判断细节。
- `services/knowledge_tools.py` 负责可单测的知识库工具核心逻辑，MCP、CLI 和未来 HTTP/Worker 入口都应复用这里的函数/类。
- `services/worker.py` 负责主流程编排。
- `services/result_writer.py` 负责把标准结果 schema 回写到 Java 服务。
- 跨服务 contract 以 Java API 为准，不允许 Worker 自行发明新的 wire 字段。

---

## 命名与组织规则

### Java

| 类型 | 当前规则 | 示例 |
|---|---|---|
| 包名 | 全小写，基包固定为 `com.tianqingyuluo.waterapproval` | `com.tianqingyuluo.waterapproval.controller` |
| DTO | 以意图命名，不强制 `DTO` 后缀 | `SubmitResponse`、`ReviewerResultResponse` |
| 实体 | 与表含义一致 | `ReviewTask`、`MaterialSlot` |
| Mapper | `<Entity>Mapper` | `ReviewTaskMapper` |
| Service 接口 | `<Domain>Service` | `ReviewTaskService` |
| Service 实现 | 当前直接放在 `service/` 包下，不再额外嵌套 `impl/` | `ReviewTaskServiceImpl` |

### Python

| 类型 | 当前规则 | 示例 |
|---|---|---|
| 文件名 | snake_case | `result_writer.py` |
| 适配器 | `<domain>_adapter.py` | `review_adapter.py` |
| 服务文件 | 以业务责任命名 | `field_extractor.py` |
| MCP 模块 | 启动/注册放 `src/mcp_server/`，业务逻辑放 `src/services/` | `mcp_server/server.py`、`services/knowledge_tools.py` |

---

## Scenario: Java Service Module Layout

### 1. Scope / Trigger

- Trigger: 新增 Java API、持久化对象、对象存储集成或 Worker 协作边界时。

### 2. Signatures

- HTTP controller:
  - `ReviewTaskController`
  - `MaterialController`
- Service:
  - `ReviewTaskService`
  - `ReviewTaskServiceImpl`
- Storage:
  - `StorageService`
  - `S3StorageServiceImpl`

### 3. Contracts

- `controller/` 不直接操作 `mapper/` 或 SDK client。
- `service/` 负责 task/session 校验、状态流转、DTO 投影、材料上传下载。
- `storage/` 暴露统一签名：

```java
public interface StorageService {
    String upload(String key, InputStream inputStream, long size, String contentType);
    InputStream download(String key);
    void delete(String key);
    String getUrl(String key);
}
```

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 新增业务控制器直接引用 `Mapper` | 视为分层违规，应改为注入 service。 |
| 新增对象存储逻辑直接依赖 AWS SDK | 视为边界泄漏，应通过 `StorageService` 抽象。 |
| 新增返回类型放进 `vo/` 或 `response/` 新包 | 当前不接受；统一继续放在 `dto/`。 |

### 5. Good/Base/Bad Cases

- Good: 新增 reviewer 结果字段时，只改 `dto/`、`service/`、前端 adapter 和测试。
- Base: 继续围绕 `ReviewTaskService` 扩展，不急着拆多 service。
- Bad: 为了“分层整洁”机械引入 `service/impl/approval/` 等当前不存在的目录。

### 6. Tests Required

- 控制器新增端点：MockMvc 测试断言 `R<T>` 包装或二进制返回。
- 服务新增字段映射：service/controller 或前端 adapter 回归测试。
- 对象存储边界调整：测试必须 mock `StorageService`，不能依赖真实 S3/RustFS。

### 7. Wrong vs Correct

#### Wrong

```java
@RestController
public class ReviewTaskController {
    @Autowired
    private ReviewTaskMapper taskMapper;
}
```

#### Correct

```java
@RestController
@RequiredArgsConstructor
public class ReviewTaskController {
    private final ReviewTaskService reviewTaskService;
}
```

---

## 禁止事项

- 不要继续照搬旧模板中的 `service/<domain>/impl/`、`vo/`、`mapper XML` 结构，除非真实实现先发生变化。
- 不要在 `config/` 中加入业务状态判断或 DTO 拼装逻辑。
- 不要在 controller 中直接持有 S3 client、数据库 mapper 或跨服务 HTTP client。
