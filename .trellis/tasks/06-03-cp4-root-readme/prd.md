# CP4 根目录总 README

## Goal

补齐仓库根目录 `README.md`，让课程验收、答辩和新成员接手时能从仓库首页快速理解 SmartWater V1 的项目目标、模块结构、启动方式、部署入口、文档索引和 CP1-CP4 交付映射。

## What I already know

* 仓库当前没有根目录 `README.md`。
* 已有 `deploy/README.md` 说明 Docker Compose 部署。
* 已有 `docs/readable/README.md` 作为可读文档导航。
* CP4-D 明确要求总 README、Java API 说明、Python API/MCP 工具说明、Docker Compose / 部署说明、验收证据表和答辩演示脚本。
* 本任务只补根目录项目总 README，不扩展到完整 CP4-D 答辩整包。

## Requirements

* 新增根目录 `README.md`，作为项目首页。
* README 使用中文，允许保留命令、路径、接口和技术名词英文。
* README 覆盖：
  * 项目简介和课程检查点定位。
  * 系统模块结构。
  * 核心能力。
  * 快速启动与 Docker Compose 部署入口。
  * 关键账号、配置和安全边界说明。
  * 文档索引和 CP1-CP4 交付映射。
  * 当前限制和后续工作。
* 更新可读文档入口，说明根 README 与 `docs/readable/**` 的关系。
* 更新 2026-06 开发日志。

## Acceptance Criteria

* [ ] 根目录存在 `README.md`。
* [ ] README 不包含真实密钥、私有 token 或本地专用绝对路径作为必要步骤。
* [ ] README 中所有相对链接指向现有文件。
* [ ] 变更仅涉及文档和 Trellis 任务记录，不改业务代码。
* [ ] `git diff --check` 通过。

## Definition of Done

* 文档已更新。
* 开发日志已记录。
* 基础文档质量检查通过。

## Out of Scope

* 不实现新的 Java、Python 或前端能力。
* 不补完整 CP4-D 答辩脚本或验收证据表。
* 不运行完整 Docker Compose 联机部署。

## Technical Notes

* 参考 `deploy/README.md`、`docs/readable/README.md`、`docs/readable/operations/deployment.md` 和现有 CP4 任务清单。
