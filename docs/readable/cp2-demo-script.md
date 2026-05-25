# CP2 答辩演示脚本

> 对应任务：`v1-cp2-docs-tests-demo`  
> 适用对象：课堂答辩、阶段预验收演示。  
> 建议时长：8-12 分钟。

---

## 1. 演示前准备（1 分钟）

确认服务与依赖：

- Java：`java-services/water-approval`
- Python：`python-services/smart-water-approval-review-system-py`
- 前端：`frontend`

建议先执行：

```bash
cd python-services/smart-water-approval-review-system-py
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

确认 `.env` 中已配置 OpenAI-compatible Embedding 端点。当前答辩默认配置如下，
也可以替换为其他兼容 OpenAI embeddings 协议的服务：

```env
EMBEDDING_PROVIDER=openai-compatible
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
EMBEDDING_BASE_URL=https://router.tumuer.me/v1
EMBEDDING_API_KEY=your-embedding-api-key
```

`EMBEDDING_BASE_URL` 填 API 根路径，当前客户端会通过 OpenAI SDK 调用
`embeddings.create`，不要把 `/embeddings` 追加到配置值里（例如不要写
`https://router.tumuer.me/v1/embeddings`）。

---

## 2. 展示 Java 侧 CP2 配置入口（1 分钟）

命令：

```bash
curl http://localhost:8080/api/ai/health
curl -X POST http://localhost:8080/api/ai/ingest
```

讲解要点：

- `/api/ai/health` 展示 Java 侧 `water-approval.ai-service.*` 配置和 Python 可达性。
- `/api/ai/ingest` 返回运维触发命令，不在 Java 进程内直接执行 Python ingest。

---

## 3. 从空 ChromaDB 重建（3 分钟）

### 3.1 准备白名单源目录

```bash
cd python-services/smart-water-approval-review-system-py
mkdir -p /tmp/smartwater-cp2-source
cp ../../docs/参考资料/取水许可办理需资料及流程.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/填报说明.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/国民经济分类国标.pdf /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/申请书.docx /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/营业执照.jpg /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/身份证.jpg /tmp/smartwater-cp2-source/
cp ../../docs/参考资料/驾驶证.png /tmp/smartwater-cp2-source/
```

### 3.2 执行 ingest 重建

```bash
cd python-services/smart-water-approval-review-system-py
UV_CACHE_DIR=/tmp/uv-cache CHROMA_PERSIST_DIR=/tmp/smartwater-cp2-chroma \
  uv run python -m src.ingest.cli \
  --source-dir /tmp/smartwater-cp2-source \
  --chunk-size 512 \
  --chunk-overlap 64 \
  --rebuild
```

讲解要点：

- 重点查看 `Documents found / Chunks created / Vectors stored`。
- 若 `Errors > 0`，按输出定位失败文件或配置问题。

---

## 4. MCP 工具演示（2 分钟）

命令：

```bash
cd python-services/smart-water-approval-review-system-py
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --list-tools
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo \
  --run-samples \
  --query "营业执照" \
  --top-k 3 \
  --materials-json '["APPLICATION_FORM","BUSINESS_LICENSE"]'
```

讲解要点：

- `knowledge_search` 展示依据片段与 `basisRefs`。
- `check_completeness` 展示缺失材料列表，例如 `ID_CARD` 缺失时的提示。

---

## 5. 前端演示台（2-3 分钟）

启动前端：

```bash
cd frontend
npm run dev
```

打开页面：

- `http://localhost:5173/knowledge-mcp`

演示顺序：

1. 查看状态面板（知识库状态、MCP 状态、最近调用工具）。
2. `knowledge_search` 成功检索。
3. 点击“演示空结果”。
4. 点击“演示失败”，观察错误提示与重试按钮。
5. `check_completeness` 勾选/取消材料，观察 `complete` 与 `missing` 变化。

讲解要点：

- 页面明确标注“演示模式，非正式审批结论”。
- 当前前端使用演示数据结构，字段对齐 Python MCP 工具返回格式。

---

## 6. 常见异常快速演示（可选 1 分钟）

1) 错误源目录：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.ingest.cli --source-dir /tmp/not-found --rebuild
```

预期：退出码 `1`，包含 `Source directory not found`。

2) 错误 JSON：

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m src.mcp_server.demo --run-samples --materials-json '{bad-json}'
```

预期：`JSONDecodeError`。
