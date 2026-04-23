# 数据库规范

> MySQL + MyBatis-Plus 的使用规范。

---

## 概述

- 数据库：MySQL 8.x
- ORM：MyBatis-Plus
- 连接池：HikariCP（Spring Boot 默认）

---

## 表命名规范

| 规则 | 示例 |
|------|------|
| 全小写，下划线分隔 | `approval_record` |
| 业务前缀分组 | `sys_user`、`approval_record`、`review_result` |
| 关联表用双方名拼接 | `user_role` |
| 禁止使用 MySQL 保留字 | 避免 `order`、`group` 等 |

## 字段规范

| 规则 | 说明 |
|------|------|
| 全小写蛇形命名 | `created_at`、`file_name` |
| 主键统一用 `id`，类型 `BIGINT` | MyBatis-Plus 雪花算法生成 |
| 每张表必须有 `created_at`、`updated_at` | `DATETIME` 类型 |
| 逻辑删除字段 `deleted` | `TINYINT(1)`，0=未删除，1=已删除 |
| 布尔字段用 `is_` 前缀 | `is_enabled` |

---

## MyBatis-Plus 使用规范

### Entity 示例

```java
@Data
@TableName("approval_record")
public class ApprovalRecord {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String title;
    private Integer status;

    @TableLogic
    private Integer deleted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
```

### Mapper 示例

```java
@Mapper
public interface ApprovalRecordMapper extends BaseMapper<ApprovalRecord> {
    // 简单 CRUD 直接继承 BaseMapper，无需手写
    // 复杂查询写在 XML 中
}
```

### Service 示例

```java
public interface ApprovalService extends IService<ApprovalRecord> {
    void submitApproval(ApprovalSubmitDTO dto);
}

@Service
public class ApprovalServiceImpl extends ServiceImpl<ApprovalRecordMapper, ApprovalRecord>
        implements ApprovalService {
    @Override
    public void submitApproval(ApprovalSubmitDTO dto) {
        // 业务逻辑
    }
}
```

---

## 查询规范

| 场景 | 方式 |
|------|------|
| 简单单表 CRUD | `BaseMapper` / `IService` 内置方法 |
| 条件查询 | `LambdaQueryWrapper` |
| 多表联查 | XML 映射文件 |
| 分页查询 | `Page<T>` + MyBatis-Plus 分页插件 |

### LambdaQueryWrapper 示例

```java
List<ApprovalRecord> list = lambdaQuery()
    .eq(ApprovalRecord::getStatus, 1)
    .like(StringUtils.isNotBlank(keyword), ApprovalRecord::getTitle, keyword)
    .orderByDesc(ApprovalRecord::getCreatedAt)
    .list();
```

---

## 禁止事项

- **禁止**在 Controller 层直接操作 Mapper
- **禁止**使用字符串拼接 SQL，防止注入
- **禁止**使用 `select *`，XML 中必须明确字段列表
- **禁止**在循环中执行数据库查询（N+1 问题）
