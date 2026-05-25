# CP2 测试与截图归档记录

> 对应任务：`v1-cp2-docs-tests-demo`  
> 记录日期：`2026-05-20`
> 最近复验：`2026-05-25`

---

## 1. 本次验证环境

- 仓库分支：`v1`
- 工作目录：`/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem`
- 验证目标：
  - CP2 文档命令可执行
  - MCP 工具主链路可演示
  - 常见异常可复现并可解释

---

## 2. 主链路验证记录

| 类别 | 命令 | 结果 |
|---|---|---|
| Java CP2 相关测试 | `cd java-services/water-approval && ./mvnw -q -Dtest=AiOpsControllerTest,AiOpsServiceTest,AiServicePropertiesTest test` | 通过（`RC=0`） |
| Python CP2 相关测试 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m pytest -q tests/test_mcp_demo.py tests/test_mcp_server_registration.py tests/test_mcp_tools.py tests/test_cp2_evidence.py tests/test_ingest_pipeline.py tests/test_chroma_store.py tests/test_document_parser.py tests/test_embedding_client.py tests/test_text_splitter.py` | 通过（`44 passed`） |
| Python 语法检查 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall src main.py knowledge_pack` | 通过 |
| ingest CLI 参数检查 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.ingest.cli --help` | 通过（参数包含 `--source-dir/--rebuild`） |
| Embedding 客户端契约 | `src.ingest.embedding_client.EmbeddingClient` 使用 OpenAI SDK `OpenAI(base_url=..., api_key=...)` 与 `embeddings.create(...)` | 支持 OpenAI-compatible embeddings 端点；当前示例配置为 `EMBEDDING_BASE_URL=https://router.tumuer.me/v1`、`EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B`，并明确 `base_url` 不应填写到 `/v1/embeddings` |
| 真实 Embedding 空库重建 | `CHROMA_PERSIST_DIR=/tmp/smartwater-cp2-chroma-verify-fixed uv run python -m src.ingest.cli --source-dir /tmp/smartwater-cp2-source-verify --chunk-size 512 --chunk-overlap 64 --rebuild` | 通过：`7` 个文档、`375` 个文本块、`665` 个 chunk、`665` 个向量；Embedding API 返回 `200 OK` |
| MCP 工具注册 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --list-tools` | 通过（包含 `knowledge_search`、`check_completeness`） |
| MCP 样例调用 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --run-samples --query "营业执照" --top-k 3 --materials-json '["APPLICATION_FORM","BUSINESS_LICENSE"]'` | 通过（返回 `knowledge_search` 结果和 `missing=["ID_CARD"]`） |
| CP2 证据脚本真实检索 | `KNOWLEDGE_SOURCE_DIR=/tmp/smartwater-cp2-source-verify CHROMA_PERSIST_DIR=/tmp/smartwater-cp2-chroma-verify-fixed uv run python -m src.cp2_evidence --no-rebuild` | 通过：向量总数 `665`，可检索“取水许可”“营业执照”“填报说明”“行业分类”，并演示两个 MCP 工具 |
| CP2 证据脚本参数检查 | `cd python-services/smart-water-approval-review-system-py && UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.cp2_evidence --help` | 通过（包含 `--no-rebuild`） |
| 前端单测 | `cd frontend && npm run test` | 通过（`2 files / 8 tests`） |
| 前端构建 | `cd frontend && npm run build` | 通过 |

---

## 3. 常见异常验证记录

| 场景 | 命令 | 预期行为 | 实际结果 |
|---|---|---|---|
| ingest 源目录不存在 | `uv run python -m src.ingest.cli --source-dir /tmp/smartwater-cp2-not-exist --chunk-size 512 --chunk-overlap 64` | 退出码非 0，并提示 `Source directory not found` | 符合预期（`RC=1`） |
| CP2 证据脚本缺配置 | `EMBEDDING_API_KEY= KNOWLEDGE_SOURCE_DIR= uv run python -m src.cp2_evidence` | 退出码非 0，并提示缺少必要配置 | 符合预期（`RC=1`，提示 `KNOWLEDGE_SOURCE_DIR, EMBEDDING_API_KEY`） |
| MCP 参数 JSON 非法 | `uv run python -m src.mcp_server.demo --run-samples --materials-json '{bad-json}'` | 参数解析失败并退出 | 符合预期（`JSONDecodeError`，`RC=1`） |

---

## 4. 截图清单（待补图）

当前执行环境无法提供浏览器与终端截图导出，本次采用截图清单占位。  
建议截图目录：`docs/readable/assets/cp2/`

| 编号 | 建议文件名 | 截图内容 | 当前状态 |
|---|---|---|---|
| S1 | `cp2-java-ai-health.png` | `GET /api/ai/health` 响应（含 `reachable`、`mcpTransport`） | 待补图 |
| S2 | `cp2-java-ai-ingest.png` | `POST /api/ai/ingest` 响应（含 `command`） | 待补图 |
| S3 | `cp2-ingest-stats.png` | `src.ingest.cli --rebuild` 统计输出 | 待补图 |
| S4 | `cp2-mcp-list-tools.png` | `--list-tools` 输出（两个工具） | 待补图 |
| S5 | `cp2-mcp-run-samples.png` | `--run-samples` 输出（检索结果与完整性检查） | 待补图 |
| S6 | `cp2-frontend-status-panel.png` | 前端 `/knowledge-mcp` 状态面板 | 待补图 |
| S7 | `cp2-frontend-knowledge-search-success.png` | `knowledge_search` 成功态 | 待补图 |
| S8 | `cp2-frontend-knowledge-search-error.png` | `knowledge_search` 失败态 | 待补图 |
| S9 | `cp2-frontend-completeness-success.png` | `check_completeness` 成功态 | 待补图 |
| S10 | `cp2-frontend-completeness-error.png` | `check_completeness` 失败态 | 待补图 |

---

## 5. 结论与风险

- 已具备可执行的 CP2 文档、演示命令和异常排查路径。
- 自动化验证覆盖了 Java CP2 入口、Python ingest/MCP 关键测试、前端构建与单测。
- 真实外部 Embedding 空库重建已通过，当前 Router OpenAI-compatible 端点与 `Qwen/Qwen3-Embedding-4B` 模型可用。
- 剩余风险：
  - 真实 ingest 仍依赖本地 `.env` 中有效 `EMBEDDING_API_KEY` 与外网可达性；密钥不进入 Git。
  - 前端演示台当前仍为演示数据模式，等待后续 MCP HTTP 代理接入后可切换真实后端链路。
