# SmartWaterApprovalReviewSystem

取水许可智能初审系统，用于课程实践 CP1-CP4 检查点验收和答辩演示。系统以 Java 后端为业务事实源，Python 服务负责知识库、OCR、MCP 工具和 AI 初审，Vue 前端提供申请人、审批人员和管理员的角色化工作台。

## 项目定位

SmartWater V1 围绕“取水许可材料智能初审”建设一条可演示、可部署、可追溯的产品闭环：

- 申请人登录后提交申请书、营业执照、身份证等材料。
- Java 后端保存任务、材料、账号、权限和审查结果，并负责调用 Python AI 服务。
- Python FastAPI 下载材料，执行文档解析、图片 OCR、字段抽取、知识库检索、规则检查和 AI 辅助结论生成。
- 审批人员查看 AI 初审结果、依据、风险和字段快照，并执行通过初审、退回补正或转人工复核。
- 申请人查看补正意见并补传材料，系统重新触发审查链路。

AI 结论只作为辅助建议，不构成正式审批决定。

## 技术栈

| 模块 | 技术 |
|---|---|
| Java 后端 | Spring Boot 3.5、Sa-Token、MyBatis-Plus、MySQL、S3 兼容对象存储 |
| Python AI 服务 | FastAPI、MCP Python SDK、ChromaDB、PyMuPDF、python-docx、GLM OCR、DashScope/OpenAI-compatible LLM |
| 前端 | Vue 3、TypeScript、Vite、Vue Router、Pinia、TailwindCSS |
| 部署 | Docker Compose、Nginx、RustFS、MySQL、Redis、ChromaDB 持久化目录 |

## 仓库结构

```text
.
├── deploy/                         # CP4 Docker Compose 部署配置
├── docs/                           # 原始资料与团队可读文档
│   ├── readable/                   # 当前实现、运维、模块和开发日志说明
│   └── 参考资料/                   # 课程与业务原始参考材料
├── frontend/                       # Vue 前端
├── java-services/water-approval/   # Spring Boot 后端
├── python-services/                # Python FastAPI、Worker、MCP、知识库服务
├── tests/                          # 历史测试与辅助材料
└── .trellis/                       # Trellis 任务、规格和工作流记录
```

## 核心能力

- 最小 RBAC：`APPLICANT`、`REVIEWER`、`ADMIN` 三类角色。
- 材料提交：固定主槽位包括申请书、营业执照、身份证。
- 对象存储：材料文件写入 RustFS/S3 兼容存储，Java 只暴露受控下载边界。
- 知识库：课程参考资料 ingest 后写入 ChromaDB，供 MCP 工具和 AI 初审检索。
- MCP 工具：`knowledge_search` 和 `check_completeness` 可独立演示。
- AI 初审：OCR/解析、字段抽取、规则检查、RAG 检索和 LLM 辅助结论。
- 角色可见性：申请人只看申请人投影，审批人员/管理员可看 reviewer-only 字段快照和模型元数据。
- 初审处理：支持通过初审、退回补正、转人工复核。
- 补正闭环：申请人可在退回补正后补传材料，并重新触发 AI 审查。
- CP4 部署：Compose 覆盖前端、Java、Python、MySQL、Redis、RustFS 和持久化目录。

## 快速启动

本地开发通常需要分别启动 Java、Python 和前端；完整部署优先使用 `deploy/` 下的 Docker Compose。

### 1. Java 后端

```bash
cd java-services/water-approval
cp src/main/resources/application-secrets.yaml.example src/main/resources/application-secrets.yaml
./mvnw spring-boot:run
```

Java 默认监听：

- API base：`http://localhost:8080/api`
- 健康检查 Python：`GET /api/ai/health`

本地运行前需要准备 MySQL 和 RustFS/S3 兼容对象存储，并在 `application-secrets.yaml` 或环境变量中配置数据库密码、S3 凭证和内部 token。详细配置见 [后端配置说明](docs/readable/modules/backend/config.md)。

### 2. Python AI 服务

```bash
cd python-services/smart-water-approval-review-system-py
cp .env.example .env
uv sync
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

Python FastAPI 暴露：

- `GET /health`
- `POST /api/review/tasks`
- `GET /api/review/tasks/{aiTaskId}`

MCP 工具演示：

```bash
uv run python -m src.mcp_server.demo --list-tools
uv run python -m src.mcp_server.demo --run-samples
```

知识库 ingest：

```bash
uv run python -m src.ingest.cli --source-dir ../../docs/参考资料 --chunk-size 512 --chunk-overlap 64
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认由 Vite 启动，具体访问地址以终端输出为准。

## Docker Compose 部署

CP4 部署入口在 `deploy/`：

```bash
cd deploy
cp .env.example .env
docker compose --env-file .env up -d --build
```

默认访问入口：

| 服务 | 地址 |
|---|---|
| 前端 | `http://localhost/` |
| Java API | `http://localhost:8080/api` |
| Python FastAPI | `http://localhost:8000` |
| RustFS S3 API | `http://localhost:9000` |
| RustFS Console | `http://localhost:9001` |

详细部署变量、健康检查、知识库初始化和常见问题见 [deploy/README.md](deploy/README.md) 与 [Docker Compose 部署说明](docs/readable/operations/deployment.md)。

## 演示账号

Java 后端启动时会初始化本地演示账号：

| 角色 | 用户名 | 密码 |
|---|---|---|
| 申请人 | `applicant` | `applicant123` |
| 审批人员 | `reviewer` | `reviewer123` |
| 管理员 | `admin` | `admin123` |

这些账号只用于本地演示和课程验收。部署或真实环境必须替换默认密码，并把数据库密码、S3 凭证、`WORKER_TOKEN`、`INTERNAL_API_TOKEN`、OCR/LLM/Embedding API key 写入未提交的本地配置文件或部署环境变量。

## 常用验证命令

```bash
cd frontend
npm run test
npm run build
```

```bash
cd python-services/smart-water-approval-review-system-py
uv run python -m compileall src main.py
uv run python -m pytest
```

```bash
cd java-services/water-approval
./mvnw test
```

```bash
docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml config --quiet
```

## 文档索引

- [项目可读文档](docs/readable/README.md)：团队维护的当前实现、模块说明、运维说明和开发日志入口。
- [Docker Compose 部署 README](deploy/README.md)：部署步骤、环境变量、健康检查和故障处理。
- [后端 API 与权限说明](docs/readable/modules/backend/api.md)：登录、角色、任务、结果和补正接口边界。
- [后端配置说明](docs/readable/modules/backend/config.md)：Java 调 Python、调度失败和本地联调配置。
- [Worker 与 Java 回写接口](docs/readable/modules/worker/api.md)：FastAPI、Worker 领取、下载、状态更新和结果回写契约。
- [Worker 适配器文档](docs/readable/modules/worker/adapters.md)：OCR、审核推理和适配器边界。
- [前端页面与角色可见性](docs/readable/modules/frontend/state-and-visibility.md)：登录态、页面入口、申请人/审批人员可见性。
- [CP3.5 真实端到端验收证据](docs/readable/cp3-5-real-e2e-evidence.md)：真实账号、真实材料、RustFS、OCR/解析、MCP、LLM、Java 回写证据。
- [开发日志](docs/readable/dev-log/index.md)：按月份记录任务、验证、已知问题和后续事项。

## CP1-CP4 对应关系

| 检查点 | 当前项目证据 |
|---|---|
| CP1 项目基础架构 | Java Web、Vue 前端、Python 服务、数据库、对象存储、Git 协作记录和基础运行证据。 |
| CP2 知识库与 MCP Server | 参考资料 ingest、ChromaDB、`knowledge_search`、`check_completeness`、MCP demo 和 CP2 文档。 |
| CP3 初审 Agent 与系统集成 | 前端提交材料、Java 调 Python、Python OCR/解析/RAG/LLM、Java 回写、前端展示结构化结论。 |
| CP4 验收、报告与答辩 | Docker Compose 部署、README/API/部署文档、补正闭环、角色工作台、报告导出和答辩材料收口。 |

## 当前限制

- Redis 已进入 CP4 部署拓扑，但 Java 登录态当前仍由 Sa-Token 默认机制处理，尚未接入 Redis 持久化。
- Compose 静态配置已校验，完整联机部署仍依赖 Docker 镜像拉取、外部模型密钥和目标网络环境。
- 当前材料主槽位固定为申请书、营业执照、身份证；更多材料类型和正式审批流属于后续产品化范围。
- AI 输出是辅助初审建议，最终审批仍需要人工复核。

## 分支与任务记录

当前 V1 开发分支为 `v1`。Trellis 任务、规格和会话记录存放在 `.trellis/`，其中：

- `.trellis/tasks/` 保存 CP1-CP4 任务规划、验收标准和归档记录。
- `.trellis/spec/` 保存后端、前端和项目文档的可执行约束。
- `.trellis/workspace/` 保存开发者会话日志。
