# CP4 Docker Compose 部署配置与 README

## Goal

为 SmartWater V1 提供一套与开发配置隔离的部署配置：在独立 `deploy/` 目录中放置 Docker Compose、部署环境变量模板、服务镜像构建文件、Nginx 反向代理配置和部署 README，使检查点 4 能按文档拉起前端、Java、Python FastAPI、RustFS、MySQL、Redis 与 ChromaDB 持久化目录。

## What I Already Know

* 用户要求配置 Docker Compose 和部署时使用的配置文件，部署配置必须与开发配置隔离，并希望放入单独目录。
* 用户写了 `depoly`，本任务采用规范目录名 `deploy/`，避免仓库中长期保留拼写错误目录。
* Java 后端已有 `application.yaml`，通过环境变量读取 MySQL、S3 兼容对象存储、Python AI 服务和内部 token 配置。
* Python 服务已有 `.env.example`，FastAPI 入口为 `uvicorn src.api.app:app --host 0.0.0.0 --port 8000`。
* 前端通过相对路径 `/api` 调 Java 后端，适合部署时由 Nginx 反向代理到 Java `/api`。
* V1 设计要求 RustFS 作为 S3 兼容对象存储进入 Docker Compose；ChromaDB 采用 Python 服务本地持久化目录，不引入独立 Chroma Server。
* `.doc` 解析依赖 LibreOffice headless 与中文字体，部署镜像需要包含这些系统依赖。

## Requirements

* 新增 `deploy/` 目录，部署相关文件集中放置。
* 新增 Docker Compose，覆盖以下服务：
  * `mysql`
  * `redis`
  * `rustfs`
  * `java-backend`
  * `python-ai`
  * `frontend`
* 新增部署专用环境变量模板，不能复用或修改开发 `.env` / `application-secrets.yaml`。
* Java 容器通过环境变量连接 Compose 网络中的 MySQL、RustFS 和 Python FastAPI。
* Python 容器通过部署 env 读取 OCR、Embedding、LLM、Java 回写地址、ChromaDB 持久化目录和知识库目录。
* 前端容器提供静态资源，并通过 Nginx 将 `/api` 反代到 Java。
* Compose 挂载 MySQL、Redis、RustFS、ChromaDB 的持久化 volume。
* 部署 README 使用中文，说明复制 env 模板、填写密钥、构建启动、初始化知识库、健康检查、常见问题和停止清理方式。

## Acceptance Criteria

* [ ] `deploy/docker-compose.yml` 能被 `docker compose config` 解析。
* [ ] `deploy/.env.example` 不包含真实密钥。
* [ ] Compose 不依赖开发专用 `.env` 或 `application-secrets.yaml`。
* [ ] Java、Python、前端 Dockerfile 路径与现有项目结构匹配。
* [ ] README 能让新环境按步骤启动服务并执行健康检查。
* [ ] 可读文档入口和开发日志记录本次部署交付。

## Out Of Scope

* 不修改业务 API、数据库 schema、前端页面逻辑或 Python 审查逻辑。
* 不实现报告导出、补正版本差异或完整 CP4 答辩脚本。
* 不提交真实外部 API key、数据库密码、RustFS 密钥或内部 token。
* 不引入独立 Chroma Server；ChromaDB 继续使用 Python 本地持久化目录。

## Technical Notes

* 任务上下文记录见 `research/deployment-context.md`。
* Compose 文件应使用 RustFS / S3 兼容表述，避免把必需中间件写成 MinIO。
* MySQL 初始化可挂载 Java 后端现有权威 schema：`java-services/water-approval/src/main/resources/db/schema.sql`。
* 前端请求基于 `/api`，Nginx 代理到 `http://java-backend:8080/api/`。
* Java 应设置 `AI_SERVICE_BASE_URL=http://python-ai:8000`、`S3_ENDPOINT=http://rustfs:9000`、`MYSQL_HOST=mysql`。
* Python 应设置 `BACKEND_API_BASE=http://java-backend:8080/api`、`CHROMA_PERSIST_DIR=/app/data/chroma`。
