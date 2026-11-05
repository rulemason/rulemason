# Tasks

## 1. 实现

- [x] 1.1 `shared.py` 新增 `legacy_console()` 与 `fail()`，`banner._can_draw_blocks` 改用前者；`judge/judge.py` 与 `key.py` 的报错标记改用 `fail()`；验证：`tests/test_shared.py` 覆盖 Windows 无终端变量、有 `WT_SESSION`、非 Windows 三种情况，`tests/test_key.py` 与 `tests/judge/test_engine.py` 各一条旧控制台下报错以「×」开头，`uv run pytest tests/test_shared.py tests/test_key.py tests/test_banner.py tests/judge` 通过
- [x] 1.2 `init.untouched_line` 数量为 0 时不写；验证：`tests/test_init.py` 新增工作区干净时 `init --plan` 没有「其余 0 个」、有 2 个改动时写「其余 2 个」，`uv run pytest tests/test_init.py tests/test_update.py` 通过
- [x] 1.3 `init.detect_commands` 对有 `pyproject.toml`、没有 `uv.lock` 的目录填 `uvx ruff check .`，测试填「待确认：填项目跑测试的命令」；验证：`tests/test_init.py` 新增根目录与子目录两种情况，有 `uv.lock` 的旧用例不变，`uv run pytest tests/test_init.py` 通过
- [x] 1.4 清单工具含 OpenCode 时，init 收尾下一步与 `check` 报告第一行后加 OpenCode 叫法一行；验证：`tests/test_check.py` 覆盖有与没有 OpenCode、`--json` 的 `next` 不变，`tests/test_init.py` 覆盖 init 收尾输出，`uv run pytest tests/test_check.py tests/test_init.py` 通过
- [x] 1.5 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
