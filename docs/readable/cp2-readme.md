# CP2 知识库与 MCP README

> 对应任务：`v1-cp2-docs-tests-demo`  
> 目标：沉淀 CP2 的知识库范围、重建步骤和演示入口，保证可从空 ChromaDB 复现主链路。

---

## 1. CP2 主线范围

CP2 主线聚焦“知识库 ingest + MCP 工具演示 + 前端演示台”，不扩展到 CP3/CP4 审批闭环。

### 1.1 知识库资料白名单（答辩主线）

| 资料 | 路径 | 用途 |
|---|---|---|
| 办理流程与材料说明 | `docs/参考资料/取水许可办理需资料及流程.docx` | 办理流程、材料清单依据 |
| 申请书填报说明 | `docs/参考资料/填报说明.docx` | 字段填报口径 |
| 国民经济分类 | `docs/参考资料/国民经济分类国标.pdf` | 行业分类依据 |
| 申请书模板 | `docs/参考资料/申请书.docx` | 申请字段结构 |
| 营业执照样例 | `docs/参考资料/营业执照.jpg` | 证照 OCR/校验样例 |
| 身份证样例 | `docs/参考资料/身份证.jpg` | 证照 OCR/校验样例 |
| 驾驶证样例 | `docs/参考资料/驾驶证.png` | 负向样例（非身份证） |

### 1.2 非主线资料（默认不纳入 CP2 验收）

- `取水许可证申领表（2022）.docx`
- `附件2验收申请.doc`
- `附件3验收报告.doc`

说明：`/api/ai/ingest` 默认给出的 `sourceDir` 是 `docs/参考资料`。若答辩要求严格按白名单演示，建议先准备独立目录再 ingest（见下文命令）。

---

## 2. 从空 ChromaDB 重建知识库

以下流程不删除仓库内已有数据，使用临时目录证明“空库重建”。

### 2.1 准备环境

```bash
cd python-services/smart-water-approval-review-system-py
cp .env.example .env
```

在 `.env` 至少设置：

- `EMBEDDING_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`

Embedding 客户端使用 OpenAI Python SDK 的 `embeddings.create` 接口，因此 CP2 主线支持
OpenAI-compatible embeddings 端点。`EMBEDDING_BASE_URL` 应填写兼容 API 的根路径，
不要写到完整 `/embeddings` 路径。

当前答辩默认示例使用 Router OpenAI-compatible embeddings：

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
EMBEDDING_BASE_URL=https://router.tumuer.me/v1
EMBEDDING_API_KEY=your-embedding-api-key
```

注意：`EMBEDDING_BASE_URL` 必须是 API 根路径，不是完整 embeddings 端点。

- 正确：`https://router.tumuer.me/v1`
- 错误：`https://router.tumuer.me/v1/embeddings`

也可以替换为其他兼容 OpenAI embeddings 协议的服务：

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_MODEL=<provider-embedding-model>
EMBEDDING_BASE_URL=<provider-openai-compatible-base-url>
EMBEDDING_API_KEY=<provider-api-key>
```

当前实现不直接适配非 OpenAI-compatible 的私有 Embedding API；这类服务需要新增客户端适配。

### 2.2 准备白名单资料目录（推荐）

```bash
mkdir -p /tmp/smartwater-cp2-source
cp ../../docs/参考资料/取水许可办理需资料及流程.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/填报说明.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/国民经济分类国标.pdf /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/申请书.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/营业执照.jpg /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/身份证.jpg /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/驾驶证.png /tmp/smartwater-cp2-source/
```

### 2.3 执行重建

```bash
cd python-services/smart-water-approval-review-system-py
UV_CACHE_DIR=/tmp/uv-cache uv sync
UV_CACHE_DIR=/tmp/uv-cache CHROMA_PERSIST_DIR=/tmp/smartwater-cp2-chroma \
  uv run python -m src.ingest.cli \
  --source-dir /tmp/smartwater-cp2-source \
  --chunk-size 512 \
  --chunk-overlap 64 \
  --rebuild
```

成功判据：

- 命令退出码为 `0`
- 输出中 `Chunks created` 和 `Vectors stored` 大于 `0`
- 无 `Errors:` 条目

---

## 3. MCP 工具演示入口

```bash
cd python-services/smart-water-approval-review-system-py
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --list-tools
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --run-samples
```

预期：

- 工具列表包含 `knowledge_search`、`check_completeness`
- `knowledge_search` 返回 `results`
- `check_completeness` 返回 `submitted/required/missing/complete`

可选自定义参数：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo \
  --run-samples \
  --query "营业执照" \
  --top-k 3 \
  --materials-json '["APPLICATION_FORM","BUSINESS_LICENSE"]'
```

---

## 4. Java 与前端演示入口

Java 侧（用于展示 CP2 配置和运维触发命令）：

```bash
curl http://localhost:8080/api/ai/health
curl -X POST http://localhost:8080/api/ai/ingest
```

前端演示台：

- 路由：`/knowledge-mcp`
- 页面标题：`AI 知识库与 MCP 演示台`
- 当前模式：演示数据（页面会标注“演示模式，非正式审批结论”）

---

## 5. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| ingest 报 `Source directory not found` | `--source-dir` 路径错误 | 检查路径或先创建白名单目录 |
| `cp2_evidence` 报缺少配置 | 未设置 `KNOWLEDGE_SOURCE_DIR` / `EMBEDDING_API_KEY` | 补齐 `.env` 后重试 |
| `materials-json` 解析失败 | JSON 不是合法格式 | 使用双引号 JSON，例如 `'["APPLICATION_FORM"]'` |
