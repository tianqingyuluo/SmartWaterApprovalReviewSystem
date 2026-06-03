# SmartWater V1 Docker Compose 部署说明

本目录存放部署专用配置，与开发环境的 `.env`、`application-secrets.yaml` 和本地启动脚本隔离。

## 文件说明

| 文件 | 用途 |
|---|---|
| `docker-compose.yml` | 启动 MySQL、Redis、RustFS、Java 后端、Python AI 服务和前端 Nginx。 |
| `.env.example` | 部署环境变量模板，只放占位值，不包含真实密钥。 |
| `java-backend/Dockerfile` | 构建 Spring Boot Java 后端镜像。 |
| `python-ai/Dockerfile` | 构建 FastAPI AI 服务镜像，包含 LibreOffice headless 与中文字体。 |
| `frontend/Dockerfile` | 构建 Vue 前端并用 Nginx 托管静态资源。 |
| `nginx/default.conf` | 前端 Nginx 配置，将 `/api` 反向代理到 Java 后端。 |

## 前置条件

- Docker Engine 与 Docker Compose v2。
- 能访问外部模型服务的网络环境。
- 有效的 OCR、LLM、Embedding API key。
- 若宿主机已有 80、8080、8000、3306、6379、9000、9001 端口占用，需要在 `deploy/.env` 中改端口。

## 1. 准备环境变量

```bash
cd deploy
cp .env.example .env
```

编辑 `deploy/.env`，至少替换这些占位值：

- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `REDIS_PASSWORD`
- `RUSTFS_ACCESS_KEY`
- `RUSTFS_SECRET_KEY`
- `WORKER_TOKEN`
- `INTERNAL_API_TOKEN`
- `OCR_GLM_API_KEY`
- `REVIEW_LLM_API_KEY`
- `EMBEDDING_API_KEY`

`WORKER_TOKEN` 会同时配置 Java Worker API 与 Python 回写请求；`INTERNAL_API_TOKEN` 会同时配置 Java 调用 Python FastAPI 和 Python 的 `X-Internal-Token` 校验。两侧必须一致。

## 2. 构建并启动

```bash
cd deploy
docker compose --env-file .env up -d --build
```

查看状态：

```bash
docker compose --env-file .env ps
docker compose --env-file .env logs -f java-backend
docker compose --env-file .env logs -f python-ai
```

默认访问入口：

| 服务 | 地址 |
|---|---|
| 前端 | `http://localhost/` |
| Java API | `http://localhost:8080/api` |
| Python FastAPI | `http://localhost:8000` |
| RustFS S3 API | `http://localhost:9000` |
| RustFS Console | `http://localhost:9001` |

## 3. 初始化知识库

Compose 会为 Python 容器挂载 `knowledge-source` 和 `chroma-data` 两个持久化 volume。首次部署后，把知识库源文档放入 Python 容器内的 `/app/knowledge_source`，再执行 ingest：

```bash
docker compose --env-file .env cp ../docs/参考资料/. python-ai:/app/knowledge_source/
docker compose --env-file .env exec python-ai \
  uv run python -m src.ingest.cli \
  --source-dir /app/knowledge_source \
  --chunk-size 512 \
  --chunk-overlap 64
```

需要清空并重建向量库时追加 `--rebuild`：

```bash
docker compose --env-file .env exec python-ai \
  uv run python -m src.ingest.cli \
  --source-dir /app/knowledge_source \
  --chunk-size 512 \
  --chunk-overlap 64 \
  --rebuild
```

Java 的 `POST /api/ai/ingest` 仍按当前实现返回可复现运维命令，不会在 Java 容器内远程执行 Python CLI。

## 4. 健康检查

```bash
curl http://localhost/
curl http://localhost:8080/api/ai/health
curl http://localhost:8000/health
```

Java 健康检查返回 `code=200` 且 `data.reachable=true` 时，说明 Java 能访问 Python FastAPI。Python `/health` 返回 `status=ok` 时，说明服务已加载知识包；如果返回 `degraded`，先检查 `KNOWLEDGE_PACK_DIR` 和容器日志。

RustFS 使用 S3 兼容接口。可用 `mc` 验证 bucket：

```bash
mc alias set smartwater-rustfs http://localhost:9000 "$RUSTFS_ACCESS_KEY" "$RUSTFS_SECRET_KEY"
mc ls smartwater-rustfs
```

Java 后端启动时会按 `S3_BUCKET` 自动创建 bucket；如果 bucket 不存在且 Java 无法创建，检查 RustFS 凭证和 `java-backend` 日志。

## 5. 常见问题

| 问题 | 处理方式 |
|---|---|
| `docker compose config` 报变量缺失 | 确认在 `deploy/` 下执行，并传入 `--env-file .env`。 |
| Java 连接 MySQL 失败 | 检查 `MYSQL_PASSWORD`、`MYSQL_USER` 与 MySQL healthcheck；首次初始化失败时可清理 volume 后重启。 |
| Java 上传材料报 S3 未初始化 | 检查 `RUSTFS_ACCESS_KEY`、`RUSTFS_SECRET_KEY`、`S3_BUCKET` 与 RustFS 日志。 |
| Python `/health` 返回 `degraded` | 检查 `/app/knowledge_pack` 是否包含 `water_permit_mvp.json`，以及外部模型密钥是否填写。 |
| `.doc` 解析失败 | 确认 `python-ai` 镜像中 `SOFFICE_PATH=/usr/bin/soffice`，并查看 LibreOffice 转换日志。 |
| Redis 未被业务使用 | Redis 当前是 CP4 部署拓扑预留项，Java 登录态尚未接入 Redis 持久化。 |

## 6. 停止和清理

停止服务但保留数据：

```bash
cd deploy
docker compose --env-file .env down
```

清理容器和持久化 volume：

```bash
cd deploy
docker compose --env-file .env down -v
```

`down -v` 会删除 MySQL、Redis、RustFS、ChromaDB 和知识库源文档 volume。执行前确认已备份需要保留的数据。
