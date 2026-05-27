# CP3 集成稳定性验收记录

> 对应任务：`v1-cp3-integration-stability-tests`  
> 记录日期：`2026-05-26`

---

## 1. 验收目标与边界

本记录覆盖 CP3-D 要求的三类验收点：

- 提交材料后可进入 Java `SUBMITTED` 队列，由 Python Worker 轮询触发 AI 审查，并回写结构化结果。
- 相同样例重复运行时，关键结构化字段稳定：`status`、`issue.code`、`severity`、`materialType`、`fieldKey`。
- 回调失败与查询兜底场景可解释：任务状态可落到 `FAILED`，并保留可查询失败原因。

说明：本次采用可重复执行的自动化测试作为主要证据，不宣称真实 OCR/LLM/对象存储联机 E2E 结果。Java 主动调用 Python FastAPI 的直接调度尚未接入，当前自动化验收按既有 Worker 轮询链路证明“提交触发 AI 处理”。

---

## 2. 本次执行环境

- 分支：`v1`
- 工作目录：`/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem`
- 依赖边界：
  - Java 测试使用 H2 与 test profile，不连接真实 MySQL/RustFS。
  - Python 测试通过 mock/stub 替代真实 Java/OCR/LLM/外网调用。
  - 前端测试为 adapter/view-model 回归与构建检查。

---

## 3. 验收命令与结果

| 类别 | 命令 | 结果 |
|---|---|---|
| Java CP3 相关回归 | `cd java-services/water-approval && ./mvnw -q -Dtest=ReviewTaskServiceImplTest,ReviewTaskControllerTest test` | 通过 |
| Python CP3 相关回归 | `cd python-services/smart-water-approval-review-system-py && uv run python -m pytest -q tests/test_fastapi_app.py tests/test_review_orchestrator.py tests/test_result_writer.py tests/test_cp3_acceptance.py` | 通过 |
| Frontend CP3 相关回归 | `cd frontend && npm run test` | 通过 |
| Frontend 构建门禁 | `cd frontend && npm run build` | 通过 |
| 文本差异检查 | `git diff --check` | 通过 |

---

## 4. 三类验收点映射

## 4.1 提交触发并回写 AI 结果

证据来源：

- Java 服务测试：
  - `ReviewTaskServiceImplTest#submittedMaterialsShouldBeClaimedByWorkerAndAcceptResultWriteback`
  - 验证申请人提交三类材料后生成 `SUBMITTED` 任务和材料槽位；Worker 领取接口把任务推进到 `PROCESSING`，返回三类材料引用；随后结果回写可被申请人和审批人员查询。
- Python FastAPI 测试：`tests/test_fastapi_app.py`
  - 验证 `POST /api/review/tasks` 受理后进入 `QUEUED`，后台任务被调度；该入口当前是 Python 侧任务 API 合同，不作为 Java 主动调度的已上线证据。
- Java 回写与结果查询测试：
  - `ReviewTaskServiceImplTest#repeatedWriteResultShouldUpdateExistingRowsWithoutDuplicatingResults`
  - `ReviewTaskServiceImplTest#getReviewerResultShouldExposeExtractedFieldSnapshotFromCallback`
  - 验证 Python 回写可更新 `REVIEWER/APPLICANT` 结果且不重复插入。
- 前端 adapter 测试：`frontend/src/api/task.spec.ts`
  - 验证 reviewer/applicant 投影与字段映射符合 CP3 DTO 合同。

## 4.2 结构化字段复跑稳定性

证据来源：`python-services/smart-water-approval-review-system-py/tests/test_cp3_acceptance.py`

- 用例：`test_repeated_runs_keep_structured_fields_stable`
- 方式：同一输入运行 3 次，审查说明文本允许变化，但断言以下结构化签名完全一致：
  - `status` 固定为 `PARTIAL_SUCCESS`
  - 每条 issue 的 `code/severity/materialType/fieldKey`
- 关键断言样例：
  - `("MISSING_MATERIAL", "WARNING", "ID_CARD", "")`
  - `("INCONSISTENT_IDENTITY", "BLOCKER", "APPLICATION_FORM", "applicant.name")`

## 4.3 回调失败与查询兜底

证据来源：`python-services/smart-water-approval-review-system-py/tests/test_cp3_acceptance.py`

- 用例：`test_callback_failure_records_failed_status_for_query_fallback`
- 方式：mock `write_results` 返回失败，触发 FastAPI 运行时失败分支。
- 验证点：
  - 任务状态更新尝试包含 `PROCESSING -> FAILED`。
  - `GET /api/review/tasks/{aiTaskId}` 可查询到：
    - `status == "FAILED"`
    - `errorMessage == "result callback failed after retries"`

---

## 5. 结论与后续

- 结论：CP3-D 要求的三类验收点已有可执行、可复验的自动化证据，且测试链路不依赖真实外部服务。
- 限制：本记录不包含真实 OCR/LLM/对象存储联机压测结果；Java 主动调用 Python FastAPI 的直接调度未纳入本次完成范围。若课程答辩要求真实联机演示，需要单独安排环境联调并追加截图/日志证据。

---

## 6. CP3.5-H OCR data URI 回归补充

对应任务：`v1-cp3-glm-ocr-data-uri-fix`

本轮新增自动化回归点：

- GLM OCR 请求的 `file` 字段必须带 MIME 前缀的 data URI：
  - `jpg` / `jpeg` -> `data:image/jpeg;base64,...`
  - `png` -> `data:image/png;base64,...`
  - `pdf` -> `data:application/pdf;base64,...`
- `md_results` 仍优先映射为 `ocr_markdown`，`layout_details` 仍可回退为 `ExtractedField[]`。
- 上游返回 HTTP `4xx/5xx` 时，`ocr_error` 和日志要保留业务错误摘要，但不能泄露 `Bearer` token 或 `data:...;base64,...` 原始内容。

本地验证命令：

- `cd python-services/smart-water-approval-review-system-py && uv run python -m unittest tests.test_ocr_adapter`
- `cd python-services/smart-water-approval-review-system-py && uv run python -m unittest discover -s tests -p test*.py`
- `cd python-services/smart-water-approval-review-system-py && uv run python -m compileall src main.py`

本节先记录自动化回归证据；真实联机证据见 6.1 和 6.2。

## 6.1 真实 GLM OCR 探测补录

记录日期：`2026-05-27`

在补充有效 `OCR_GLM_API_KEY` 与 `OCR_GLM_BASE_URL` 后，使用仓库内真实营业执照样例：

- 样例文件：`docs/参考资料/营业执照.jpg`
- 文件大小：`449597` 字节
- 文件头：`FFD8FFE1...`，为有效 JPEG

对同一文件执行两种请求：

| 请求方式 | `file` 字段 | 结果 |
|---|---|---|
| 旧实现 | 裸 base64 | HTTP `400` |
| 新实现 | `data:image/jpeg;base64,...` | HTTP `200` |

关键结果：

- 裸 base64 返回业务错误：`OCR仅支持PDF、JPG、PNG、JPEG格式...`
- data URI 返回 `md_results`、`layout_details`、`request_id` 等字段
- 通过当前 `GlmOcrAdapter` 直接调用，返回：
  - `field_count = 1`
  - `field_key = ocr_markdown`
  - `ocr_markdown` 预览中可识别：
    - `营业执照`
    - `统一社会信用代码`
    - `91441303MA531L6K37`

结论：

- 本任务“data URI 修复后真实 GLM OCR 从 400 变 200”的关键验收点已被真实联机探测证明。
- OCR 适配器本身已确认可用。

## 6.2 Java -> Worker -> GLM OCR -> 结果页联机补录

记录日期：`2026-05-27`

本次使用真实后端、真实对象存储、真实 Worker 与真实 GLM OCR 凭证执行完整链路：

- MySQL：本机 `3306`，使用隔离库 `smartwater_e2e` 按 `schema.sql` 初始化。
- 对象存储：本机 MinIO/S3 兼容服务 `http://localhost:9000`，bucket `smartwater`。
- Java：`http://localhost:8080/api`，带 `--water-approval.worker.token=smartwater-worker-token` 启动。
- Python Worker：从外部 `.env` 加载 `WORKER_TOKEN`、`OCR_GLM_API_KEY`、`OCR_GLM_BASE_URL` 与 LLM 配置。
- 样例材料：`docs/参考资料/营业执照.jpg`，作为 `businessLicense` 上传。

关键执行记录：

- 申请人登录 `POST /api/auth/login` 返回 `code=200`。
- 提交任务 `POST /api/task/submit` 返回：
  - `taskId = SW252E98F23D714BB6`
  - `sessionId = f41e523d58ea4122befc600a9eaa68d1`
  - `status = SUBMITTED`
  - `BUSINESS_LICENSE uploaded = true`
- Worker 轮询 `GET /api/task/pending` 返回 HTTP `200`，并开始处理 `SW252E98F23D714BB6`。
- Worker 状态回写 `PUT /api/task/SW252E98F23D714BB6/status` 返回 HTTP `200`。
- Worker 下载材料 `GET /api/material/download?key=...BUSINESS_LICENSE...jpg` 返回 HTTP `200`。
- Worker 调用 GLM `POST https://open.bigmodel.cn/api/paas/v4/layout_parsing` 返回 HTTP `200 OK`。
- Worker 回写结果 `PUT /api/task/SW252E98F23D714BB6/result` 返回 HTTP `200`，任务最终为 `PARTIAL_SUCCESS`。

结果查询：

- 申请人结果 `GET /api/task/SW252E98F23D714BB6/result/applicant?sessionId=...` 返回 `code=200`，`status=PARTIAL_SUCCESS`。
- 申请人结果 `missingMaterials` 为 `["APPLICATION_FORM", "ID_CARD"]`。
- 审核人结果 `GET /api/task/SW252E98F23D714BB6/result/reviewer` 返回 `code=200`。
- 审核人结果 `extractedFields[0].fieldKey = ocr_markdown`。
- `ocr_markdown` 中可识别：
  - `营业执照`
  - `统一社会信用代码`
  - `91441303MA531L6K37`

注意事项：

- 由于本次只上传营业执照，缺少申请书与身份证，业务结果为 `PARTIAL_SUCCESS` 是符合预期的。
- Review LLM 返回 JSON 外层结构不符合当前严格 schema，Worker 降级为规则结果并保留 `MODEL_UNCERTAIN`；这不影响本任务的 OCR data URI 验收结论。
- 本次结果页没有出现 `ocr_error: 400 Bad Request`，证明 Java 存储材料经 Worker 下载后已按 data URI 成功进入 GLM OCR。
