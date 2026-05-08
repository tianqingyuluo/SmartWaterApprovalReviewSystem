# SmartWater API 集成冒烟测试

## 前置条件

这些脚本是**集成/手工验收脚本**，不是单元测试。运行前需要：

1. **后端服务已启动**（Java Spring Boot 服务在 `http://localhost:8080`）
2. **数据库已就绪**（MySQL + 对象存储 RustFS/MinIO）
3. **Worker Token 已配置**（通过环境变量 `WATER_APPROVAL_WORKER_TOKEN` 或后端 `application-secrets.yaml`）
4. **测试材料文件存在**（`test_data/` 目录下的测试文件）
5. **Python 3.12+** 已安装，依赖包已安装：
   ```bash
   pip install httpx
   ```

## 运行方式

```bash
# 执行所有冒烟测试
python3 run_all.py

# 单独执行某个测试
python3 test_01_submit.py
```

## 脚本说明

| 脚本 | 说明 | 调用的 API |
|------|------|-----------|
| `test_01_submit.py` | 提交材料（PDF/JPG/PNG） | `POST /api/task/submit` |
| `test_02_pending.py` | 拉取待处理任务 | `GET /api/task/pending` (需 Worker Token) |
| `test_03_get_status.py` | 查询任务状态 | `GET /api/task/{id}/status` |
| `test_04_update_status.py` | 更新任务状态 | `PUT /api/task/{id}/status` (需 Worker Token) |
| `test_05_write_result.py` | 回写审核结果 | `PUT /api/task/{id}/result` (需 Worker Token) |
| `test_06_applicant_result.py` | 查询申请人结果 | `GET /api/task/{id}/result/applicant` |
| `test_07_reviewer_result.py` | 查询审核人员结果 | `GET /api/task/{id}/result/reviewer` |
| `test_08_download.py` | 下载材料文件 | `GET /api/material/download` |

## 注意

- 这些脚本**不是自动化 CI 门禁**。它们需要完整运行环境。
- PR 的自动化质量门禁由 Java `./mvnw test` 提供。
- 断言失败时脚本会打印差异，**但不会以非零退出码退出**。这将在后续版本改进。
- 当前脚本多数是响应打印，缺少 pytest/unittest 风格的严格 assert。
