# 目录结构

> 后端代码（Java + Python）的组织方式。

---

## 概述

本项目后端分为两部分：
- **java-services**：Spring Boot 单模块应用，负责业务逻辑、用户管理、审批流程等
- **python-services**：FastAPI 应用，负责 AI 审查（文档解析、OCR、向量化、RAG、合规审查）

Java 与 Python 之间通过 HTTP API 通信，Java 端调用 Python 端的 AI 审查接口。

---

## Java 目录布局

```
java-services/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/smartwater/
│   │   │   ├── SmartWaterApplication.java
│   │   │   ├── controller/          # REST 控制器
│   │   │   ├── service/             # 业务逻辑（按功能子包）
│   │   │   │   ├── approval/        # 审批相关
│   │   │   │   │   ├── ApprovalService.java
│   │   │   │   │   └── impl/
│   │   │   │   ├── review/          # 审查相关
│   │   │   │   │   ├── ReviewService.java
│   │   │   │   │   └── impl/
│   │   │   │   └── system/          # 系统管理
│   │   │   │       ├── UserService.java
│   │   │   │       └── impl/
│   │   │   ├── mapper/              # MyBatis-Plus Mapper 接口
│   │   │   ├── entity/              # 数据库实体类
│   │   │   ├── dto/                 # 数据传输对象
│   │   │   ├── vo/                  # 视图对象（返回给前端）
│   │   │   ├── config/              # 配置类
│   │   │   ├── common/              # 通用工具（统一响应、异常、常量等）
│   │   │   └── interceptor/         # 拦截器
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── mapper/              # MyBatis XML 映射文件
│   └── test/
│       └── java/com/smartwater/
```

## Python 目录布局

```
python-services/
├── pyproject.toml
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── api/                     # 路由定义
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── ocr.py
│   │       ├── document.py
│   │       └── review.py
│   ├── core/                    # 配置、依赖
│   │   ├── config.py
│   │   └── deps.py
│   ├── services/                # 业务逻辑
│   │   ├── ocr_service.py
│   │   ├── document_parser.py
│   │   ├── vector_store.py
│   │   ├── rag_service.py
│   │   ├── completeness_checker.py
│   │   └── compliance_agent.py  # LangChain Agent
│   ├── models/                  # Pydantic 模型
│   │   ├── request.py
│   │   └── response.py
│   └── utils/                   # 工具函数
```

---

## 模块组织规则

### Java
- **controller**：扁平结构，按功能命名如 `ApprovalController.java`
- **service**：按功能划分子包，每个子包包含接口和 `impl/` 实现目录
- **mapper / entity / dto / vo**：扁平结构
- **config**：每个配置一个类，如 `MybatisPlusConfig.java`、`RustFsConfig.java`

### Python
- **api**：按版本分目录（`v1/`），每个路由文件对应一个功能域
- **services**：每个服务一个文件，按功能命名

---

## 命名规范

### Java
| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | 大驼峰 | `ApprovalService` |
| 方法名 | 小驼峰 | `submitApproval()` |
| 常量 | 全大写下划线 | `MAX_FILE_SIZE` |
| 包名 | 全小写 | `com.smartwater.service.approval` |
| 实体类 | 与表名对应，大驼峰 | `ApprovalRecord` |
| DTO | 以 `DTO` 结尾 | `ApprovalSubmitDTO` |
| VO | 以 `VO` 结尾 | `ApprovalDetailVO` |

### Python
| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | 蛇形命名 | `ocr_service.py` |
| 类名 | 大驼峰 | `OcrService` |
| 函数/变量 | 蛇形命名 | `parse_document()` |
| 常量 | 全大写下划线 | `MAX_RETRIES` |
