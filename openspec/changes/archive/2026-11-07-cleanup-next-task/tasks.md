# Tasks

## 1. 第 7 节

- [x] 1.1 在 `skills/rulemason/SKILL.md` 第 7 节写上：最后一行是 `/rulemason cleanup <模块>` 时，命令前用该模块已有的 1 到 2 个例子写一句这次要做的事，包含要动的位置、要做的事，以及哪一类软指标不算这次要清的内容。这句只给这一条命令点名的模块，不写入文件，也不代替进入后的计划。最后一行是要先提交的路径或这次没有要做的模块时，不写这句。收尾不重新抽样；同一次诊断已有下一模块的例子时，用那些例子在命令前写同样的一句；没有时只给命令或要先提交的路径，并写明具体改哪些等进入该模块后的计划。原有队列、六步和既有句子保留。验证：`tests/test_templates.py` 断言第 7 节含「这次要做的事」「不算这次要清的内容」「同一次诊断」，行数仍不超过 70；`uv run pytest tests/test_templates.py::test_skill_legacy_cleanup_section` 通过。

## 2. 收尾与跨项目验证

- [x] 2.1 按检查点收尾。skill 是文档，测试只加断言，跳过会改断言含义的精简，并在汇报里写明。然后独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果和 design 的估计行数对照写进 `verification.md`。
- [x] 2.2 在已接入的项目里运行开发版 `rulemason update --dry-run`，不提交也不推送。验证：计划列出项目所选工具对应的 skill 副本和 `.rulemason.yaml`，不列出 `rules/` 下的文件；结果记进 `verification.md`。

## Workflow follow-up

- 归档后发版。发版前先查 `git tag` 和 PyPI 上已有的版本。发布说明只写：清理命令前用已有例子写明这次要做的事。
- 接入项目升级本机后再 `rulemason update`。本机被精确版本钉住时，用 `uv tool install rulemason@latest`，不用 `uv tool upgrade`。
