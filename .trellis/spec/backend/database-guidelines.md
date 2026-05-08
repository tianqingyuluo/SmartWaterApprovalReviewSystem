# 数据库规范

> SmartWater MVP 当前 MySQL/H2/MyBatis-Plus 的真实持久化约定。

---

## 当前数据库边界

- 生产/本地运行数据库：MySQL
- 测试数据库：H2（test profile）
- ORM：MyBatis-Plus
- 分页插件：`PaginationInnerInterceptor(DbType.MYSQL)`

当前权威建表脚本：

- [schema.sql](/home/tianqingyuluo/code/水利开发/SmartWaterApprovalReviewSystem/java-services/water-approval/src/main/resources/db/schema.sql:1)

初始化入口：

- `src/main/resources/db/init.sql`
- `src/main/resources/db/init-db.sh`
- `src/main/resources/db/init-db.bat`

---

## 当前表模型

MVP 当前只有三张核心表：

| 表 | 实体 | 用途 |
|---|---|---|
| `review_task` | `ReviewTask` | 任务主表，保存 `taskId/sessionId/status/knowledgePackVersion` |
| `material_slot` | `MaterialSlot` | 固定三槽位材料上传记录 |
| `review_result` | `ReviewResult` | `APPLICANT` / `REVIEWER` 两类结果 JSON |

### 实体约定

- 主键 `id`：`BIGINT` + MyBatis-Plus `ASSIGN_ID`
- 逻辑删除字段：`deleted`
- 时间字段统一用 `LocalDateTime`
- `taskId`、`sessionId` 是外部 contract 主键，不向前端暴露数据库 `id`

---

## 查询与写入规则

- 简单查询使用 `BaseMapper` + `LambdaQueryWrapper`
- 当前项目没有 mapper XML；未出现复杂联表查询前，不引入 XML
- controller 不直接访问 mapper
- 业务写入统一在 `ReviewTaskServiceImpl` 中完成

### 当前真实查询模式

```java
resultMapper.selectOne(
    new LambdaQueryWrapper<ReviewResult>()
        .eq(ReviewResult::getTaskId, taskId)
        .eq(ReviewResult::getResultType, "REVIEWER")
);
```

### 当前真实约束

- `review_task.task_id`、`review_task.session_id` 唯一
- `material_slot (task_id, material_type)` 唯一，保证每类材料只有一个槽位
- `review_result (task_id, result_type)` 唯一，保证申请人/审批人员结果各一份

---

## Scenario: Schema And Entity Synchronization

### 1. Scope / Trigger

- Trigger: 新增实体字段、schema 变更、知识包版本写入、材料类型扩展、状态字段调整时。

### 2. Signatures

- 权威 schema：`src/main/resources/db/schema.sql`
- 对应实体：
  - `ReviewTask`
  - `MaterialSlot`
  - `ReviewResult`

### 3. Contracts

| Layer | Contract |
|---|---|
| schema | 列名使用 snake_case，字段约束先体现在 schema.sql |
| entity | 字段名使用 camelCase，与 schema 通过驼峰映射对应 |
| service | 只通过实体/mapper 读写，不拼原始 SQL |
| test | H2 schema 与主 schema 保持必要同步，确保关键字段不会“只在 MySQL 存在” |

### 4. Validation & Error Matrix

| Condition | Expected handling |
|---|---|
| 新增实体字段但未更新 `schema.sql` | 视为未完成，必须补齐 schema 和验证。 |
| 新增 schema 字段但 service/test 不断言 | 视为 contract 不完整，至少补一个 focused test。 |
| 为简单单表查询引入 XML | 默认不接受，除非出现无法用 wrapper 表达的复杂查询。 |
| 未来扩展材料类型时直接把固定槽位逻辑删掉 | 不接受；MVP contract 仍以固定三槽位为前提。 |

### 5. Good/Base/Bad Cases

- Good: `knowledge_pack_version` 增加后，`ReviewTask`、`schema.sql`、service 测试同步更新。
- Base: 继续把 reviewer/applicant 结果 JSON 保存在 `review_result.content` 中。
- Bad: 只改 entity，不改建表脚本或 H2 测试 schema。

### 6. Tests Required

- schema/entity 相关变更：至少一个 service 或 controller 测试覆盖新字段读写。
- 唯一约束相关逻辑：要么有显式测试，要么在 PR 说明里记录人工验证命令。
- 测试 profile 必须继续脱离真实 MySQL。

### 7. Wrong vs Correct

#### Wrong

```java
private String knowledgePackVersion;
```

只改实体，不改 `schema.sql` 和测试。

#### Correct

- `ReviewTask` 增加字段
- `schema.sql` 增加列
- `writeResultShouldPersistKnowledgePackVersion` 断言字段已落库

---

## 禁止事项

- 不要把数据库 `id` 当作外部 API 标识。
- 不要在循环里逐条查 `material_slot` 或 `review_result` 造成隐式 N+1。
- 不要把 `schema.sql` 和测试 schema 漂移成两套不同 contract。
