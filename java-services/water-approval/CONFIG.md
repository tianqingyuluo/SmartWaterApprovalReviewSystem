# SmartWater 后端服务配置说明

## 配置文件结构

```
src/main/resources/
├── application.yaml              # 主配置文件（无敏感信息）
├── application-secrets.yaml      # 敏感配置文件（密码、密钥）
├── application-secrets.yaml.example  # 敏感配置模板
├── db/
│   ├── init.sql                  # 数据库初始化脚本
│   ├── init-db.sh               # Linux/Mac 数据库初始化
│   └── init-db.bat              # Windows 数据库初始化
```

## 快速开始

### 1. 配置敏感信息

```bash
# 复制模板文件
cp src/main/resources/application-secrets.yaml.example \
   src/main/resources/application-secrets.yaml

# 编辑 application-secrets.yaml，填入实际密码
```

**application-secrets.yaml 示例：**
```yaml
spring:
  datasource:
    password: your-mysql-password

storage:
  s3:
    access-key: your-s3-access-key
    secret-key: your-s3-secret-key

water-approval:
  ai-service:
    internal-token: your-ai-service-internal-token
```

### 2. 初始化数据库

**方式一：使用脚本**
```bash
# Windows
src/main/resources/db/init-db.bat root your-password

# Linux/Mac
chmod +x src/main/resources/db/init-db.sh
./src/main/resources/db/init-db.sh root your-password
```

**方式二：手动执行**
```bash
mysql -u root -p < src/main/resources/db/schema.sql
```

### 3. 启动服务

```bash
./mvnw spring-boot:run
```

### 4. 环境变量（可选）

如果不使用 `application-secrets.yaml`，也可以通过环境变量配置：

```powershell
# Windows PowerShell
$env:MYSQL_PASSWORD="your-password"
$env:S3_ACCESS_KEY="your-access-key"
$env:S3_SECRET_KEY="your-secret-key"
```

```bash
# Linux/Mac
export MYSQL_PASSWORD="your-password"
export S3_ACCESS_KEY="your-access-key"
export S3_SECRET_KEY="your-secret-key"
export AI_SERVICE_BASE_URL="http://localhost:8000"
export AI_SERVICE_INTERNAL_TOKEN="your-ai-service-internal-token"
```

## AI 服务与知识库配置

Java 侧通过 `water-approval.ai-service.*` 配置 Python AI/MCP 服务地址、探活路径、MCP transport 和 ingest 运维命令参数。

| 配置 | 默认值 | 说明 |
|---|---|---|
| `water-approval.ai-service.base-url` | `http://localhost:8000` | Python AI/MCP HTTP 适配服务地址。 |
| `water-approval.ai-service.health-path` | `/health` | Java 探活路径。 |
| `water-approval.ai-service.internal-token` | 空 | 探活请求携带的 `X-Internal-Token`，建议放入 `application-secrets.yaml`。 |
| `water-approval.ai-service.timeout` | `3s` | 探活连接和读取超时。 |
| `water-approval.ai-service.mcp-transport` | `streamable-http` | Python MCP Server transport 说明。 |
| `water-approval.ai-service.mcp-path` | `/mcp` | MCP HTTP transport 入口路径说明。 |
| `water-approval.ai-service.review-task.enabled` | `true` | 是否在提交材料后由 Java 主动调用 Python FastAPI 审查任务入口。 |
| `water-approval.ai-service.review-task.path` | `/api/review/tasks` | Python FastAPI 审查任务创建路径。 |
| `water-approval.ai-service.review-task.max-attempts` | `3` | Java 调度 Python 的最大尝试次数，至少为 `1`。 |
| `water-approval.ai-service.ingest.workdir` | `../../python-services/smart-water-approval-review-system-py` | 从 `java-services/water-approval` 出发的 ingest 运维命令执行目录。 |
| `water-approval.ai-service.ingest.source-dir` | `../../docs/参考资料` | 进入 Python 服务目录后的知识库源资料目录。 |
| `water-approval.ai-service.ingest.chunk-size` | `512` | ingest 分块长度。 |
| `water-approval.ai-service.ingest.chunk-overlap` | `64` | ingest 分块重叠长度。 |
| `water-approval.ai-service.ingest.rebuild` | `false` | 是否输出 `--rebuild` 重建参数。 |

验证命令：

```bash
curl http://localhost:8080/api/ai/health
curl -X POST http://localhost:8080/api/ai/ingest
```

`/api/ai/ingest` 当前返回可复现运维命令，不在 Java 进程内启动 Python ingest。Python 侧正式 REST ingest API 补齐后，再把该入口升级为远程触发。

`POST /api/task/submit` 默认会主动调用 Python FastAPI `POST /api/review/tasks`。如果 Python 接受任务，Java 将任务状态写为 `PROCESSING`；如果 Python 不可用或返回错误，Java 将任务写为 `FAILED` 并保存失败分类。普通单元测试或临时回退可设置 `AI_REVIEW_TASK_DISPATCH_ENABLED=false`，让旧 Worker 轮询路径继续处理 `SUBMITTED` 任务。

## 安全提醒

⚠️ **application-secrets.yaml 已添加到 .gitignore，请勿手动将其提交到 Git！**

如果误提交敏感信息，请立即：
1. 修改所有密码和密钥
2. 从 Git 历史中移除该文件
3. 强制推送到远程仓库
