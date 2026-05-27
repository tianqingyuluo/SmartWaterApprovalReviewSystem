# SmartWater V1 系统设计

> 状态：V1 第一版设计基线（正式版）。本文用于把 V1 的产品、课程检查点和技术架构统一成可实施设计。

Context and motivation
----------------------

SmartWater V1 需要在 MVP 已完成基础架构的前提下，补齐课程 CP2-CP4 所要求的知识库、MCP、Agent、系统集成和验收交付能力，同时把系统从演示型提交页面推进到具备账号、权限、待办、补正、版本和报告导出的产品闭环。

Goals:

* 保持 Java 后端为业务事实源。
* 使用 FastAPI 承接 Java 调用和 AI 审查任务。
* 使用 RustFS 保存上传材料。
* 使用 ChromaDB 和 MCP Server 满足 CP2 知识库检查。
* 使用规则先行、Agent 汇总的方式满足 CP3 初审和稳定性检查。
* 用前端角色化工作台支撑申请人、审批人员、管理员三类用户。

Non-goals for V1:

* 不做完整政务审批系统。
* 不做完整规则引擎。
* 不做知识库、规则、对象存储的后台管理页面。
* 不做复杂组织机构、区域权限和派单。
* 不做 PDF 报告导出。

Implementation considerations
-----------------------------

现有技术基线：

* 前端：Vue 3、Vue Router、Pinia、Axios、Vite。
* Java：Spring Boot 3.5、Java 21、MyBatis-Plus、MySQL、S3 SDK。
* Python：Python 3.12、httpx、pydantic、OpenAI-compatible SDK 风格适配。
* 对象存储：复用 MVP 已搭建的 S3 兼容 RustFS。

关键设计原则：

* Java 保存业务状态、用户权限、材料版本和审查结果。
* Python 只负责 AI 处理、知识库、MCP、规则和 Agent。
* 长耗时 AI 流程全部异步处理。
* 结构化规则负责稳定结论；Agent 只负责汇总说明。
* 外部模型和内部服务 token 均通过配置注入，不进入 Git。
* 所有 AI 结论必须标注为“辅助建议”，不构成正式审批决定。

High-level behavior
-------------------

端到端链路：

1. 申请人登录并上传申请材料。
2. Java 校验并写入 RustFS，保存材料版本。
3. Java 创建 AI 审查任务，向 Python 传入申请 ID、材料版本 ID、预签名 URL、回调地址和幂等键。
4. Python 返回 `aiTaskId`。
5. Python 后台任务下载材料，执行解析、OCR、字段抽取、规则检查、RAG 检索和 Agent 汇总。
6. Python 回调 Java 写回结构化结果；Java 幂等保存主表、问题明细、字段快照和原始 JSON。
7. 审批人员在前端查看结果并执行审核动作。
8. 退回补正后，申请人补传材料，新版本再次触发 AI 复审。
9. Java 基于固定 Word 模板导出初审报告。

Architecture
------------

```text
Vue 前端
  -> Java Spring Boot API
      -> MySQL：用户、申请、材料、版本、审查结果、问题、字段快照、日志
      -> Redis：Sa-Token 登录态
      -> RustFS：材料对象
      -> Python FastAPI：AI 审查任务
          -> 文档解析 / GLM OCR / 字段抽取
          -> ChromaDB：知识库向量检索
          -> MCP Server 共享工具函数
          -> 结构化规则
          -> LangChain Agent
      <- Python 回调 Java 写回结果
```

Java backend design
-------------------

Java 后端负责：

* Sa-Token 登录、注册、角色、权限、Redis 登录态。
* 用户管理。
* 申请、材料、材料版本、补正意见、审批动作、操作日志。
* RustFS 上传和预签名 URL 生成。
* 调用 Python FastAPI 创建 AI 任务。
* 接收 Python 回调并幂等保存结果。
* 提供申请详情、AI 结果、字段快照、版本差异、待办列表 API。
* 使用 poi-tl 和固定模板生成 Word 初审报告。

Java 不负责：

* 文档解析、OCR、RAG、Agent 推理。
* 导出时重新调用 AI。
* 持有 Python 内部状态作为事实源。

Python AI service design
------------------------

Python AI 服务采用同一项目两个入口：

* FastAPI 入口：被 Java 调用，创建 AI 审查任务并执行后台处理。
* MCP Server 入口：独立启动，暴露 `knowledge_search` 和 `check_completeness`。

两个入口共享：

* 知识库 ingest。
* ChromaDB 检索。
* 完整性检查。
* 文档解析。
* 字段抽取。
* 结构化规则。

文档处理：

* `.doc`：LibreOffice headless 转 `.docx`，需要 `SOFFICE_PATH`、超时、临时目录和中文字体。
* `.docx`：`python-docx` 提取段落和表格。
* `.pdf`：PyMuPDF 提取文本和文本块；文本不足时渲染为图片后走 OCR。
* 图片：GLM OCR / layout parsing。

Knowledge base design
---------------------

ChromaDB 采用 Python 服务本地持久化目录：

* 配置示例：`CHROMA_PERSIST_DIR=./data/chroma`。
* Docker Compose 挂载持久化 volume。
* ingest 支持清空重建或幂等重建。
* ingest 输出文档数、chunk 数、向量条目数。

文本切分采用“文档结构优先 + 固定长度兜底”：

* 优先按标题、法律条款、材料清单项、表格行、填报字段说明切分。
* 超长块再按固定长度或 token 窗口切分。
* 元数据保留来源文件、资料类型、章节/标题、页码或段落序号、chunk 序号。

Embedding 使用外部 API：

* `EMBEDDING_PROVIDER`
* `EMBEDDING_MODEL`
* `EMBEDDING_BASE_URL`
* `EMBEDDING_API_KEY`

MCP design
----------

MCP Server 必须可独立启动和演示。

V1 至少提供：

* `knowledge_search(query, top_k, filters)`：检索课程资料依据片段。
* `check_completeness(materials, extracted_fields)`：检查材料和关键字段完整性。

FastAPI 内部 Agent 主线可以直接调用共享工具函数；MCP Server 用于课程演示和协议验收。后续可增加 MCP client，使 Agent 严格通过 MCP 调工具。

Review rule design
------------------

规则实现采用“YAML/JSON 元数据 + Python 检查函数”。

规则输入：

* 材料清单。
* 申请书字段。
* 营业执照字段。
* 身份证字段。
* 解析质量。
* 检索依据。

规则输出：

* `code`
* `severity`
* `materialSlot`
* `field`
* `message`
* `evidence`
* `suggestion`
* `requiresManualReview`
* `conclusionEffect`

首批规则分类：

* 材料完整性。
* 材料类型。
* 申请书关键字段。
* 跨材料一致性。
* 人工复核触发。

Agent design
------------

LangChain Agent 采用“规则先行 + Agent 汇总”。

执行顺序：

1. 材料下载。
2. 文档解析/OCR。
3. 字段抽取。
4. 结构化规则检查。
5. RAG 检索。
6. Agent 汇总说明、修改建议和人工复核提示。

Agent 不决定规则是否命中。若 Agent 失败或超时，系统仍保存规则结果，整体结论降级为需人工复核，并记录结构化错误。

Integration and authentication
------------------------------

Java-Python 内部接口：

* 采用 `X-Internal-Token`。
* token 通过环境变量或部署配置注入。
* Java 调 Python 和 Python 回调 Java 均携带内部 token。
* 使用 `aiTaskId` / `idempotencyKey` 保证重复回写幂等。

文件访问：

* Java 上传材料到 RustFS。
* Java 创建 AI 任务时生成短期预签名下载 URL。
* Python 只通过预签名 URL 下载材料，不持有 RustFS access key / secret key。

Data model
----------

建议 Java 侧表按以下概念拆分：

* `user_account`
* `role`
* `user_role`
* `application`
* `application_material`
* `material_version`
* `ai_review_task`
* `ai_review_result`
* `ai_review_issue`
* `extracted_field_snapshot`
* `review_operation_log`
* `correction_request`
* `report_export_record`

AI 结果持久化：

* 主表保存整体审查结果和原始 JSON。
* 问题表保存结构化问题。
* 字段快照表保存关键抽取字段。

Frontend design
---------------

V1 页面范围：

* 登录。
* 注册。
* 申请人工作台。
* 审批人员工作台。
* 管理员工作台。
* 我的申请列表。
* 审批待办列表。
* 申请详情。
* 上传/补正。
* AI 初审结果。
* 版本对比。
* 用户管理。
* 报告导出入口。

申请详情页集中展示：

* 材料清单和版本。
* 系统识别信息。
* AI 初审辅助结论。
* 结构化问题列表。
* 依据片段。
* 审批动作。
* 补正意见。
* 操作日志。
* 版本差异。

Error handling and UX
---------------------

错误分层：

* 用户错误：文件格式不支持、大小超限、必填材料缺失。
* 解析错误：文件损坏、`.doc` 转换失败、PDF 文本不可提取。
* 外部能力错误：OCR、Embedding、LLM 超时或限流。
* 内部集成错误：Python 任务失败、回调失败、RustFS 下载失败。

处理方式：

* 用户可修正的错误在前端明确提示。
* AI 失败不应导致申请丢失。
* Agent 失败时保存规则结果并标记需人工复核。
* 回调失败时 Python 有有限重试，Java 可主动查询 Python 任务状态。

Testing approach
----------------

Java：

* Sa-Token 登录、角色权限、可见性测试。
* 材料上传、RustFS object key、预签名 URL 测试。
* Python 回调幂等测试。
* AI 结果、问题、字段快照、版本差异查询测试。
* Word 报告生成测试。

Python：

* 文档解析单元测试。
* `.doc` 转换失败路径测试。
* ingest 和 ChromaDB 持久化测试。
* MCP 工具测试。
* 规则函数测试。
* Agent 失败降级测试。

前端：

* 登录/注册。
* 动态菜单。
* 申请提交。
* 审批待办。
* AI 结果详情。
* 补正和版本差异。

集成：

* Java -> Python -> Java 回调全链路。
* RustFS 预签名 URL 下载。
* 同一用例多次运行结构化结论一致。

Acceptance criteria
-------------------

* 能以申请人身份提交申请材料并触发 AI 审查。
* 能以审批人员身份查看 AI 初审辅助结果和结构化问题。
* 能退回补正，申请人补传后形成新版本并触发复审。
* 能展示材料、字段、问题三类版本差异。
* 能导出 Word 初审报告。
* MCP Server 能独立启动并演示工具。
* ChromaDB ingest 可重复运行并输出统计。
* Java-Python 内部接口带内部 token 且回调幂等。
