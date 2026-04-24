# SmartWater 总体设计与路线规划

## Goal

为 SmartWaterApprovalReviewSystem 建立一个团队共享的宏观设计父任务，用来沉淀项目总体路线、功能域边界、阶段计划、子任务拆分和团队分派规则。该父任务不直接承载业务实现，而是作为团队任务看板和架构决策入口。

## What I Already Know

* 仓库当前是单仓库结构，已有 Java 后端骨架与 Python 服务骨架。
* Java 服务位于 `java-services/water-approval/`，使用 Spring Boot `3.5.13`、Java `21`，当前只包含 Web starter 和测试 starter。
* Python 服务位于 `python-services/smart-water-approval-review-system-py/`，要求 Python `>=3.12`，当前无业务依赖。
* `docs/` 中已提交取水许可办理相关参考资料，包括申请书、填报说明、流程材料、证照样例、国民经济分类国标。
* `.trellis/spec/backend/` 与 `.trellis/spec/frontend/` 目前仍是模板化占位，需要后续随项目实现逐步补充真实约定。
* Trellis 任务是团队共享的，`.trellis/tasks/**` 进入 Git 后同事可以拉取查看；`.trellis/.current-task` 与 `.trellis/.developer` 是个人本地状态。

## Assumptions (Temporary)

* 项目目标是构建一个面向取水许可或水利审批材料的智能审核/辅助审批系统。
* Java 服务更适合作为主业务 API、流程、权限、数据持久化入口。
* Python 服务更适合作为文档解析、智能审核、规则/模型调用等 AI 或文本处理能力入口。
* 前端尚未创建，后续需要单独决定技术栈和任务边界。

## Open Questions

* 审核推理模型供应商尚未最终选择，需要通过 `smartwater-review-inference-vendor-contract` 子任务完成调研与适配契约。
* 具体数据库、对象存储和部署环境尚未最终选择，应在后端提交与存储子任务中形成可替换配置方案。
* 团队成员真实 owner 尚未分派，当前首批子任务先由 `tianqingyuluo` 占位负责。

## Product Direction Options

### Option A: 申请材料助手

面向申请人，重点解决“材料怎么填、缺什么、格式是否正确”的问题。

* 核心价值：降低申请准备门槛。
* MVP 功能：材料清单、表单填报、材料上传、基础完整性检查。
* 风险：审批侧价值较弱，智能审核深度有限。

### Option B: 智能审核辅助

面向审批人员，重点解决“材料是否齐全、字段是否合理、审核意见如何生成”的问题。

* 核心价值：提高审核效率，最贴合“Approval Review System”的命名。
* MVP 功能：材料上传、字段抽取、AI 审核推理、问题清单、审核意见草稿。
* 风险：需要定义模型输出约束、可解释性边界和人工复核入口。

### Option C: 审批流程管理

面向主管部门，重点解决“受理、初审、复核、退回补正、办结”的流程协同问题。

* 核心价值：形成完整业务闭环。
* MVP 功能：流程状态机、角色权限、待办列表、材料流转。
* 风险：范围较大，早期容易陷入通用 OA/工作流系统。

## Material-Based Assessment

根据 `docs/参考资料/取水许可办理需资料及流程.docx`、`docs/参考资料/填报说明.docx`、`docs/参考资料/申请书.docx` 的内容，当前材料更强烈指向 **Option B: 智能审核辅助**，而不是完整审批流系统。

### Evidence from Materials

* 办理流程材料包含大量审核依据：无需办理取水许可证情形、审批权限、延续依据、变更依据、水资源论证分类、专家评审组人数要求、公示期限、现场验收与发证时限。
* 办理流程材料明确列出材料清单：法人身份证、营业执照、申请报告、第三者利害关系说明、取水申请书、水资源论证、取水许可证申请书、取水工程验收申请、取水工程或设施验收报告。
* 填报说明材料是字段级规则说明：申请人、统一社会信用代码、住所、行业类别、项目概况、取水量、水源类型、取水地点、取水用途、计量方式、退水方式等字段都有明确填写规则。
* 申请书材料是结构化表单模板，天然适合做字段抽取、字段校验、缺失项检查和审核意见生成。
* 图片材料包括营业执照、身份证、驾驶证样例，更像是材料识别/证照信息抽取的输入样例，而不是审批流状态设计的核心依据。

### Recommendation

MVP 主线建议采用 **智能审核辅助**，并且同时包含申请人侧入口，但范围要刻意收敛：

* 主目标：帮助审批人员快速判断材料是否齐全、字段是否合理、是否触发办理/公示/论证/专家评审等规则。
* 申请人侧：支持申请书、营业执照、身份证等材料上传、基础材料清单管理和 AI 预检查。
* 用户已确认：申请人侧 MVP 深度为“材料提交 + AI 预检查”，不包含补材料闭环。
* 用户已确认：MVP 暂不做账号体系，申请人侧采用演示型或匿名提交模式，通过任务 ID / 会话 ID 追踪一次提交结果。
* 用户已确认：MVP 不支持多轮材料版本管理；一次提交对应一次解析与审核结果。
* 用户已确认：MVP 第一版材料范围收敛为 `申请书 + 营业执照 + 身份证`。
* 用户已确认：审批人员侧 MVP 只展示 AI 结果页，不包含人工编辑、人工改写或流转动作。
* 用户已确认：前端第一版采用演示型双页应用，而不是完整产品式信息架构。
* 用户已确认：无账号模式下，审批人员通过 `任务 ID / 会话 ID` 进入结果页，不提供提交列表。
* 用户已确认：OCR + AI 审核采用异步任务处理，提交后立即返回任务 ID / 会话 ID，前端轮询任务状态和结果。
* 用户已确认：第一版直接接入真实数据库与对象存储，而不是本地文件系统演示存储。
* 用户已确认：申请人侧只展示基础 AI 提示，例如缺失材料、明显字段问题和重新上传建议，不展示审批侧详细分析。
* 用户已确认：MVP 第一版不支持审核结果导出，结果仅在页面中展示。
* 用户已确认：法规知识包第一版不提供人工维护入口，法规依据、材料清单和提示词片段先通过静态配置或种子数据管理。
* 用户已确认：MVP 第一版支持图片与 PDF 上传，不支持 Word/Docx 作为首批输入格式。
* 用户已确认：上传采用按材料类型固定上传位的方式，不做自由上传后自动分类。
* 用户已确认：每种材料在 MVP 中只支持上传一个文件，不支持单个材料多文件上传。
* 用户已确认：缺失部分材料时仍允许提交，系统返回缺失材料提示和对已上传材料的预检查结果。
* 用户已确认：MVP 第一版只支持单申请人、单水源，不支持共同申请人和多个水源。
* 暂不优先做完整审批流：受理、初审、复核、退回补正、办结可以在 V1/V2 作为协同流程扩展。
* 用户已确认：MVP 接入真实 OCR / 大模型能力，不采用纯手填字段演示作为主方案。
* 用户已确认：MVP 同时包含申请人侧入口，而不只服务审批人员。

### MVP Shape from Materials

* 材料清单检查：按取水许可材料清单判断缺失项。
* 字段结构化：从申请书中抽取申请人、统一社会信用代码、行业类别、取水量、水源类型、取水地点、取水用途、计量方式、退水方式等字段。
* 证照识别：从营业执照、身份证中抽取主体身份信息，用于与申请书内容做基础一致性校验和审核提示。
* 简化数据模型：第一版仅处理单申请人、单水源场景，避免共同申请人份额分配和多水源表格展开。
* 规则审核：基于材料中的法规和流程规则输出审核提示，例如是否无需办理、审批层级、公示要求、水资源论证类型、专家评审人数、延续/变更条件。
* 审核意见草稿：生成问题清单和可解释的审核建议，引用命中的材料依据。
* AI 审核推理：基于已抽取字段、上传材料内容和法规依据，生成问题清单、审核意见草稿、初步结论和需要人工复核的风险点。
* 双端协同：申请人可先看到材料缺失项和基础 AI 提示，审批人员可看到更完整的审核建议与人工复核入口。
* 结果追踪：单次提交生成任务 ID / 会话 ID，用于查看该次解析和审核结果，不要求用户登录。
* 无版本管理：同一提交不支持反复补传和历史版本对比。
* 审批人员结果页：仅展示抽取字段、问题清单、审核建议、风险提示和材料摘要，不提供在线编辑或流程提交按钮。
* 申请人结果页：仅展示基础提示，不显示审批侧详细问题清单、推理过程或结论草稿。
* 前端形态：第一版为双页演示应用，至少包含“申请人提交页”和“审批人员结果页”。
* 结果访问方式：申请人提交后获得任务 ID / 会话 ID，审批人员凭该标识直接查看对应结果页。
* 异步处理：前端提交材料后进入处理中状态，后端异步完成 OCR、字段抽取和 AI 审核，前端通过轮询获取状态与最终结果。
* 真实存储：材料文件进入对象存储，任务状态、抽取结果、AI 审核结果和元数据进入数据库，避免把 MVP 锁死在演示型本地存储方案上。
* 无导出：第一版审核结果仅在页面中查看，不提供 PDF、Word、Markdown 或打印模板导出。
* 静态知识包：法规依据、材料清单和审核提示词由后端配置或初始化数据提供，不在前端暴露编辑入口。
* 文件格式：第一版支持 `jpg/jpeg/png/pdf`，不支持 `doc/docx`。
* 上传组织：申请书、营业执照、身份证分别使用固定上传位，前后端都基于材料类型处理，不做自由上传自动分类。
* 单文件约束：每个材料槽位只接受一个文件，避免多页合并、文件排序和多文件聚合解析带来的复杂度。
* 缺失容忍：允许缺少部分材料后提交，系统需明确区分“缺失材料提示”和“基于现有材料生成的预检查结果”。

## Decision (ADR-lite)

**Context**: `docs/` 中的申请书、填报说明和办理流程材料都包含大量字段级规则和审核依据。若只做手填字段演示，无法体现“智能审核辅助”的核心价值。  
**Decision**: MVP 需要接入真实 OCR / 大模型能力，用于材料识别、字段抽取和审核意见草稿生成；接入方式采用云 API 优先，不采用本地模型作为第一阶段主路径。  
**Consequences**: 需要设计可替换的 AI/OCR 接口边界、云厂商密钥配置、文件上传与解析任务状态、失败重试、人工校正入口和可解释审核输出；同时需要将 OCR 识别与审核推理解耦，避免把不同能力混在同一个模型职责中。

## AI / OCR Integration Direction

* MVP 采用云 API 接入真实 OCR / 大模型能力。
* OCR 首选供应商：GLM OCR。
* Java 后端负责业务 API、材料记录、审核任务状态和权限边界。
* Python 服务负责云 API 调用编排、文档解析、字段结构化和审核辅助生成。
* 云 API 密钥必须通过环境变量或部署密钥注入，不写入 Git。
* 第一阶段仍保留内部接口抽象，例如 `DocumentParser`、`CredentialExtractor`、`ReviewAssistant`，便于后续替换云厂商或切换本地模型。
* OCR 模型与审核推理模型分离：GLM OCR 只负责识别与抽取，不承担审核推理。

## Vendor Decision

**Context**: 项目已明确需要真实 OCR / 大模型能力，且第一阶段优先采用云 API 方案。  
**Decision**: OCR 供应商选择 GLM OCR。  
**Consequences**: 后续需要补充 GLM OCR 的输入格式、返回结构、费用/限流、鉴权方式、失败重试和图片/PDF 兼容范围；Python 服务中的 OCR 适配层将以 GLM 为首个实现。

## Review AI Direction

* 审核意见生成、问题清单、结论草稿属于独立 AI 推理服务，不由 GLM OCR 承担。
* 该推理服务应基于：OCR/抽取得到的结构化字段、材料原文片段、法规依据摘要、材料清单和上下文提示。
* 该推理服务不应被硬编码规则主导；规则只能作为提示、约束或证据来源，而不是主决策逻辑。
* 系统输出应包含可解释内容，例如引用的字段、触发的材料依据、置信度或人工复核提示。
* 用户已确认：审核推理服务不使用 GLM OCR 所属模型能力，推理模型供应商另选。
* 用户已确认：MVP 中 AI 输出定位为“辅助建议”，包括问题清单、审核意见草稿、风险提示和材料摘要；最终判断仍由人工完成。

## Inference Vendor Decision

**Context**: OCR 已明确采用 GLM OCR，但用户认为审核意见生成、问题清单和结论草稿属于独立 AI 推理能力，不应由 OCR 模型承担。  
**Decision**: 推理服务与 OCR 服务解耦，推理模型供应商另选。  
**Consequences**: 需要单独评估推理模型的中文法规理解、长上下文能力、稳定性、成本、国内可用性以及 API 兼容性；系统内要把 `OCR adapter` 与 `Review reasoning adapter` 分成两个独立边界。

## Inference Selection Priorities

* 第一优先级：中文法规与公文理解能力。
* 这意味着模型需要更擅长处理正式中文、政策条文、表单说明、证照信息和审核语气，而不是只追求通用推理 benchmark。
* 在后续模型选型中，成本、上下文长度、国内可用性将作为次级筛选条件，而不是第一门槛。
* 用户已确认：推理模型必须选择国内可稳定访问、可用于实际接入的供应商。

## Requirements (Evolving)

* 建立项目级父任务，承载总体设计、阶段路线和任务拆分。
* 将后续实现拆成可分派、可验收的子任务，而不是直接在父任务中写业务代码。
* 每个子任务必须有明确 owner、范围、输入输出、验收标准和上下游依赖。
* 父任务 PRD 持续维护模块边界、跨模块依赖和阶段状态。
* 后续复杂技术选择必须通过 `research/` 产出调研材料，而不是只保留在对话里。

## Phase Roadmap

### MVP: 智能审核辅助闭环

MVP 聚焦“一次匿名提交 → 异步 OCR/抽取/审核 → 双页查看结果”的最小可演示闭环。

* 申请人侧：固定上传位提交 `申请书 + 营业执照 + 身份证`，允许缺失材料提交，提交后获得任务 ID / 会话 ID。
* 审批侧：通过任务 ID / 会话 ID 进入只读结果页，查看字段抽取、材料缺失、基础一致性问题、风险提示、审核意见草稿和材料摘要。
* 后端侧：Java 服务负责提交 API、任务状态、材料元数据、数据库记录、对象存储引用和查询接口。
* AI 侧：Python 服务负责 GLM OCR 适配、字段抽取、推理模型适配、审核输出结构化和失败状态回传。
* 知识侧：法规依据、材料清单、字段规则和提示词片段以静态配置或种子数据维护，不提供前端编辑入口。

### V1: 审批协同增强

V1 在 MVP 验证后补齐审批人员日常协同能力。

* 增加账号体系、审批人员登录、提交列表和待办视图。
* 增加人工备注、审核意见人工改写、补正建议和结果导出。
* 增加材料补传、历史版本和差异对比。
* 扩展更多材料类型，例如申请报告、水资源论证、利害关系说明和验收材料。

### V2: 业务流程与知识运营

V2 面向正式业务闭环和长期运营。

* 引入受理、初审、复核、退回补正、办结等流程状态机。
* 增加角色权限、通知待办、审计日志和监管统计。
* 提供法规知识包维护后台、规则版本管理和提示词评估机制。
* 支持多申请人、多水源、多文件材料、跨区域字典和复杂审批权限判断。

## Module Boundaries

| Module | Owner Task | Responsibility | Does Not Own |
|---|---|---|---|
| 域模型与契约 | `smartwater-mvp-domain-contract` | 统一材料类型、任务状态、结果 DTO、跨服务事件/接口边界 | 具体 Java/Python/前端实现 |
| Java 后端 | `smartwater-backend-submission-storage-mvp` | 提交 API、任务查询、数据库、对象存储、Python Worker 调用边界 | OCR、审核推理、前端页面 |
| Python Worker | `smartwater-python-ocr-review-worker-mvp` | GLM OCR、字段抽取、审核推理适配、结构化结果回传 | 对外业务 API、对象存储归档策略 |
| 推理模型选型 | `smartwater-review-inference-vendor-contract` | 国内可接入推理模型调研、适配接口、输出约束 | OCR 供应商、业务 UI |
| 法规知识包 | `smartwater-regulation-knowledge-pack-mvp` | 材料清单、字段规则、法规依据、提示词片段 | 知识维护后台、在线规则编辑 |
| 前端演示 | `smartwater-frontend-dual-page-mvp` | 申请人提交页、审批人员结果页、轮询、结果展示 | 账号体系、待办列表、流程操作 |
| 项目规范 | `smartwater-project-spec-hardening-mvp` | 将已验证的目录、API、错误、状态、跨服务契约写入 `.trellis/spec/` | 业务功能实现 |

## Cross-Module Flow

1. 前端申请人提交页按固定材料槽位上传文件到 Java 后端。
2. Java 后端校验文件类型和材料槽位，写入任务、材料元数据和对象存储引用。
3. Java 后端返回任务 ID / 会话 ID，并把任务置为 `PENDING` 或 `PROCESSING`。
4. Python Worker 根据任务 ID 获取材料引用，执行 GLM OCR、字段抽取、知识包约束组织和审核推理。
5. Python Worker 回写结构化抽取结果、问题清单、审核建议、风险提示、材料摘要和失败原因。
6. 前端通过轮询任务状态展示处理中、部分失败、完成等状态。
7. 申请人页只展示缺失材料、明显字段问题和重新上传建议；审批人员页展示完整只读审核结果。

## Candidate Functional Domains

* 申请材料管理：上传、归档、材料清单、证照样例管理。
* 申请人入口：材料提交、AI 预检查结果查看。
* 表单结构化：申请书、填报说明、证照信息的字段抽取和校验。
* 智能审核：AI 推理、缺失材料检查、风险提示、审核意见草稿。
* 审批流程：受理、初审、复核、退回补正、办结等流程状态。
* 用户与权限：申请人、审批人员、管理员等角色和操作边界。
* 通知与待办：补正通知、审核待办、状态变更提醒。
* 审核报告：审核结论、问题清单、材料摘要、可导出报告。
* 基础数据：国民经济分类、行政区划、行业类型、许可类型等字典。

## MVP Child Tasks

| Task | Priority | Dev Type | Assignee | Scope | Key Output |
|---|---:|---|---|---|---|
| `04-24-smartwater-mvp-domain-contract` | P0 | fullstack | `tianqingyuluo` | architecture | MVP 域模型、状态机、跨模块 DTO 与接口契约 |
| `04-24-smartwater-backend-submission-storage-mvp` | P0 | backend | `tianqingyuluo` | backend | Java 提交/查询 API、数据库与对象存储边界 |
| `04-24-smartwater-python-ocr-review-worker-mvp` | P0 | backend | `tianqingyuluo` | ai-worker | Python OCR/抽取/审核 Worker 与回写契约 |
| `04-24-smartwater-review-inference-vendor-contract` | P0 | fullstack | `tianqingyuluo` | ai-vendor | 国内推理模型选型、适配契约和输出约束 |
| `04-24-smartwater-frontend-dual-page-mvp` | P1 | frontend | `tianqingyuluo` | frontend | 双页演示前端、上传、轮询、结果展示 |
| `04-24-smartwater-regulation-knowledge-pack-mvp` | P1 | fullstack | `tianqingyuluo` | knowledge | 静态法规知识包、材料清单、字段规则和提示词片段 |
| `04-24-smartwater-project-spec-hardening-mvp` | P1 | docs | `tianqingyuluo` | spec | `.trellis/spec/` 项目规范固化 |

### Dependency Order

1. `smartwater-mvp-domain-contract` 先定义材料类型、任务状态、结果结构和 API/Worker 边界。
2. `smartwater-review-inference-vendor-contract` 与 `smartwater-regulation-knowledge-pack-mvp` 可并行推进，为 Python Worker 提供模型和知识输入。
3. `smartwater-backend-submission-storage-mvp` 与 `smartwater-python-ocr-review-worker-mvp` 基于契约并行实现，但需共享任务状态和结果 schema。
4. `smartwater-frontend-dual-page-mvp` 依赖后端 API 契约，可先 mock 接口开发，后续接真实 API。
5. `smartwater-project-spec-hardening-mvp` 在关键实现稳定后执行，把实际约定沉淀为团队规范。

## Acceptance Criteria (Evolving)

* [x] 父任务 PRD 明确 MVP、V1、V2 阶段目标。
* [x] 父任务 PRD 明确模块边界和跨模块依赖。
* [x] 至少创建第一批 MVP 子任务并挂到父任务。
* [x] 每个 MVP 子任务有 assignee、priority、dev type 和验收标准。
* [x] 已明确申请人侧与审批侧在 MVP 中各自承担的能力边界。
* [x] 已明确第一版仅支持申请书、营业执照、身份证三类材料。
* [x] 已明确无账号模式下的单次提交追踪方式。
* [x] 已明确审批人员侧只读展示，不含人工编辑和流程动作。
* [x] 已明确前端第一版为双页演示应用。
* [x] 已明确审批人员通过任务 ID / 会话 ID 访问结果页。
* [x] 已明确 OCR + AI 审核采用异步任务处理与轮询结果模式。
* [x] 已明确第一版采用真实数据库与对象存储。
* [x] 已明确申请人侧只展示基础 AI 提示。
* [x] 已明确第一版不支持审核结果导出。
* [x] 已明确法规知识包第一版不提供人工维护入口。
* [x] 已明确第一版支持图片与 PDF 上传，不支持 Word/Docx。
* [x] 已明确按材料类型固定上传位，不做自由上传自动分类。
* [x] 已明确每种材料只支持一个文件上传。
* [x] 已明确缺失材料时允许提交，并返回部分预检查结果。
* [x] 已明确第一版只支持单申请人、单水源。
* [x] 父任务初始化 `implement.jsonl` / `check.jsonl`，便于后续上下文注入。
* [ ] 团队确认后提交父任务和子任务到 Git。

## Definition of Done

* 总体路线可被团队成员理解和执行。
* MVP 子任务可独立分派，不互相争抢同一批文件。
* 关键跨模块契约有明确 owner。
* 需要技术调研的事项已转入 `research/`。
* 设计更新和任务拆分已提交到 Git。

## Technical Approach

父任务只管理规划，不直接实现业务代码。团队执行时，每个功能点创建一个子任务，子任务内再走 Trellis 标准流程：

* `planning`：完善子任务 `prd.md`。
* `init-context`：根据任务类型初始化上下文。
* `start`：开发者本地开始自己的子任务。
* `implement`：实现代码。
* `check`：质量检查。
* `completed/archive`：完成并归档。

## Out of Scope

* 本父任务不直接实现 Java/Python/前端业务代码。
* 本父任务不直接选择最终前端框架。
* 本父任务不直接接入大模型、OCR、数据库或对象存储。
* 本父任务不替代每个子任务自己的 PRD 和验收标准。

## Technical Notes

* Inspected `java-services/water-approval/pom.xml`.
* Inspected `java-services/water-approval/src/main/resources/application.yaml`.
* Inspected `python-services/smart-water-approval-review-system-py/pyproject.toml`.
* Inspected `python-services/smart-water-approval-review-system-py/main.py`.
* Inspected repository file layout under `docs/`, `java-services/`, `python-services/`, `.trellis/spec/`.
