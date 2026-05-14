# CP1 证据映射总表

> 本文档将 CP1 评分点映射到 MVP 现有证据，标注缺口并关联后续任务。
> 对应任务：`v1-cp1-docs-git-demo-evidence`

---

## 评分项总览

| 编号 | 评分项 | 证据状态 | MVP 证据位置 | 缺口说明 | 后续任务 |
|------|--------|----------|--------------|----------|----------|
| **CP1-A** | **Java 基础架构证据** | | | | `v1-cp1-java-architecture-evidence` |
| A1 | Spring Boot 项目结构说明 | 已有 | `java-services/water-approval/` 单模块结构 | 无缺口 | — |
| A2 | MySQL / MyBatis-Plus 使用说明 | 已有 | `java-services/water-approval/src/main/resources/application.yaml` | 无缺口 | — |
| A3 | RustFS S3 兼容对象存储接入证据 | 已有 | `application.yaml` 中 `storage.s3` 配置段 | 无缺口 | — |
| A4 | 现有 API 截图或接口说明 | 已有 | `java-services/water-approval/API.md` | 无缺口 | — |
| A5 | 能启动 Java 服务 | 已有 | `./mvnw spring-boot:run` | 无缺口 | — |
| A6 | 能说明 Java 后端在 V1 中作为业务事实源 | 已有 | 后端提供统一 `R<T>` 响应、任务状态管理、材料存储 | 无缺口 | — |
| A7 | 能提供数据库和对象存储联通证据 | 待补齐 | 需补充启动后连通性截图或日志 | 需本地运行后截图 | CP1-A 执行时补齐 |
| **CP1-B** | **Python 服务证据** | | | | `v1-cp1-python-service-evidence` |
| B1 | Python 服务现状说明 | 已有 | `python-services/smart-water-approval-review-system-py/WORKER_API.md` | 无缺口 | — |
| B2 | OCR / LLM 配置说明 | 已有 | `.env.example` + `WORKER_API.md` | 无缺口 | — |
| B3 | FastAPI 改造前置差距清单 | 待补齐 | 当前为脚本式 Worker，非 FastAPI 服务 | 需列出差距：缺少 HTTP 服务框架、路由、依赖注入、异步任务队列等 | CP1-B 执行时补齐 |
| B4 | 能说明 MVP Worker 资产如何迁移到 FastAPI 主线 | 待补齐 | 需编写迁移路径说明 | 需整理：适配器层复用、配置迁移、任务调度改为 API 端点 | CP1-B 执行时补齐 |
| B5 | 能列出 V1 需要补齐的 Python 依赖和系统依赖 | 待补齐 | 当前 `pyproject.toml` 仅含 Worker 依赖 | 需补充 FastAPI、Uvicorn、ChromaDB、LangChain 等依赖清单 | CP1-B 执行时补齐 |
| **CP1-C** | **前端基础页面证据** | | | | `v1-cp1-frontend-evidence` |
| C1 | Vue 项目结构说明 | 已有 | `frontend/` 目录 + `package.json` | 无缺口 | — |
| C2 | 当前页面和路由截图 | 已有 | `frontend/src/router/index.ts` 定义三页路由 | 需补充浏览器运行截图 | CP1-C 执行时补齐 |
| C3 | V1 动态菜单改造差距清单 | 待补齐 | 当前为硬编码路由，无角色权限控制 | 需列出：动态菜单接口、角色路由守卫、权限指令等 | CP1-C 执行时补齐 |
| C4 | 能启动前端项目 | 已有 | `npm run dev` | 无缺口 | — |
| C5 | 能说明当前后台管理骨架如何承接三类角色工作台 | 待补齐 | 当前无角色区分 | 需说明：申请人/审批人/管理员三类视图如何在现有骨架上扩展 | CP1-C 执行时补齐 |
| **CP1-D** | **Git、运行与答辩证据整理** | | | | `v1-cp1-docs-git-demo-evidence`（本文档） |
| D1 | CP1 证据表 | 已有 | 本文档 | 无缺口 | — |
| D2 | 本地启动步骤 | 已有 | `docs/readable/operations/local-dev.md` | 无缺口 | — |
| D3 | Git 分工和提交证明整理 | 已有 | `docs/readable/cp1-git-evidence.md` | 无缺口 | — |
| D4 | 运行截图清单 | 待补齐 | 需各服务启动后截图 | 需补充：Java 启动日志、前端页面、数据库连接、API 调用等截图 | CP1-A/B/C 执行时分别补齐 |

---

## 证据缺口汇总

| 缺口项 | 优先级 | 负责子任务 | 预计补齐方式 |
|--------|--------|------------|--------------|
| 数据库和对象存储联通证据 | P1 | CP1-A | 本地启动 Java 服务后，截图或复制启动日志中 datasource 和 S3 初始化成功信息 |
| FastAPI 改造差距清单 | P1 | CP1-B | 对比当前 Worker 架构与 FastAPI 标准项目结构，列出差距条目 |
| MVP Worker 迁移到 FastAPI 路径说明 | P1 | CP1-B | 编写迁移文档，说明哪些模块可直接复用、哪些需重写 |
| V1 Python 依赖清单 | P1 | CP1-B | 在 `pyproject.toml` 或文档中补充 FastAPI、ChromaDB、LangChain 等依赖 |
| 前端页面运行截图 | P1 | CP1-C | 启动前端后截取申请列表、新建申请、AI 审核结果三页 |
| 动态菜单改造差距清单 | P1 | CP1-C | 列出从硬编码路由到动态权限菜单的改造步骤 |
| 三类角色工作台承接说明 | P1 | CP1-C | 基于现有三页说明如何扩展为角色化视图 |
| 各服务运行截图 | P1 | CP1-A/B/C | 分别补充各服务启动成功截图 |

---

## 相关文档链接

- [本地启动步骤](./operations/local-dev.md)
- [Git 分工与提交证明](./cp1-git-evidence.md)
- [开发日志](./dev-log/2026-05.md)
- Java API 文档：`java-services/water-approval/API.md`
- Java 配置文档：`java-services/water-approval/CONFIG.md`
- Worker API 文档：`python-services/smart-water-approval-review-system-py/WORKER_API.md`
