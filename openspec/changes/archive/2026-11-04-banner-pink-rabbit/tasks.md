# Tasks

## 1. 实现

- [x] 1.1 `src/rulemason/banner.py` 的 `ICON_COLORS` 把兔身 `w` 改为 `211`、兔的阴影 `g` 改为 `168`，上方注释同步改为「兔身樱粉，兔的阴影深一档」；`tests/test_banner.py` 里断言兔身白 `231` 的用例改为断言 `211`；验证：`uv run pytest tests/test_banner.py` 通过，交互运行 `rulemason` 在浅色与深色终端里都能看清兔子
- [x] 1.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`
