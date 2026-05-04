# Python Worker 接口文档与启动指南

## 一、Worker 依赖的 Java 后端接口

Worker 通过 HTTP 调用 Java 后端，需要以下端点：

### 1. 拉取待处理任务

**GET** `/api/task/pending`

返回所有状态为 `SUBMITTED` 或 `QUEUED` 的任务。

**响应示例：**
```json
{
  "code": 200,
  "data": [
    {
      "taskId": "SWA1B2C3D4E5F6G7H",
      "sessionId": "a1b2c3d4e5f6789012345678abcdef01",
      "status": "SUBMITTED",
      "materials": [
        {
          "materialType": "APPLICATION_FORM",
          "originalFileName": "test.pdf",
          "storageKey": "SWA1B2/APPLICATION_FORM/uuid.pdf",
          "fileExtension": "pdf",
          "uploaded": true
        },
        {
          "materialType": "BUSINESS_LICENSE",
          "originalFileName": "license.jpg",
          "storageKey": "SWA1B2/BUSINESS_LICENSE/uuid.jpg",
          "fileExtension": "jpg",
          "uploaded": true
        },
        {
          "materialType": "ID_CARD",
          "originalFileName": null,
          "storageKey": null,
          "fileExtension": null,
          "uploaded": false
        }
      ]
    }
  ]
}
```

### 2. 更新任务状态

**PUT** `/api/task/{taskId}/status`

```json
{ "status": "PROCESSING" }
```

### 3. 下载材料文件

**GET** `/api/material/download?key={storageKey}`

返回文件的 binary 流。

### 4. 回写审核结果

**PUT** `/api/task/{taskId}/result`

```json
{
  "status": "COMPLETED",
  "resultSummary": "申请材料基本完整，发现一个警告",
  "knowledgePackVersion": "water-permit-mvp-2026-04-27",
  "applicantResult": {
    "summary": "材料审核完成",
    "issues": [
      { "code": "MISSING_MATERIAL", "severity": "WARNING", "message": "缺少身份证" }
    ],
    "materialCompleteness": { "received": ["APPLICATION_FORM"], "missing": ["ID_CARD", "BUSINESS_LICENSE"], "unrecognized": [] },
    "manualReviewNotice": "AI审核结果为辅助建议"
  },
  "reviewerResult": {
    "summary": "材料审核完成",
    "issues": [
      {
        "code": "MISSING_MATERIAL",
        "severity": "WARNING",
        "message": "缺少身份证材料",
        "materialType": "ID_CARD",
        "fieldKey": null,
        "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
        "applicantVisible": true
      }
    ],
    "riskHints": [
      {
        "riskLevel": "MEDIUM",
        "description": "材料不完整",
        "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
        "requiresManualReview": true
      }
    ],
    "draftOpinion": "建议补充身份证扫描件",
    "materialCompleteness": { "received": ["APPLICATION_FORM"], "missing": ["ID_CARD", "BUSINESS_LICENSE"], "unrecognized": [] },
    "basisRefs": ["BASIS_MATERIAL_INITIAL_LIST"],
    "manualReviewNotice": "AI审核结果为辅助建议，不构成最终审批意见。",
    "modelMetadata": {
      "provider": "dashscope",
      "model": "qwen-max",
      "requestId": "req-xxx",
      "finishReason": "stop",
      "tokenUsage": { "prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700 }
    }
  }
}
```

---

## 二、启动 Python Worker

### 前置条件
- Python 3.12+
- uv (推荐) 或 pip
- Java 后端服务已启动
- GLM OCR API Key + 审核推理模型 API Key

### 步骤

**1. 配置环境变量**

```bash
cd python-services/smart-water-approval-review-system-py

# 复制配置模板
cp .env.example .env

# 编辑 .env 填入实际值
```

**.env 内容：**
```bash
BACKEND_API_BASE=http://localhost:8080/api

OCR_GLM_API_KEY=your-glm-api-key

REVIEW_LLM_API_KEY=your-dashscope-or-deepseek-key
REVIEW_LLM_PROVIDER=dashscope
REVIEW_LLM_MODEL=qwen-max
REVIEW_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

WORKER_POLL_INTERVAL=5
LOG_LEVEL=INFO
```

**2. 安装依赖**

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install httpx pydantic python-dotenv openai
```

**3. 启动 Worker**

```bash
# 使用 uv
uv run python main.py

# 或直接运行
python main.py
```

**4. 验证运行**

启动后应看到类似输出：
```
2026-04-27 10:00:00 [INFO] src.services.worker: SmartWater Worker starting...
2026-04-27 10:00:05 [INFO] src.services.worker: Processing task: SWA1B2C3...
2026-04-27 10:00:15 [INFO] src.services.result_writer: Result written for task SWA1B2C3..., status=COMPLETED
```

---

## 三、处理流程

```
Worker启动
  │
  ├─ 加载知识包 (knowledge_pack/water_permit_mvp.json)
  │
  └─ 轮询循环 (每 WORKER_POLL_INTERVAL 秒)
       │
       ├─ GET /api/task/pending  ← 拉取待处理任务
       │
       ├─ PUT /api/task/{id}/status  → 更新为 PROCESSING
       │
       ├─ 逐材料处理:
       │   ├─ GET /api/material/download  ← 下载文件
       │   └─ GLM OCR 抽取字段
       │
       ├─ 审核推理:
       │   └─ Qwen/DeepSeek → 生成 ReviewResult
       │
       ├─ 组装结果:
       │   ├─ applicantResult (过滤 applicantVisible=true)
       │   ├─ reviewerResult (完整结果)
       │   └─ knowledgePackVersion (来自知识包 version)
       │
       └─ PUT /api/task/{id}/result  → 回写 COMPLETED/PARTIAL_SUCCESS/FAILED
```

## 四、知识包契约

Worker 启动时加载 `knowledge_pack/water_permit_mvp.json`，并把其中的 `reviewBasis[]` 和 `promptSnippets[]` 归一化为审核推理 adapter 使用的 `knowledgeFragments`。模型输出中的 `basisRefs` 只能引用本次传给 adapter 的 fragment ID，例如 `BASIS_MATERIAL_INITIAL_LIST` 或 `PROMPT_BASIS_LIMIT`，不能编造法规名称、条款号或来源 ID。

Worker 回写结果时必须携带 `knowledgePackVersion`，Java 后端将该值保存到 `review_task.knowledge_pack_version`，用于后续追溯本次审核使用的知识包版本。
