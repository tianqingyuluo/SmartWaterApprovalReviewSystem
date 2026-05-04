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
      "task_id": "SWA1B2C3D4E5F6G7H",
      "status": "SUBMITTED",
      "materials": [
        {
          "material_type": "APPLICATION_FORM",
          "original_file_name": "test.pdf",
          "storage_key": "SWA1B2/APPLICATION_FORM/uuid.pdf",
          "file_extension": "pdf",
          "uploaded": true
        },
        {
          "material_type": "BUSINESS_LICENSE",
          "original_file_name": "license.jpg",
          "storage_key": "SWA1B2/BUSINESS_LICENSE/uuid.jpg",
          "file_extension": "jpg",
          "uploaded": true
        },
        {
          "material_type": "ID_CARD",
          "original_file_name": null,
          "storage_key": null,
          "file_extension": null,
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
  "result_summary": "申请材料基本完整，发现一个警告",
  "applicant_result": {
    "summary": "材料审核完成",
    "issues": [
      { "code": "MISSING_MATERIAL", "severity": "WARNING", "message": "缺少身份证" }
    ],
    "material_completeness": { "received": ["APPLICATION_FORM"], "missing": ["ID_CARD", "BUSINESS_LICENSE"], "unrecognized": [] },
    "manual_review_notice": "AI审核结果为辅助建议"
  },
  "reviewer_result": {
    "summary": "材料审核完成",
    "issues": [
      {
        "code": "MISSING_MATERIAL",
        "severity": "WARNING",
        "message": "缺少身份证材料",
        "material_type": "ID_CARD",
        "field_key": null,
        "basis_refs": ["REG-001"],
        "applicant_visible": true
      }
    ],
    "risk_hints": [
      {
        "risk_level": "MEDIUM",
        "description": "材料不完整",
        "basis_refs": ["REG-001"],
        "requires_manual_review": true
      }
    ],
    "draft_opinion": "建议补充身份证扫描件",
    "material_completeness": { "received": ["APPLICATION_FORM"], "missing": ["ID_CARD", "BUSINESS_LICENSE"], "unrecognized": [] },
    "basis_refs": ["REG-001"],
    "manual_review_notice": "AI审核结果为辅助建议，不构成最终审批意见。",
    "model_metadata": {
      "provider": "dashscope",
      "model": "qwen-max",
      "request_id": "req-xxx",
      "finish_reason": "stop",
      "token_usage": { "prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700 }
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
  ├─ 加载知识包 (knowledge_pack/*.json)
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
       │   ├─ applicantResult (过滤 applicant_visible=true)
       │   └─ reviewerResult (完整结果)
       │
       └─ PUT /api/task/{id}/result  → 回写 COMPLETED/PARTIAL_SUCCESS/FAILED
```

---

## 四、注意：Java 后端缺少的接口

Worker 依赖以下接口，当前 Java 后端尚未实现，**需要补充**：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/task/pending` | GET | 返回待处理任务列表 |
| `/api/task/{id}/result` | PUT | 接收 Worker 回写的审核结果 |
| `/api/material/download?key=` | GET | 根据 storage_key 下载原始文件 |
| `/api/task/{id}/status` | PUT | 更新任务状态（Worker调用） |

需要我帮你把这些接口补到 Java 后端里吗？
