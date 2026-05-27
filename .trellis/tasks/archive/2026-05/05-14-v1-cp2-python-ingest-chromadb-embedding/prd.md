# CP2-B Python ingest、ChromaDB、Embedding

## Scope
实现课程资料 ingest 主线，落地 ChromaDB 持久化与外部 Embedding。
在不改变 CP2-B 主体范围的前提下，补齐可答辩的 Python 收尾演示证据。

## Deliverables
- 可重复执行的 ingest 命令/API
- CHROMA_PERSIST_DIR 持久化与重建策略
- 文档结构优先切分与统计输出
- CP2 收尾演示证据：至少包含 ingest 统计日志、检索样例输出、关键步骤截图或等价记录

## Dependencies
- 无

## Acceptance Criteria
- 重复运行 ingest 可控且可重建
- 输出文档数/chunk 数/向量条目数
- 能检索课程资料关键依据片段
- 可按文档复现一次“从重建到检索”的演示链路并保留证据记录

## Wave Gate Notes
- Checkpoint: `CP2`
- Lane: `python`
- Wave: `1`
- Gate policy: "Do not start locked tasks until dependencies are completed and parent task approves next wave."
- Unlock criteria: Wave 1 baseline task for CP2 knowledge base.
