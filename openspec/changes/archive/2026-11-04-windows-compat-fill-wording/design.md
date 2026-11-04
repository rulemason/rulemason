# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 写 key 文件：先 `os.chmod(path.parent, 0o700)`，再用 `os.open(..., O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0o600)` 打开、`os.fchmod(descriptor, 0o600)` 收紧，汇报写「权限 600」（`src/rulemason/key.py:26-32`）。`os.O_NOFOLLOW` 只在 Unix 上存在；`os.fchmod` 在 Windows 上要 Python 3.13 才有（Python 官方文档 os 模块，未在 Windows 上核实）。项目支持 Python 3.11 起（`pyproject.toml:9`）。
- 代跑 openspec：先 `shutil.which("openspec")` 判断有没有命令，再以 `["openspec", "init", ...]` 启动（`src/rulemason/init.py:312-319`）。Windows 上 `which` 会按 PATHEXT 找到 `openspec.cmd`，而只给名字 `openspec` 启动时不会补扩展名，于是报 `[WinError 2]`（Notion 第 71 篇实测）。用完整路径启动 `.cmd` 能否成功：未核实（本机没有 Windows）。
- 颜色：`color_enabled()` 只看 `NO_COLOR` 与标准输出是不是终端（`src/rulemason/shared.py:90-92`），`paint` 与启动画面都经它判断（`src/rulemason/shared.py:97`、`src/rulemason/banner.py:135`）。Windows 旧版控制台默认不解析 ANSI，于是显示 `[38;5;…m`（Notion 第 71 篇实测）。
- 逐键选择没有 termios 时已抛 `Unsupported`，由调用方退回普通选择（`src/rulemason/select.py:22-27`），本次不动。
- 补齐计划的说法：试运行与正式运行都打印「补齐计划（你自己的文件）：…」，试运行结尾是「确认后运行 rulemason update（补齐计划加 --yes）」（`src/rulemason/update.py:77-80`、`:113`）；`tests/test_update.py:76`、`:228` 断言了原文。skill 的 `update` 一行写「由用户决定是否 `rulemason update --yes`」（`skills/rulemason/SKILL.md:29`）。

## Goals / Non-Goals

**Goals:**
- Windows 上 `rulemason key`、代跑 `openspec init` 能用，旧版控制台不出现乱码。
- macOS 与 Linux 上的行为、权限与输出不变（只改补齐计划的措辞）。

**Non-Goals:**
- 不在 CI 加 Windows 运行，也不为 Windows 改写现有测试；Windows 行为用替身模拟，发版后请 Windows 用户实测。
- 不在 Windows 上设置 ACL；key 文件放在用户目录下，依赖系统对用户目录的默认权限。

## Decisions

1. **key：有什么用什么。** `O_NOFOLLOW` 用 `getattr(os, "O_NOFOLLOW", 0)`，`fchmod` 只在 POSIX 上调用；打开时并上 `getattr(os, "O_BINARY", 0)`，免得 Windows 的文本模式与 Python 各转一次换行；汇报按 `os.name == "posix"` 决定写「权限 600」还是「在当前用户目录下」。否决在 Windows 上调 `icacls` 收紧 ACL：要起外部命令、行为随系统语言与策略变化，而用户目录本来只对本人可写。否决 Windows 上直接拒绝写入、只提示用环境变量：等于不修。
2. **openspec：用 which 的结果启动。** `command[0]` 换成 `shutil.which("openspec")` 返回的完整路径，展示给用户的命令仍写 `openspec init …`。参数只有工具 id 与固定的 `zh-CN`，不含用户输入，用 `.cmd` 启动不涉及参数转义的风险。否决 `shell=True`：参数经 shell 解析，平台差异更大。否决硬编码追加 `.cmd`：用户可能用 pnpm、scoop 等装出 `.exe` 或 `.ps1` 包装。
3. **颜色：Windows 上先开 ANSI，开不了就不上色。** 在 `color_enabled()` 里，Windows 平台在函数内导入 `ctypes`（缺 libffi 的 Python 导入 ctypes 会失败，不能影响其他平台），调 `GetConsoleMode` / `SetConsoleMode` 为标准输出加上 `ENABLE_VIRTUAL_TERMINAL_PROCESSING`，结果缓存，失败返回 False。否决引入 colorama：新增依赖只为一个平台。否决 Windows 上一律不上色：Windows Terminal 与新版控制台能正常显示，白白丢掉颜色。
4. **补齐说法只改文字，不改流程。** 补齐计划一行改为「补齐计划（写进项目文件的 rulemason 基础配置，升级时与副本一起提交）：…」；试运行结尾改为「只列计划，未写任何文件。终端里运行 rulemason update 会询问是否补齐；非交互环境加 --yes」；正式补齐后写「已补齐。这些文件属于这次升级，请与副本、.rulemason.yaml 一起提交。」。否决把补齐计划改成自动写入：规格要求改项目文件前先确认，这条不变。否决让 update 自动提交：rulemason 不提交是一贯约定。
5. **skill 写明怎么认出升级产出。** 以 update 输出里「补齐计划」列出的文件为准；事后再看时，把 `openspec/config.yaml` 里未提交的新增条目与安装包里的 `_shared/openspec-base/*.yaml` 逐字比对，能找到就是基础版。巡检的「与基础版的差异」只查基础条目有没有缺（`src/rulemason/check.py:495-505`），不能用来认定新增条目是基础版。汇报把升级产出列为「提交时与副本一起带上」；skill 本身仍不提交。否决让 check 输出「哪几行来自基础版」：要扩 `--json` 字段，本次只改说法。

## Risks / Trade-offs

- [替身测不出真实 Windows 的行为（`.cmd` 启动、`SetConsoleMode`）] → design 标为未核实；发版说明请 Windows 用户实测 `rulemason key`、代跑 `openspec init` 与旧控制台显示，结果回写 Notion 第 71 篇。
- [`SetConsoleMode` 在输出被重定向时失败] → 标准输出不是终端时本来就不上色，先判断终端再调 Windows 接口。
- [Python 3.12.0 的 `shutil.which` 在 Windows 上可能返回 npm 生成的无扩展名脚本（3.12.1 修复），启动会报 WinError 193（未核实）] → 发布说明请 Windows 用户用 3.11 或 3.12.1 及以上；仍出错时手动运行 `openspec init`。
- [Windows 上 key 文件权限依赖用户目录默认 ACL] → 汇报如实写「在当前用户目录下」，不声称 600；统一入口的已知问题改写为这一说明。
- [改了 update 的输出文字，依赖原文的脚本或 AI 提示会对不上] → `--json` 字段不变，只改文字输出；测试断言同步改。

## Migration Plan

1. 改 `key.py`、`init.py`、`shared.py`、`update.py` 与 SKILL.md，补替身测试，跑 ruff 与测试；在本机与三个接入项目跑 `rulemason update --dry-run` 看新说法。
2. 发版（版本号按发版时 PyPI 已有版本递增），发布说明写明 Windows 三处修复与补齐说法，请 Windows 用户实测。
3. 接入项目升级后运行 `rulemason update`，刷新 skill 副本。

回滚：`uv tool install rulemason==<上一版>` 后 `rulemason update`；这次不改任何项目文件的格式，回滚不留痕迹。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/key.py` | 按平台取 `O_NOFOLLOW`、`fchmod`，汇报按平台写 | +8 / −3 |
| `src/rulemason/init.py` | `ensure_openspec` 用 which 的结果启动 | +3 / −2 |
| `src/rulemason/shared.py` | `color_enabled` 在 Windows 上先开 ANSI | +20 / −2 |
| `src/rulemason/update.py` | 补齐计划、试运行结尾与补齐后的说法 | +4 / −3 |
| `skills/rulemason/SKILL.md` | `update` 一行与巡检：补齐计划改动的文件属于升级 | +3 / −1 |
| `tests/test_key.py` | 模拟没有 `O_NOFOLLOW`、`fchmod` 的平台 | +20 |
| `tests/test_init.py` | 替身 which 返回带扩展名的路径，断言以该路径启动 | +15 |
| `tests/test_shared.py` 或 `tests/test_banner.py` | 模拟 Windows 开启 ANSI 成功与失败 | +25 |
| `tests/test_update.py` | 新说法断言；交互确认后的提醒 | +10 / −2 |
| `tests/test_templates.py` | skill 新说法 | +5 |
