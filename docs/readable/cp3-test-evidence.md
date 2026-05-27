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

当前限制：

- 本机当前未配置 `OCR_GLM_API_KEY` 与 `OCR_GLM_BASE_URL`，因此本次补充的是自动化回归证据，不宣称真实 GLM OCR 联机成功。
- 若后续补真实营业执照样例证据，应追加记录：请求前后差异、GLM 返回 `200`、以及结果页不再出现 `ocr_error: 400 Bad Request`。
