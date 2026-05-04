# SmartWater MVP 法规知识包

本目录存放 Python Worker 消费的静态法规知识包。

## 文件说明

- `water_permit_mvp.json` 是 MVP 材料清单、申请书字段规则、审核依据、提示词片段、人工复核规则和引用格式的配置源。
- `loader.py` 为 Worker 代码提供知识包加载能力，并做基础章节校验。

## 使用方式

Worker 通过下面的方式加载知识包：

```python
from knowledge_pack import load_knowledge_pack

pack = load_knowledge_pack()
```

Worker 回写结果时，应把 `pack["version"]` 作为 `knowledgePackVersion`。

调用审核推理 adapter 时，应把筛选后的知识条目作为 `knowledgeFragments` 传入。凡是允许模型引用的片段，都必须包含稳定的 `id`、`sourceId`、`sourceTitle` 和 `summary`。模型生成的 `basisRefs` 只能引用本次请求中已经传入的 ID。

## MVP 边界

MVP 固定材料槽位为：

- `APPLICATION_FORM`
- `BUSINESS_LICENSE`
- `ID_CARD`

知识包也记录了申请报告、第三者利害关系说明、水资源论证等后续材料，但这些内容在 MVP 中只作为审核提示，不作为固定上传槽位。

标记为 `manualReview: true` 的规则，或收录在 `manualReviewRules` 中的规则，不能被转换成自动批准或驳回结论。它们只能生成面向审核人员的问题提示或风险提示。
