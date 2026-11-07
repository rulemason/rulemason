# Tasks

## 1. skill 正文

- [x] 1.1 `skills/rulemason/SKILL.md` 第 1 节加一句：用户要做存量清理时，`next.code` 只作第 7 节的入口闸门。第 7 节写明闸门（`init`、`fix_manifest`、`upgrade_machine`、`update` 停下；`fill_project_info`、`manual_lint`、`fix_gitignore`、`none` 继续）、不带模块名只诊断不改文件、带模块名先列计划等确认。原有六步标题和既有句子保留。验证：`tests/test_templates.py` 把第 7 节行数上限从 30 改为 70，并断言上述闸门用词与「不改任何文件」「用户确认后再」；`uv run pytest tests/test_templates.py` 通过。
- [x] 1.2 第 7 节补上三层诊断、查重回退、并行上限和进度约定：硬指标读「接入前遗留」与复杂度；临时参数统计 `ARG`、`ERA`、`BLE`、`S110`、`T201`，不改 lint 配置；有 Node 用钉死版本的 `npx --yes jscpd@<版本>`，否则对 Python 用钉死版本的 `uvx pylint@<版本>`，失败则空出该列；每模块抽 2 到 3 个文件给高/中/低；诊断最多 5 个只读代理，修模块最多 3 个，没有子代理就串行；修模块前通读，用户选择落地哪些；不把诊断写入 `.rulemason/`；收尾说明提交信息写成 `refactor(cleanup): <模块>`，skill 仍不提交。版本号在实现时查当时的稳定版再写死。验证：同一测试断言这些用词都在第 7 节，行数仍不超过 70，`uv run pytest tests/test_templates.py` 通过。

## 2. 收尾与跨项目验证

- [x] 2.1 按检查点做收尾：skill 是文档；测试只加断言时，手工看有没有重复可抽的断言，不跑会改变断言含义的精简。然后做独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果和 design 的估计行数对照写进 `verification.md`。
- [x] 2.2 在已接入的项目里运行开发版 `rulemason update --dry-run`，不提交也不推送。验证：计划列出项目所选工具对应的 skill 副本（`.claude/skills/rulemason/SKILL.md`、`.agents/skills/rulemason/SKILL.md` 中实际会更新的那几份）和 `.rulemason.yaml`，不列出 `rules/` 下的文件；结果记进 `verification.md`。

## Workflow follow-up

- 发版前先查 `git tag` 和 PyPI 上已有的版本，再 bump。发布说明只写存量清理的新用法。
- 接入项目运行 `uv tool upgrade rulemason`、`rulemason update`，按项目惯例提交。
