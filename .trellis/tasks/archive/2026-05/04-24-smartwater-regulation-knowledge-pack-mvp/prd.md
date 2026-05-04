# 法规知识包 MVP

## Goal

把 `docs/参考资料/` 中与取水许可审核相关的材料清单、字段规则、法规依据和提示词片段整理为 MVP 可消费的静态知识包，为 Python Worker 的审核推理提供可解释依据。

## Parent Context

* 父任务：`.trellis/tasks/04-23-smartwater-architecture-roadmap/`
* 第一版法规知识包不提供人工维护入口。
* 知识包通过静态配置或种子数据管理。
* 审核推理不能被硬编码规则主导，规则作为提示、约束和证据来源。

## Scope

### In Scope

* 整理 MVP 材料清单，重点覆盖申请书、营业执照、身份证。
* 整理申请书字段规则和填报说明。
* 整理常见审核依据：无需办理情形、审批权限、公示要求、水资源论证、专家评审等。
* 形成可被 Worker 消费的配置结构或种子数据草案。
* 提供提示词片段和引用依据格式。

### Out of Scope

* 不实现知识维护后台。
* 不做在线规则编辑、版本审批或知识库检索系统。
* 不把规则写成不可解释的最终审批判定。
* 不覆盖所有 V1/V2 材料类型。

## Inputs

* `docs/参考资料/取水许可办理需资料及流程.docx`
* `docs/参考资料/填报说明.docx`
* `docs/参考资料/申请书.docx`
* 证照样例图片和国民经济分类材料。
* `smartwater-mvp-domain-contract` 的字段和结果结构。

## Outputs

* MVP 材料清单知识配置。
* 申请书字段规则配置。
* 审核依据条目配置。
* 提示词片段和引用格式。
* 知识包加载/消费说明。

## Requirements

* 每条知识应保留来源说明，便于审核结果引用。
* 知识包结构应稳定，便于 Python Worker 拼装提示和输出依据。
* 静态配置或种子数据不得依赖前端人工编辑。
* 对不确定或需要人工判断的规则必须标记为人工复核，而不是强制判定。

## Acceptance Criteria

* [x] 整理出 MVP 材料清单和缺失材料提示文本。
* [x] 整理出申请书核心字段及填报规则。
* [x] 整理出首批审核依据条目及来源说明。
* [x] 定义知识包配置结构或种子数据格式。
* [x] 定义提示词片段和依据引用格式。
* [x] 明确哪些规则只能作为人工复核提示。

## Dependencies

* Depends on `smartwater-mvp-domain-contract` for field names and result schema.
* Feeds `smartwater-python-ocr-review-worker-mvp` with knowledge inputs.
* Feeds `smartwater-review-inference-vendor-contract` with prompt and output constraints.

## Definition of Done

* Worker 可通过稳定结构加载知识包并生成可解释审核结果。
* 知识包范围足够支撑 MVP，但不冒充完整法规系统。
* 后续 V1/V2 可在该结构上扩展材料和规则。
