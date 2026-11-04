# Tasks

## 1. 实现

- [x] 1.1 `init.set_block` 处理没有标题的块（即 `CLAUDE.md` 的 claude 块）时：原文没有该块、正文首行 `@AGENTS.md` 在全文只出现一次且顶格独占一行（不在代码块里）时，用新块替换该行，不再追加到文末，也不报重复导入；其余情况保持现状，重复导入提示改为按 `@AGENTS.md` 与 `@./AGENTS.md` 判断；验证：`tests/test_init.py` 改写 `test_existing_agents_import_in_claude_md_is_reported` 为「单独一行被块替换」，新增「`@./AGENTS.md` 仍报告」与「`remove --yes` 后再 `init --yes`，全文只有一处 `@AGENTS.md`、项目说明逐字不变、notes 无重复导入」两个用例，`tests/test_update.py` 新增「`update --yes` 用块替换单独一行」用例，`uv run pytest tests/test_init.py tests/test_remove.py tests/test_update.py` 通过
- [x] 1.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`
