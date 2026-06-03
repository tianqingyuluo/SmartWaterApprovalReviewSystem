# Docker Compose 部署说明

部署配置集中放在仓库根目录的 `deploy/`，不复用开发环境的 `.env` 或 `application-secrets.yaml`。

## 部署范围

当前 Compose 覆盖：

- `mysql`：业务数据库，初始化脚本挂载 Java 后端权威 `schema.sql`。
- `redis`：CP4 部署拓扑预留项，当前 Java 登录态尚未接入 Redis。
- `rustfs`：S3 兼容对象存储，Java 通过 `storage.s3.*` 配置访问。
- `java-backend`：Spring Boot 后端，API context-path 为 `/api`。
- `python-ai`：FastAPI AI 服务，包含 LibreOffice headless 和中文字体。
- `frontend`：Nginx 托管 Vue 静态资源，并把 `/api` 反向代理到 Java。

## 配置边界

- 部署变量模板是 `deploy/.env.example`。
- 实际部署变量写入 `deploy/.env`，该文件不提交。
- Java 数据库密码通过 `SPRING_DATASOURCE_PASSWORD` 注入，不依赖 `application-secrets.yaml`。
- RustFS 凭证通过 `STORAGE_S3_ACCESS_KEY` 和 `STORAGE_S3_SECRET_KEY` 注入 Java。
- Python 的 `CHROMA_PERSIST_DIR` 使用容器内 `/app/data/chroma`，由 Compose volume 持久化。
- 知识库源文档目录使用容器内 `/app/knowledge_source`，由 Compose volume 持久化。

## 操作入口

详细命令见 [部署 README](../../../deploy/README.md)。

常用命令：

```bash
cd deploy
cp .env.example .env
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

健康检查：

```bash
curl http://localhost/
curl http://localhost:8080/api/ai/health
curl http://localhost:8000/health
```

知识库初始化在 `python-ai` 容器内执行：

```bash
docker compose --env-file .env cp ../docs/参考资料/. python-ai:/app/knowledge_source/
docker compose --env-file .env exec python-ai \
  uv run python -m src.ingest.cli \
  --source-dir /app/knowledge_source \
  --chunk-size 512 \
  --chunk-overlap 64
```
