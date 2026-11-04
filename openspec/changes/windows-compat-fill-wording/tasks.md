# Tasks

## 1. Windows 兼容

- [x] 1.1 `key.py`：`O_NOFOLLOW` 用 `getattr(os, "O_NOFOLLOW", 0)`，`fchmod` 只在 POSIX 上调用，打开时并上 `O_BINARY`（Windows 不再按文本模式转换换行），汇报在 POSIX 上写「权限 600」、其他平台写「在当前用户目录下」；验证：`tests/test_key.py` 新增用例用 monkeypatch 去掉 `os.O_NOFOLLOW`、`os.fchmod` 并把 `os.name` 设为 `nt`，`rulemason key` 写入成功、汇报不含「600」；原有权限用例仍通过
- [x] 1.2 `init.ensure_openspec`：以 `shutil.which("openspec")` 返回的完整路径启动，提示文字仍写 `openspec init …`；验证：`tests/test_init.py` 原有 `test_new_dir_agrees_to_openspec_init` 加 `subprocess.run` 的 spy，断言 openspec 以 `shutil.which` 返回的完整路径启动且接入完成
- [x] 1.3 `shared.color_enabled`：Windows 平台在确认是终端后，用 `ctypes` 为标准输出开启 ANSI 支持，结果缓存，失败时返回 False；其他平台逻辑不变；验证：新增用例模拟 `sys.platform == "win32"` 与开启成功 / 失败两种结果，失败时 `paint` 与启动画面输出不含 `\x1b[`，`NO_COLOR` 用例仍通过

## 2. 补齐计划的说法

- [x] 2.1 `update.py`：补齐计划一行改为「补齐计划（写进项目文件的 rulemason 基础配置，升级时与副本一起提交）：…」，试运行结尾改为「终端里运行 rulemason update 会询问是否补齐；非交互环境加 --yes」，补齐写入后提醒与副本一起提交；`--json` 字段不变；验证：`tests/test_update.py:76`、`:228` 的断言改为新说法并通过，新增交互答 y 后输出含提醒的用例，`update --dry-run --json` 字段集合不变
- [x] 2.2 `skills/rulemason/SKILL.md`：`update` 一行改为「终端里运行会询问是否补齐，非交互加 --yes」；巡检一节补：以 update 输出的补齐计划为准，事后与安装包里的 `_shared/openspec-base/*.yaml` 逐字比对认出升级产出（「与基础版的差异」不能用来认定），汇报列为「提交时与副本一起带上」，skill 不提交；验证：`tests/test_templates.py` 断言 skill 含这两处新说法

## 3. 收尾

- [x] 3.1 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙运行开发版 `rulemason update --dry-run`，确认只多出新说法、计划与 0.8.13 相同；验证：结果与 design 行数对照写进 `verification.md`，未核实的 Windows 行为写明待实测

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README CI 钉版本，推送、归档、打 tag；发布说明写明 Windows 三处修复与补齐说法，请 Windows 用户实测 `rulemason key`、代跑 `openspec init` 与旧控制台显示。
- 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`；Notion 统一入口删去已修的 Windows 已知问题行，第 71 篇补实测结果。
