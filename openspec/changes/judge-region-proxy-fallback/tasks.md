# Tasks

## 1. 实现

- [x] 1.1 `judge.py`：判断本机有无代理；`Judge` 记录是否改走代理，`_jev` 按它决定 `trust_env`；`ask` 遇 451 且本机有代理、尚未改走代理时，输出一行说明、重建连接重发一次；验证：`tests/judge/test_engine.py` 用假的 SDK 客户端（不联网）覆盖直连成功不建代理连接、451 有代理时换路且两次请求只说明一次、已改走代理后不再先直连，`uv run pytest tests/judge` 通过
- [x] 1.2 `cli()` 捕获 451：本机没有代理时提示设置 `HTTPS_PROXY`，有代理时提示换代理，以非 0 退出、无堆栈；验证：仿照 `test_rejected_key_gives_one_line_error` 新增两条用例，断言文字与无 `Traceback`，`uv run pytest tests/judge` 通过
- [x] 1.3 README「判断」一节补一句：被按地区拒绝时自动改用本机代理，Linux / WSL 需设 `HTTPS_PROXY`；验证：`rg -n "HTTPS_PROXY" README.md` 有这一句，`uv run pytest tests/test_templates.py` 通过
- [x] 1.4 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
