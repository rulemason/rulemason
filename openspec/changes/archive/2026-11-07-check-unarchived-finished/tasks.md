# Tasks

## 1. 巡检项

- [x] 1.1 在 `src/rulemason/check.py` 的「最近归档的检查点记录」里，加上 `openspec/changes/` 下带 `.openspec.yaml` 的直接子目录：`tasks.md` 至少有一个勾选框，且每个框内去掉空白后是 `x` 或 `X` 时才列出。没有 `verification.md` 写「<目录名>：没有 verification.md」，有则写「<目录名>：尚未归档」。没有 `tasks.md`、没有勾选框或仍有未完成的框时不列出。不改变退出码和下一步。验证：`uv run pytest tests/test_check.py::test_finished_change_without_report_is_listed tests/test_check.py::test_finished_change_with_report_is_unarchived tests/test_check.py::test_unfinished_change_stays_unlisted tests/test_check.py::test_change_without_checkboxes_stays_unlisted tests/test_check.py::test_archive_gap_and_unarchived_change_are_both_listed` 通过。

## 2. 收尾

- [x] 2.1 按检查点收尾。这次改了检查逻辑，做行为保持的精简，再独立审查、`uv run ruff check .`、`uv run pytest`。没有改判断规则或 `JEV_MODEL`，判断回归跳过并写明。验证：结果和 design 的估计行数对照写进 `verification.md`。

## Workflow follow-up

- 归档后发版。发版前先查 `git tag` 和 PyPI 上已有的版本。发布说明只写：巡检列出任务已勾完、尚未归档的 change。
- 接入项目升级本机的 `rulemason` 即可。本机被精确版本钉住时，用 `uv tool install rulemason@latest`，不用 `uv tool upgrade`。
