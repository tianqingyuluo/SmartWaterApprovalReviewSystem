# Git 分工与提交证明

> 本文档整理 SmartWater 项目团队成员、Git 分工、关键提交记录和分支策略。
> 对应任务：`v1-cp1-docs-git-demo-evidence`

---

## 1. 团队成员与职责分工

| 成员 | 邮箱 | 主要职责 | 主要贡献领域 |
|------|------|----------|--------------|
| tianqingyuluo | 1185207374@qq.com | 项目负责人、架构设计、前后端联调 | Java 后端、前端重构、Trellis 工作流、文档规范 |
| 岳显维 | 15473273+yue-xianwei@user.noreply.gitee.com | 前端开发 | 前端双页 MVP、API 契约对齐、Tailwind 样式重构 |
| 6NewUser6 | 1642258843@qq.com | Python Worker 开发、后端测试 | Python OCR Worker、Java 后端接口、跨服务契约修复 |
| YMX | 3471830049@qq.com | 知识包与法规整理 | 法规知识包 MVP、审核依据梳理 |

---

## 2. 提交统计

```bash
# 总提交数（截至 2026-05-14）
git log --oneline --all | wc -l
# 输出：约 108 条提交

# 各成员提交分布
git shortlog -sne --all
#     60  tianqingyuluo <1185207374@qq.com>
#     36  6NewUser6 <1642258843@qq.com>
#      7  tianqingyuluo <85054746+tianqingyuluo@users.noreply.github.com>
#      4  岳显维 <15473273+yue-xianwei@user.noreply.gitee.com>
#      1  YMX <3471830049@qq.com>
```

---

## 3. 近期关键提交记录

### V1 阶段（当前分支 `v1`）

| 提交 | 日期 | 作者 | 说明 |
|------|------|------|------|
| `cf34743` | 2026-05-14 | tianqingyuluo | chore: 分配 V1 第一波任务 |
| `420e125` | 2026-05-14 | tianqingyuluo | chore: 拆分 V1 检查点任务树 |
| `d79dd8e` | 2026-05-14 | tianqingyuluo | docs: 添加 V1 设计基线 |

### MVP 阶段（分支 `mvp/smartwater`）

| 提交 | 日期 | 作者 | 说明 |
|------|------|------|------|
| `8801c8b` | 2026-05-13 | tianqingyuluo | feat: 重构前端 Tailwind 样式体系 |
| `3a20089` | 2026-05-13 | tianqingyuluo | feat: 重构审核流程前端界面 |
| `8f871da` | 2026-05-13 | tianqingyuluo | feat: 前端审核流程重构 + 后端申请列表 API |
| `3c95685` | 2026-05-11 | tianqingyuluo | fix(worker): switch OCR to glm-ocr layout parsing |
| `610f4fb` | 2026-05-11 | tianqingyuluo | chore(worker): tighten typing and add uv lockfile |
| `b2638fa` | 2026-05-08 | 岳显维 | fix: 对齐前端 API 契约与后端接口，修复 4 项合并前问题 |
| `3a60674` | 2026-05-04 | YMX | feat: 增加法规知识包 MVP |
| `d79adb6` | 2026-05-03 | 6NewUser6 | fix: test infrastructure, regression tests, and cross-service fixes |
| `ca1910b` | 2026-05-02 | 6NewUser6 | fix: 修复代码审查阻塞点（Worker鉴权、secrets导入、missingMaterials契约、IDE配置清理） |
| `31b8bc6` | 2026-04-27 | 6NewUser6 | feat: 实现Python OCR与智能审核Worker MVP |
| `2fc4e48` | 2026-04-27 | 6NewUser6 | feat: 实现后端提交与存储 MVP |
| `376a41d` | 2026-04-28 | 岳显维 | feat: 实现 SmartWater 前端双页演示 MVP |

---

## 4. 分支策略

### 当前分支

```
* v1                    # V1 开发分支（当前工作分支）
  mvp/smartwater        # MVP 稳定分支（已合并所有 MVP 功能）
  main                  # 主分支（保留历史）
  integrate/backend-worker-mvp  # 后端-Worker 集成分支（历史）
```

### 分支策略说明

1. **`main`**：项目主分支，保留历史基线。
2. **`mvp/smartwater`**：MVP 功能稳定分支，所有 MVP 阶段的功能 PR 合并至此。
3. **`v1`**：V1 阶段开发分支，基于 `mvp/smartwater` 切出，承载 CP1~CP4 检查点任务。
4. **任务分支**：V1 阶段采用 `task/xxx` 或 `feature/xxx` 短分支，完成后合并到 `v1`。

### 提交规范

- 使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范
- 主要类型：`feat`、`fix`、`chore`、`docs`、`spec`
- 示例：`feat: 前端审核流程重构 + 后端申请列表 API`

---

## 5. PR 历史

| PR | 日期 | 来源分支 | 目标分支 | 说明 |
|----|------|----------|----------|------|
| #5 | 2026-05-04 | `review/mvp-code-quality-fix` | `mvp/smartwater` | Worker 鉴权、响应契约、回归测试 |
| #6 | 2026-05-05 | `task/smartwater-regulation-knowledge-pack-mvp` | `mvp/smartwater` | 法规知识包 MVP |
| #7 | 2026-05-08 | `task/smartwater-frontend-dual-page-mvp` | `mvp/smartwater` | 前端双页 MVP |
| #8 | 2026-05-04 | `task/project-readable-docs-spec` | `mvp/smartwater` | 项目规范固化 |

---

## 6. 协作规范

- 所有代码变更通过 PR 合并，禁止直接推送到 `mvp/smartwater` 和 `v1`
- PR 必须通过质量门禁：Java `./mvnw test`、Python `uv run pytest`、前端 `npm run test && npm run build`
- 敏感配置（密码、API Key）不得提交到 Git，使用 `.env.example` 和 `application-secrets.yaml.example` 模板
- Trellis 任务状态在 `.trellis/tasks/` 中跟踪，完成后归档到 `archive/`

---

## 相关文档

- [CP1 证据映射总表](./cp1-evidence.md)
- [本地启动步骤](./operations/local-dev.md)
- [开发日志](./dev-log/2026-05.md)
