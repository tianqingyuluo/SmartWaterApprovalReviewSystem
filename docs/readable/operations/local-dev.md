# 本地启动步骤

> 本文档记录 SmartWater 审批审查系统各服务的本地启动方式与健康检查方法。
> 对应任务：`v1-cp1-docs-git-demo-evidence`

---

## 前置条件

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Java | 21+ | Java 后端运行 |
| Maven | 3.9+（已含 wrapper） | Java 构建 |
| MySQL | 8.0+ | 业务数据库 |
| Node.js | 20+ | 前端构建 |
| Python | 3.12+ | Python Worker |
| uv | 最新版 | Python 依赖管理 |
| RustFS / MinIO | 最新版 | S3 兼容对象存储 |

---

## 1. MySQL 数据库

### 1.1 启动 MySQL

```bash
# 如使用 systemd
sudo systemctl start mysql

# 如使用 Docker
docker run -d \
  --name smartwater-mysql \
  -e MYSQL_ROOT_PASSWORD=your-password \
  -p 3306:3306 \
  mysql:8.0
```

### 1.2 初始化数据库

```bash
cd java-services/water-approval/src/main/resources/db

# 方式一：使用脚本（推荐）
chmod +x init-db.sh
./init-db.sh root your-password

# 方式二：手动执行
mysql -u root -p < schema.sql
```

### 1.3 健康检查

```bash
mysql -u root -p -e "USE smartwater; SHOW TABLES;"
# 预期输出：review_task、material_slot、review_result 三张表
```

---

## 2. RustFS / MinIO 对象存储

### 2.1 启动 MinIO（如使用 MinIO）

```bash
# 单节点模式
docker run -d \
  --name smartwater-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### 2.2 创建 bucket

```bash
# 安装 mc 客户端后
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/smartwater
```

### 2.3 健康检查

```bash
curl http://localhost:9000/minio/health/live
# 预期返回 HTTP 200
```

> 如使用 RustFS，启动方式待确认（参考项目文档或运维手册）。

---

## 3. Java 后端服务

### 3.1 配置敏感信息

```bash
cd java-services/water-approval

# 复制配置模板
cp src/main/resources/application-secrets.yaml.example \
   src/main/resources/application-secrets.yaml

# 编辑 application-secrets.yaml，填入实际密码和密钥
```

`application-secrets.yaml` 示例：

```yaml
spring:
  datasource:
    password: your-mysql-password

storage:
  s3:
    access-key: your-s3-access-key
    secret-key: your-s3-secret-key
```

### 3.2 启动服务

```bash
cd java-services/water-approval
./mvnw spring-boot:run
```

### 3.3 健康检查

```bash
# 检查服务是否启动
curl http://localhost:8080/api/task/submit -X POST
# 预期返回：任务提交成功，包含 taskId

# 检查 Java 侧 AI 服务配置与 Python 探活结果
curl http://localhost:8080/api/ai/health
# 预期返回：code=200；data.reachable=true 表示 Python HTTP 健康端点可达

# 查看知识库 ingest 运维触发命令
curl -X POST http://localhost:8080/api/ai/ingest
# 预期返回：uv run python -m src.ingest.cli ... 命令和 MCP demo 验证命令

# 或查看启动日志中以下关键字：
# - "Started WaterApprovalApplication"
# - "HikariPool-1 - Start completed"（数据库连接成功）
# - 无 S3 连接异常堆栈
```

---

## 4. Python Worker

### 4.1 配置环境变量

```bash
cd python-services/smart-water-approval-review-system-py

# 复制配置模板
cp .env.example .env

# 编辑 .env 填入实际值
```

`.env` 示例：

```bash
BACKEND_API_BASE=http://localhost:8080/api

OCR_PROVIDER=glm
OCR_GLM_API_KEY=your-glm-api-key
OCR_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

REVIEW_LLM_API_KEY=your-dashscope-or-deepseek-key
REVIEW_LLM_PROVIDER=dashscope
REVIEW_LLM_MODEL=qwen-max
REVIEW_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

WORKER_POLL_INTERVAL=5
LOG_LEVEL=INFO
```

### 4.2 知识库 ingest 与 MCP 验证

CP2 知识库 ingest 当前由 Python CLI 执行：

```bash
cd python-services/smart-water-approval-review-system-py
uv run python -m src.ingest.cli --source-dir ../../docs/参考资料 --chunk-size 512 --chunk-overlap 64
```

需要清空重建时追加：

```bash
--rebuild
```

MCP 工具验证：

```bash
uv run python -m src.mcp_server.demo --run-samples
```

### 4.3 安装依赖

```bash
cd python-services/smart-water-approval-review-system-py

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install httpx pydantic python-dotenv openai
```

### 4.4 启动 Worker

```bash
# 使用 uv
uv run python main.py

# 或直接运行
python main.py
```

### 4.5 健康检查

启动后应看到类似输出：

```
2026-04-27 10:00:00 [INFO] src.services.worker: SmartWater Worker starting...
2026-04-27 10:00:05 [INFO] src.services.worker: Processing task: SWA1B2C3...
```

---

## 5. 前端

### 5.1 安装依赖

```bash
cd frontend
npm install
```

### 5.2 启动开发服务器

```bash
cd frontend
npm run dev
```

### 5.3 健康检查

```bash
# 默认启动在 http://localhost:5173
# 浏览器访问应看到申请列表页面

# 或检查构建
cd frontend
npm run build
# 预期：无 TypeScript 错误，dist/ 目录生成成功
```

---

## 6. 完整启动顺序

```
1. MySQL      → 2. MinIO/RustFS  → 3. Java 后端  → 4. Python Worker  → 5. 前端
   (端口 3306)    (端口 9000)        (端口 8080)      (轮询后端)          (端口 5173)
```

---

## 7. 快速验证端到端流程

```bash
# 1. 提交材料
curl -X POST http://localhost:8080/api/task/submit \
  -F "applicationForm=@test.pdf" \
  -F "businessLicense=@license.jpg"

# 2. 记录返回的 taskId，查询状态
curl http://localhost:8080/api/task/{taskId}/status

# 3. 查询申请人结果
curl http://localhost:8080/api/task/{taskId}/result/applicant

# 4. 查询审批人员结果
curl http://localhost:8080/api/task/{taskId}/result/reviewer
```

---

## 8. 常见问题

| 问题 | 可能原因 | 解决方式 |
|------|----------|----------|
| Java 启动报数据库连接失败 | MySQL 未启动或密码错误 | 检查 MySQL 状态和 `application-secrets.yaml` |
| Java 启动报 S3 连接异常 | MinIO 未启动或配置错误 | 检查 MinIO 状态和 `storage.s3` 配置 |
| Worker 拉取不到任务 | Java 后端未启动 | 确认 `BACKEND_API_BASE` 地址正确 |
| Worker OCR 失败 | API Key 无效 | 检查 `.env` 中 `OCR_GLM_API_KEY` |
| 前端页面空白 | 后端未启动或跨域问题 | 确认 Java 后端已启动，检查浏览器控制台 |
| `./mvnw test` 失败 | Mockito inline agent 限制 | 在提权环境运行，或添加 `-Dnet.bytebuddy.experimental=true` |

---

## 相关文档

- [CP1 证据映射总表](../cp1-evidence.md)
- [Git 分工与提交证明](../cp1-git-evidence.md)
- Java API 文档：`java-services/water-approval/API.md`
- Java 配置文档：`java-services/water-approval/CONFIG.md`
- Worker API 文档：`python-services/smart-water-approval-review-system-py/WORKER_API.md`
