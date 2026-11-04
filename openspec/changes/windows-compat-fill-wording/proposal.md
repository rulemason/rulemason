## Why

Windows 上实测（Notion 第 71 篇）有三处直接卡住接入：

- `rulemason key` 崩溃：`AttributeError: module 'os' has no attribute 'O_NOFOLLOW'`。写 key 文件用了 Windows 没有的 `os.O_NOFOLLOW` 与 `os.fchmod`（`src/rulemason/key.py:27-28`）。
- `rulemason init` 代为运行 `openspec init` 报 `[WinError 2]`。`shutil.which("openspec")` 能找到 npm 装的 `openspec.cmd`，但随后用 `["openspec", ...]` 启动，Windows 不会自动补 `.cmd`（`src/rulemason/init.py:312-319`）。
- 旧版控制台满屏 `[38;5;…m`。只要标准输出是终端就输出 ANSI 颜色，没有确认控制台能显示（`src/rulemason/shared.py:90-92`）。

另外，`rulemason update` 把补齐计划写成「补齐计划（你自己的文件）：openspec/config.yaml」（`src/rulemason/update.py:77`、`:113`）。某接入项目升级 0.8.13 时，AI 据此把补齐写进 `openspec/config.yaml` 的 rulemason 基础条目当成项目自己的规则，没有和副本一起提交。试运行结尾的「确认后运行 rulemason update（补齐计划加 --yes）」又容易读成每次都要再加 `--yes` 跑一遍。

## What Changes

- `rulemason key` 在 Windows 上能写入 key：没有 `O_NOFOLLOW`、`fchmod` 的平台不用它们；汇报不再声称「权限 600」，改为说明文件在当前用户目录下。
- `init` 代跑 `openspec init` 时，用 `shutil.which` 找到的完整路径启动，Windows 上的 `openspec.cmd` 也能运行。
- 颜色：Windows 上先尝试为控制台开启 ANSI 支持，开不了就不输出颜色；其他平台行为不变，`NO_COLOR` 照旧生效。
- `update` 的补齐说法改为写明「写进你的文件的是 rulemason 的基础配置，升级时与副本一起提交」；试运行结尾改为「终端里运行 `rulemason update` 会询问是否补齐；非交互环境加 `--yes`」。skill 的 `update` 一行与巡检说明同步：补齐计划改动的文件属于这次升级，提交时一起带上。
- 不做：在 CI 加 Windows 运行（现有测试大量依赖 POSIX 的权限与符号链接行为，另开 change）；Windows 上的逐键选择界面（没有 termios 时已退回非交互选择）；没有 `uv.lock` 时 ruff 命令识别为「跳过」的问题（与 Windows 无关，另开 change）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：`key` 在没有 `O_NOFOLLOW` 的平台上的写法与汇报；`init` 代跑 `openspec init` 的启动方式；颜色输出在控制台不支持时关闭；`update` 补齐计划与试运行结尾的说法。
- `rules-layer-setup`：skill 说明补齐计划改动的文件属于升级、提交时一起带上。

## Impact

- 代码：`src/rulemason/key.py`、`src/rulemason/init.py`（`ensure_openspec`）、`src/rulemason/shared.py`（`color_enabled`）、`src/rulemason/update.py`；对应测试用替身模拟 Windows（没有 `O_NOFOLLOW`、`which` 返回 `.cmd` 路径、控制台不支持颜色）。
- 共享正文：`skills/rulemason/SKILL.md`。README 没有写这几个 Windows 问题，不用改；Notion 统一入口里的「已知问题」行在发版后删去。
- 接入项目：升级后 `rulemason update` 刷新 skill 副本；Windows 用户可以直接用 `rulemason key` 与代跑的 `openspec init`。
