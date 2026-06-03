# 部署上下文记录

## 现有入口

* Java 后端目录：`java-services/water-approval`
* Java 启动入口：`com.tianqingyuluo.waterapproval.WaterApprovalApplication`
* Java 构建工具：Maven Wrapper，Java 21
* Java 配置：`src/main/resources/application.yaml`，大部分部署项通过环境变量注入
* MySQL schema：`java-services/water-approval/src/main/resources/db/schema.sql`
* Python AI 服务目录：`python-services/smart-water-approval-review-system-py`
* Python FastAPI 入口：`uvicorn src.api.app:app --host 0.0.0.0 --port 8000`
* Python MCP 入口：`python -m src.mcp_server.app --transport stdio|sse|streamable-http`
* Python ingest 入口：`python -m src.ingest.cli --source-dir ... --chunk-size ... --chunk-overlap ...`
* 前端目录：`frontend`
* 前端构建命令：`npm run build`
* 前端 API 基址：`/api`

## 配置边界

* Java 开发配置：`java-services/water-approval/src/main/resources/application.yaml` 与 `application-secrets.yaml`。
* Python 开发配置：`python-services/smart-water-approval-review-system-py/.env`。
* 部署配置应集中在 `deploy/`，用 `deploy/.env.example` 作为模板，实际 `deploy/.env` 不提交。
* `.gitignore` 已忽略任意位置的 `.env`，所以 `deploy/.env` 会保持本地私有。

## Compose 服务映射

| 服务 | 端口 | 用途 |
|---|---:|---|
| `frontend` | `80` | Nginx 托管前端静态资源，并反代 `/api` |
| `java-backend` | `8080` | Spring Boot 后端，真实 API 入口为 `/api/**` |
| `python-ai` | `8000` | Python FastAPI 审查任务、MCP 工具 HTTP 包装和健康检查 |
| `mysql` | `3306` | 业务数据库 |
| `redis` | `6379` | V1 部署依赖预留；当前 Java 代码未实际集成 Redis 存储登录态 |
| `rustfs` | `9000`, `9001` | S3 兼容对象存储 |

## 关键约束

* RustFS 是 V1 本地集成和部署目标；文档使用 RustFS 或 S3 兼容对象存储表述。
* ChromaDB 不作为独立服务启动，数据目录挂载到 Python 容器。
* Python 镜像必须包含 LibreOffice headless 与中文字体，支持旧版 `.doc` 转换。
* 外部模型 API key 只能放在部署 env，不写入 Git。
* Redis 当前是部署拓扑的一部分，但 Java 代码尚未配置 Sa-Token Redis 持久化依赖，应在 README 中明确“预留/待接入”。
