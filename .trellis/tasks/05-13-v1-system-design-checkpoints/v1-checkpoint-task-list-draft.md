# SmartWater V1 检查点任务清单初稿

> 状态：初稿，待评审。任务按 CP1-CP4 组织，每个检查点尽量拆成四个人可并行承担的任务包。

## 分工原则

每个检查点默认拆为四类任务：

* A：Java 后端与数据模型。
* B：Python AI 服务与知识库。
* C：前端页面与交互。
* D：文档、测试、演示与集成验收。

每个任务必须交付：

* 可运行代码或明确文档。
* 对应检查点证据。
* 最少一组验证方式。
* 与其他任务的接口契约说明。

## CP1：基础架构验收映射

目标：不重做 MVP，只把 MVP 已完成能力映射到课程 CP1，并补齐必要证据。

### CP1-A Java 基础架构证据

负责人类型：Java 后端。

交付物：

* Spring Boot 项目结构说明。
* MySQL / MyBatis-Plus 使用说明。
* RustFS S3 兼容对象存储接入证据。
* 现有 API 截图或接口说明。

验收标准：

* 能启动 Java 服务。
* 能说明 Java 后端在 V1 中作为业务事实源。
* 能提供数据库和对象存储联通证据。

### CP1-B Python 服务证据

负责人类型：Python AI。

交付物：

* Python 服务现状说明。
* OCR / LLM 配置说明。
* FastAPI 改造前置差距清单。

验收标准：

* 能说明 MVP Worker 资产如何迁移到 FastAPI 主线。
* 能列出 V1 需要补齐的 Python 依赖和系统依赖。

### CP1-C 前端基础页面证据

负责人类型：前端。

交付物：

* Vue 项目结构说明。
* 当前页面和路由截图。
* V1 动态菜单改造差距清单。

验收标准：

* 能启动前端项目。
* 能说明当前后台管理骨架如何承接三类角色工作台。

### CP1-D Git、运行与答辩证据整理

负责人类型：文档/测试/演示。

交付物：

* CP1 证据表。
* 本地启动步骤。
* Git 分工和提交证明整理。
* 运行截图清单。

验收标准：

* CP1 每个评分点都有对应证据或缺口说明。
* 缺口转成后续轻量任务。

## CP2：知识库与 MCP Server

目标：完成课程资料 ingest、ChromaDB、Embedding、MCP Server 和工具演示。

### CP2-A Java 配置与知识库触发入口

负责人类型：Java 后端。

交付物：

* Java 配置 AI 服务地址和内部 token。
* 可选的内部 ingest 触发 API 或运维说明。
* 与 Python ingest / MCP 的健康检查接口约定。

验收标准：

* Java 能配置 Python AI 服务地址。
* Java 能展示 AI 服务健康状态或至少在部署文档中说明检查方式。

### CP2-B Python ingest、ChromaDB、Embedding

负责人类型：Python AI。

交付物：

* 课程资料解析 ingest 命令/API。
* `CHROMA_PERSIST_DIR` 持久化。
* 外部 Embedding 配置。
* 文档结构优先切分。
* ingest 统计输出。

验收标准：

* 重复运行 ingest 不产生不可控重复数据，或支持清空重建。
* 输出文档数、chunk 数、向量条目数。
* 能检索到办理流程、填报说明和行业分类相关依据。

### CP2-C MCP Server 工具实现与演示

负责人类型：Python AI / 前端辅助。

交付物：

* 独立 MCP Server 启动入口。
* `knowledge_search` 工具。
* `check_completeness` 工具。
* 工具调用演示样例。

验收标准：

* MCP Server 能单独启动。
* 工具列表可展示。
* 两个工具能返回结构化结果和依据片段。

### CP2-D CP2 文档、测试与演示脚本

负责人类型：文档/测试/演示。

交付物：

* CP2 README。
* ingest 演示脚本。
* MCP 工具演示截图。
* 知识库资料范围说明。

验收标准：

* 能按文档从空 ChromaDB 重建知识库。
* 能在答辩时演示 MCP 工具查询。

## CP3：初审 Agent 与系统集成

目标：打通 Java -> Python -> Java 回调全链路，并稳定输出 AI 初审辅助结果。

### CP3-A Java AI 任务、回调与结果持久化

负责人类型：Java 后端。

交付物：

* AI 任务表。
* AI 审查结果主表。
* AI 问题明细表。
* 关键字段快照表。
* Python 创建任务客户端。
* Python 回调接口和幂等处理。
* 结果查询 API。

验收标准：

* Java 能创建 AI 审查任务。
* Python 重复回调不会生成重复结果。
* 前端可查询 AI 总结、问题列表和字段快照。

### CP3-B Python FastAPI、解析、规则与 Agent

负责人类型：Python AI。

交付物：

* FastAPI AI 审查任务接口。
* 预签名 URL 文件下载。
* `.doc` / `.docx` / `.pdf` / 图片解析。
* GLM OCR 主线。
* 混合字段抽取。
* YAML/JSON 规则元数据和 Python 检查函数。
* LangChain Agent 汇总。
* 回调 Java 和查询兜底接口。

验收标准：

* 能处理申请书、营业执照、身份证和负向驾驶证样例。
* Agent 失败时能降级为规则结果 + 需人工复核。
* 同一用例多次运行结构化结论一致。

### CP3-C 前端 AI 结果、待办和审核动作

负责人类型：前端。

交付物：

* 审批人员待办列表。
* 申请详情 AI 结果视图。
* 系统识别信息视图。
* 问题列表和依据详情。
* 通过初审、退回补正、转人工复核动作。
* 操作日志展示。

验收标准：

* 审批人员能完成三类审核动作。
* AI 结论明确标注为辅助建议。
* 页面能展示问题 code、严重程度、材料、字段、建议。

### CP3-D 集成测试与稳定性验收

负责人类型：文档/测试/演示。

交付物：

* Java-Python 全链路测试用例。
* RustFS 预签名 URL 下载验证。
* 结构化结果稳定性测试记录。
* 回调失败/查询兜底测试记录。

验收标准：

* 端到端提交能触发 AI 审查并回写结果。
* 重复运行的辅助结论、问题 code、材料/字段、严重程度一致。
* 错误场景有可解释状态。

## CP4：验收、报告与答辩

目标：完成产品闭环、报告导出、部署文档和答辩材料。

### CP4-A Java 报告导出与管理能力收口

负责人类型：Java 后端。

交付物：

* poi-tl Word 模板渲染。
* 固定模板放入 Java resources。
* 报告导出 API。
* 用户管理 API 完整收口。

验收标准：

* 能导出 `.docx` 初审报告。
* 报告包含材料清单、AI 辅助结论、问题、依据、建议、人工复核提示和审批备注。
* 导出时不重新调用 AI。

### CP4-B Python 部署、降级与演示样例

负责人类型：Python AI。

交付物：

* Python 服务部署说明。
* LibreOffice headless 和中文字体说明。
* GLM OCR、Embedding、LLM 配置说明。
* 离线/外部 API 不可用时的演示降级说明。

验收标准：

* 新环境能按说明启动 Python FastAPI 和 MCP Server。
* 外部 API 错误能返回结构化失败状态。

### CP4-C 前端角色工作台、补正和版本差异收口

负责人类型：前端。

交付物：

* 申请人、审批人员、管理员工作台。
* 上传/补正页面。
* 材料、字段、问题三类版本差异视图。
* 报告导出入口。

验收标准：

* 申请人能看到补正意见并补传材料。
* 审批人员能看到新旧版本差异。
* 管理员能管理用户和角色。

### CP4-D README、部署、API 和答辩材料

负责人类型：文档/测试/演示。

交付物：

* 总 README。
* Java API 说明。
* Python API 和 MCP 工具说明。
* Docker Compose / 部署说明。
* CP1-CP4 验收证据表。
* 答辩演示脚本。

验收标准：

* 按文档能启动前端、Java、Python、RustFS、Redis、MySQL、ChromaDB 持久化目录。
* 答辩脚本覆盖提交、AI 初审、审批动作、补正复审、版本差异、报告导出、MCP 工具演示。

## 建议里程碑顺序

1. CP1 证据映射与缺口确认。
2. CP2 ingest + ChromaDB + MCP Server。
3. CP3 Java-Python 异步 AI 审查链路。
4. CP3 前端待办、详情和审核动作。
5. CP4 补正、版本差异、报告导出。
6. CP4 文档、部署和答辩材料。

## 当前风险

* 账号/RBAC 产品骨架不能挤压 CP2/CP3 课程硬性能力。
* RustFS 预签名 URL、Python 下载和回调 Java 需要尽早联调。
* `.doc` 转换依赖 LibreOffice headless，不是 Python 包，需要部署验证。
* 外部 Embedding、GLM OCR、LLM API 需要演示前确认 Key 和网络。
* 规则和 Agent 职责必须分离，否则稳定性验收风险高。
