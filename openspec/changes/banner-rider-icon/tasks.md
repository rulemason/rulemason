# Tasks

## 1. 图标数据与渲染（`src/rulemason/banner.py`）

- [x] 1.1 把 design.md 附录的 26×22 网格写成 `ICON`，加 `ICON_COLORS`（`t`/`b`/`d`/`g` 的 256 色码；`w` 用默认前景色，`h` 与 `.` 不画）；验证：`uv run python -c "from rulemason import banner; assert len(banner.ICON) == 22 and {len(r) for r in banner.ICON} == {26}"` 不报错。
- [x] 1.2 实现 `_icon_lines(color)`：两像素一行，返回 11 行字符串；按 design 决策 2 处理前景 / 背景、默认前景色与无颜色；验证：有颜色时至少一行含 `48;5;`，无颜色时输出不含 `\033` 且只含 `▀▄█` 与空格。
- [x] 1.3 `render` 在画字标的条件下，先拼图标 11 行、再一行空行、再字标；验证：`render("9.9.9", INIT_FOOTER, 80, False, True)` 前 11 行是图标、第 12 行为空、第 13 行以 `█▀▀█` 开头；`width=59` 或 `unicode_ok=False` 时输出与改动前逐字相同。

## 2. 测试（`tests/test_banner.py`）

- [x] 2.1 改现有断言：首行从字标改为图标首行，宽度断言覆盖图标与字标各行，`test_show_draws_logo_in_wide_utf8_terminal` 的 `startswith` 改为图标首行的转义；验证：`uv run pytest tests/test_banner.py` 通过。
- [x] 2.2 新增用例：图标 11 行且每行不超过 26 列；有颜色时马像素带字标的色号、兔的阴影压在马身上时马做背景（`48;5;`）、兔身格子逐格不带转义；`_cell` 的六种像素组合（含兔身与有色像素共用一格时只设背景）逐一断言；`NO_COLOR` 下无转义且图标仍在；窄终端或非 UTF-8 时输出没有块字符；验证：`uv run pytest tests/test_banner.py` 通过。

## 3. 集成检查

- [x] 3.1 `uv run ruff check .` 与 `uv run pytest` 全部通过；在真实终端运行 `rulemason` 与 `rulemason init`（停在预检即可）目视确认马蓝、兔默认色、兔骑在马背上；验证：结果记入 change 的 `verification.md`。
- [x] 3.2 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行自动精简、独立审查与完成汇报；验证：`verification.md` 逐项有结果，design 的估计行数对照写明。
