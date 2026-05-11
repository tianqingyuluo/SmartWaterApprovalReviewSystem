# Worker 失败处理与后端契约

## Java 后端统一响应约定

Python Worker 调用以下 JSON 接口时，必须同时校验 HTTP 状态码和响应体中的业务码：

- `GET /task/pending`
- `PUT /task/{taskId}/status`
- `PUT /task/{taskId}/result`

处理规则：

- 先执行 `raise_for_status()`，处理网络错误和非 2xx HTTP 错误。
- 再解析统一响应 `R<T>`，只有 `code == 200` 才算成功。
- 如果出现 HTTP 200 但 `code != 200`，例如 `403`、`404`、`409`，Worker 必须按失败处理，进入重试、失败回写或日志告警路径。

## Worker 鉴权约定

以下接口属于 Worker 专用接口，调用时必须携带 `X-Worker-Token`：

- `GET /task/pending`
- `PUT /task/{taskId}/status`
- `PUT /task/{taskId}/result`
- `GET /material/download?key=<storageKey>`

如果 token 缺失、未配置或不匹配，Java 后端会返回业务错误码 `403`。对于 JSON 接口，Worker 需要把该响应视为失败；对于下载接口，按 HTTP 结果和下载失败处理。

## 下载失败处理

`/material/download` 返回的是二进制文件流，不走 `R<T>` 包装。当前处理约定如下：

- 下载成功：按返回的文件字节继续 OCR 和字段抽取。
- 下载失败：记录错误日志，并为对应材料生成 `download_error` 抽取结果，避免整个任务无结果结束。

更细的 OCR 适配器行为见 [Worker 适配器文档](./adapters.md)。

## 重试与降级

- `update_status()` 和 `write_results()` 使用有界重试，失败后返回 `False`，由上层 Worker 决定是否继续降级或写入失败状态。
- `fetch_pending_tasks()` 调用失败时记录日志并返回空列表，避免轮询线程崩溃。
- 非法状态流转、任务不存在、token 错误等业务失败不能被视为成功完成的回写。

## 法规知识包与依据引用

Worker 默认加载 `knowledge_pack/water_permit_mvp.json`。该文件提供 MVP 材料清单、字段规则、审核依据、提示词片段和人工复核规则。

处理约定：

- Worker 读取知识包的 `version`，并在结果回写时携带 `knowledgePackVersion`。
- Java 后端将 `knowledgePackVersion` 保存到 `review_task.knowledge_pack_version`，用于追溯本次审核使用的知识版本。
- Worker 会把 `reviewBasis[]` 和 `promptSnippets[]` 归一化为审核推理 adapter 使用的 `knowledgeFragments`。
- 模型输出中的 `basisRefs` 只能引用本次输入的知识片段 ID，例如 `BASIS_MATERIAL_INITIAL_LIST`，不能编造法规名称、条款号或来源 ID。
- 如果模型返回未输入的 `basisRefs`，adapter 会将结果判为 `SCHEMA_MISMATCH`，避免把不可追溯依据写回后端。
