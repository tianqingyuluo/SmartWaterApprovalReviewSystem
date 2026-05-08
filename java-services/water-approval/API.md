# SmartWater API 接口文档

> 基础地址：`http://localhost:8080/api`

---

## 1. 提交材料

**POST** `/task/submit`

提交申请材料，支持 0-3 个文件（申请书、营业执照、身份证）。

### 请求参数（multipart/form-data）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| applicationForm | File | 否 | 申请书（jpg/jpeg/png/pdf） |
| businessLicense | File | 否 | 营业执照（jpg/jpeg/png/pdf） |
| idCard | File | 否 | 身份证（jpg/jpeg/png/pdf） |

### curl 示例

```bash
# 提交全部材料
curl -X POST http://localhost:8080/api/task/submit \
  -F "applicationForm=@test.pdf" \
  -F "businessLicense=@license.jpg" \
  -F "idCard=@idcard.png"

# 只提交部分材料
curl -X POST http://localhost:8080/api/task/submit \
  -F "applicationForm=@test.pdf"

# 不提交材料（空提交）
curl -X POST http://localhost:8080/api/task/submit
```

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "sessionId": "a1b2c3d4e5f6789012345678abcdef01",
    "status": "SUBMITTED",
    "submittedAt": "2026-04-27T19:30:00",
    "materials": [
      {
        "materialType": "APPLICATION_FORM",
        "originalFileName": "test.pdf",
        "uploaded": true
      },
      {
        "materialType": "BUSINESS_LICENSE",
        "originalFileName": "license.jpg",
        "uploaded": true
      },
      {
        "materialType": "ID_CARD",
        "originalFileName": null,
        "uploaded": false
      }
    ]
  }
}
```

---

## 2. 查询任务状态

**GET** `/task/{taskId}/status`

查询指定任务的当前处理状态。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | String | 是 | 任务ID |

### curl 示例

```bash
curl http://localhost:8080/api/task/SWA1B2C3D4E5F6G7H/status
```

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "status": "SUBMITTED",
    "submittedAt": "2026-04-27T19:30:00",
    "updatedAt": "2026-04-27T19:30:00",
    "materials": [
      {
        "materialType": "APPLICATION_FORM",
        "originalFileName": "test.pdf",
        "uploaded": true
      },
      {
        "materialType": "BUSINESS_LICENSE",
        "originalFileName": "license.jpg",
        "uploaded": true
      },
      {
        "materialType": "ID_CARD",
        "originalFileName": null,
        "uploaded": false
      }
    ]
  }
}
```

### 状态说明

| 状态 | 说明 |
|------|------|
| SUBMITTED | 已提交 |
| QUEUED | 排队中 |
| PROCESSING | 处理中 |
| PARTIAL_SUCCESS | 部分成功 |
| COMPLETED | 已完成 |
| FAILED | 失败 |

---

## 3. 查询申请人结果

**GET** `/task/{taskId}/result/applicant`

查询申请人视图的结果（简化版，隐藏敏感信息）。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | String | 是 | 任务ID |

### curl 示例

```bash
curl http://localhost:8080/api/task/SWA1B2C3D4E5F6G7H/result/applicant
```

### 响应示例（处理中）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "status": "PROCESSING",
    "summary": "审核结果处理中，请稍后查询",
    "issues": [],
    "missingMaterials": []
  }
}
```

### 响应示例（已完成）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "status": "COMPLETED",
    "summary": "申请材料基本完整，建议补充身份证扫描件",
    "issues": [
      {
        "code": "MISSING_MATERIAL",
        "severity": "WARNING",
        "message": "缺少身份证材料"
      }
    ],
    "missingMaterials": ["ID_CARD"]
  }
}
```

---

## 4. 查询审批人员结果

**GET** `/task/{taskId}/result/reviewer`

查询审批人员视图的完整结果（包含详细信息）。

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | String | 是 | 任务ID |

### curl 示例

```bash
curl http://localhost:8080/api/task/SWA1B2C3D4E5F6G7H/result/reviewer
```

### 响应示例（处理中）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "status": "PROCESSING",
    "summary": "审核结果处理中，请稍后查询",
    "issues": [],
    "riskHints": [],
    "draftOpinion": "",
    "missingMaterials": [],
    "extractedFields": null,
    "modelMetadata": ""
  }
}
```

### 响应示例（已完成）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "taskId": "SWA1B2C3D4E5F6G7H",
    "status": "COMPLETED",
    "summary": "申请材料审核完成，发现1个问题",
    "issues": [
      {
        "code": "MISSING_MATERIAL",
        "severity": "WARNING",
        "message": "缺少身份证材料",
        "materialType": "ID_CARD",
        "fieldKey": null,
        "basisRefs": ["REG-2024-001"],
        "applicantVisible": true
      }
    ],
    "riskHints": [
      {
        "riskLevel": "MEDIUM",
        "description": "申请材料不完整，可能影响审批进度",
        "basisRefs": ["REG-2024-001"],
        "requiresManualReview": true
      }
    ],
    "draftOpinion": "建议补充身份证扫描件后重新提交",
    "missingMaterials": ["ID_CARD"],
    "extractedFields": {
      "companyName": "某某科技有限公司",
      "licenseNumber": "91350100M0001"
    },
    "modelMetadata": "{\"provider\":\"qwen\",\"model\":\"qwen-max\"}"
  }
}
```

---

## 通用响应格式

所有接口统一返回：

```json
{
  "code": 200,      // 200=成功，其他=错误码
  "message": "success",
  "data": { ... }   // 业务数据
}
```

### 错误响应示例

```json
{
  "code": 404,
  "message": "任务不存在",
  "data": null
}
```

```json
{
  "code": 400,
  "message": "不支持的文件格式: docx, 只允许: jpg, jpeg, png, pdf",
  "data": null
}
```

---

## 快速测试流程

```bash
# 1. 提交材料
curl -X POST http://localhost:8080/api/task/submit \
  -F "applicationForm=@test.pdf" \
  -F "businessLicense=@license.jpg"

# 2. 记录返回的 taskId，然后查询状态
curl http://localhost:8080/api/task/{taskId}/status

# 3. 查询申请人结果
curl http://localhost:8080/api/task/{taskId}/result/applicant

# 4. 查询审批人员结果
curl http://localhost:8080/api/task/{taskId}/result/reviewer
```

---

## 注意事项

1. 文件格式限制：jpg, jpeg, png, pdf
2. 每个材料类型最多上传一个文件
3. 缺失材料不会导致任务失败
4. 结果需要等待 Python Worker 处理后才能查询到
