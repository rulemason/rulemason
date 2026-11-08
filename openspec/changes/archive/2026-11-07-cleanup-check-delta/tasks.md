# Tasks

## 1. 汇报格式

- [x] 1.1 在 `skills/rulemason/SKILL.md` 第 1 节写明：存量清理可以继续时不贴识别表，不列「齐全」和「一致」；这次对话第一次清理写一行 `next.code`，列出不是「一致」的项及其子行、不是「齐全」的层，汇报第一行不是「日常巡检：一切一致」时带上该行；同一对话里再次清理，这些行没变就写「巡检与这次清理开始时相同」，有变只列变了的行；不把上次巡检写入文件；`next.code` 要停下时仍贴全文。第 7 节入口指向这段，不把细则写进第 7 节。第 8 节写明清理收尾不以报告全文开头，展示与第 1 节相同。普通运行仍贴全文。验证：`tests/test_templates.py` 断言第 1 节含「巡检与这次清理开始时相同」「不把上次巡检写入文件」，第 7 节行数仍不超过 70，第 8 节含收尾不以全文开头；`uv run pytest tests/test_templates.py::test_skill_legacy_cleanup_section tests/test_templates.py::test_skill_reads_check_json_and_lists_every_code` 通过。

## 2. 收尾与跨项目验证

- [x] 2.1 按检查点收尾。skill 是文档，测试只加断言，跳过会改断言含义的精简，并在汇报里写明。然后独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果和 design 的估计行数对照写进 `verification.md`。
- [x] 2.2 在已接入的项目里运行开发版 `rulemason update --dry-run`，不提交也不推送。验证：计划列出项目所选工具对应的 skill 副本和 `.rulemason.yaml`，不列出 `rules/` 下的文件；结果记进 `verification.md`。

## Workflow follow-up

- 归档后发版。发版前先查 `git tag` 和 PyPI 上已有的版本。发布说明只写：连续清理模块时不再重复贴整份巡检。
- 接入项目升级本机后再 `rulemason update`。本机被精确版本钉住时，用 `uv tool install rulemason@latest`。
