# Tasks

## 1. 像素数据（`src/rulemason/banner.py`）

- [x] 1.1 把 `ICON` 换成 design.md 附录的 26×20 网格，注释里「26 列 × 22 行」与 `_icon_lines` docstring 里「22 行像素合成 11 行」改为 20 与 10；验证：`uv run python -c "from rulemason import banner; assert len(banner.ICON) == 20 and {len(r) for r in banner.ICON} == {26} and len(banner._icon_lines(False)) == 10"` 不报错，且无色渲染 `_icon_lines(False)` 的后 5 行与改动前的后 5 行逐字相同（这 5 行的像素位置没变，只是整体上移一行；其中第 1 行含兔脚，彩色下颜色不同）。

## 2. 测试（`tests/test_banner.py`）

- [x] 2.1 `ICON_ROWS` 改为 10 并更新注释，`test_icon_is_eleven_rows_within_26_cols` 改名为 `test_icon_is_ten_rows_within_26_cols` 且断言 `len(banner.ICON) == 20`；验证：`uv run pytest tests/test_banner.py` 通过。

## 3. 集成检查

- [x] 3.1 `uv run ruff check .` 与 `uv run pytest` 全部通过；伪终端运行 `rulemason`，前 10 行是图标、第 11 行空、第 12 行起是字标；验证：结果记入 change 的 `verification.md`。
- [x] 3.2 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行自动精简、独立审查与完成汇报；验证：`verification.md` 逐项有结果，design 的估计行数对照写明。
