# Tasks

## 1. 第 7 节

- [x] 1.1 在 `skills/rulemason/SKILL.md` 第 7 节写上诊断队列：跳过已有 `refactor(cleanup): <模块>` 的模块；工作区干净的在前；再按软指标条数、行数、模块路径字典序。高、中、低只标在行旁。潜力为低的合成一行并写明这次不做。最后一行是第一个工作区干净且不是低的模块的 `/rulemason cleanup <模块>`；排在前面的模块有未提交文件时，最后一行改为要先提交的路径，不进入该模块。写上完成只认这种提交，工作区里的改动仍算未完成，skill 不提交。修完一个模块的收尾先要求提交，然后把该模块视为已完成，只按提交记录、未提交文件和软指标重算下一个、不再抽样，最后一行给出下一个命令或要先提交的路径，并且不改下一个模块的文件。原有六步和既有句子保留。验证：`tests/test_templates.py` 断言这些句子都在第 7 节，行数仍不超过 70；`uv run pytest tests/test_templates.py::test_skill_legacy_cleanup_section` 通过。

## 2. 收尾与跨项目验证

- [x] 2.1 按检查点收尾。skill 是文档，测试只加断言，跳过会改断言含义的精简，并在汇报里写明。然后独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果和 design 的估计行数对照写进 `verification.md`。
- [x] 2.2 在已接入的项目里运行开发版 `rulemason update --dry-run`，不提交也不推送。验证：计划列出项目所选工具对应的 skill 副本和 `.rulemason.yaml`，不列出 `rules/` 下的文件；结果记进 `verification.md`。

## Workflow follow-up

- 归档后发版。发版前先查 `git tag` 和 PyPI 上已有的版本。发布说明只写诊断队列和做完一个模块后的下一步。
- 接入项目升级本机后再 `rulemason update`。本机被精确版本钉住时，用 `uv tool install rulemason@latest`，不用 `uv tool upgrade`。
