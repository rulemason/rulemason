# Tasks

## 1. git 按 UTF-8 读写

- [x] 1.1 `shared.git`、`has_git`、`ignored_files` 的 git 调用加 `encoding="utf-8"`，`judge.changed_copy` 改用 `shared.git`；验证：新增用例用替身让「没写 encoding 的 text=True 调用」按 GBK 解码（复现 Windows 中文版），`tests/judge/test_engine.py` 断言 `--copy` 在只改一条中文文案时只检查那一条，`tests/test_shared.py` 断言中文文件名被正确判为忽略；改动前这两个用例会失败

## 2. key

- [x] 2.1 `judge.py` 新增 key 合法性判断（去掉首尾空白后全是可打印 ASCII、不含空白）与「值与来源」的读取；`key.py` 写入前用它检查，不合格不写入、以非 0 退出，含 `0x16` 时提示用右键或 Ctrl+Shift+V 粘贴；验证：`tests/test_key.py` 新增 `0x16` 与夹空格两个用例，key 文件不存在或内容不变
- [x] 2.2 `Judge._jev` 建客户端前检查 key，不合格以「✗」开头一句话退出，写明来源（环境变量或文件路径）与 `rulemason key`；`--dry-run`、`--lint-only` 不检查；验证：`tests/judge/test_engine.py` 新增文件里是 `0x16`、环境变量夹空格、`--lint-only` 不受影响三个用例，输出不含 `Traceback`

## 3. 显示

- [x] 3.1 `banner._unicode_ok` 改名为 `_can_draw_blocks`，在 Windows 上要求有 `WT_SESSION` 或 `TERM_PROGRAM`；验证：`tests/test_banner.py` 新增用例，`sys.platform` 设为 win32、两个变量都没有时输出以「rulemason 版本号」一行开头、不含图标字符，有 `WT_SESSION` 时画图标；macOS 现有用例仍通过
- [x] 3.2 judge 的 specs 小标题用 `as_posix()`；验证：用例构造 `specs/a/spec.md` 断言小标题写 `specs/a/spec.md`，用于锁定输出（macOS 上修复前也会通过，反斜杠只在 Windows 上出现）

## 4. 收尾

- [x] 4.1 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙运行开发版 `rulemason check` 与 `rulemason judge --change <已归档 change> --lint-only`，确认与 0.8.14 相同；验证：结果与 design 行数对照写进 `verification.md`，未在 Windows 上核实的项写明待实测

## Workflow follow-up

- 与 init-at-cwd 一起发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README CI 钉版本，推送、归档、打 tag；发布说明写明 Windows 修复，请 Windows 用户实测 `judge --copy`、`rulemason key` 的 Ctrl+V 提示与旧控制台启动画面。
- Notion 第 71 篇补实测结果。
