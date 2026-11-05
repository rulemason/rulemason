## Why

Windows 实测与 Cursor、OpenCode 实测留下四个小问题（Notion 第 71、81 篇），单个都不值得发版，合在一起修：

1. Windows 旧控制台（conhost）里，报错开头的 `✗` 显示成方框：控制台字体按 GBK 取字，`✗` 不在 GBK 里。
2. init 计划在没有其他未提交改动时仍写「不会碰：其余 0 个未提交改动不变」，是一行废话。
3. Python 项目有 `pyproject.toml` 但没有 `uv.lock` 时，命令表的 ruff 与测试都写成「无，跳过」，检查点于是不跑 lint 与测试。
4. OpenCode 里 skill 不进 `/` 列表，照着「在 AI 工具中运行 /rulemason」找不到，要对它说「用 rulemason skill」。

## What Changes

- 报错开头的标记按终端选字形：Windows 旧控制台（与启动画面同一判断：没有 `WT_SESSION` 也没有 `TERM_PROGRAM`）用 `×`，其他终端仍用 `✗`。覆盖 `rulemason judge` 与 `rulemason key` 的报错。
- init 与 update 的计划只在有计划外的未提交改动时写数量那一行；数量为 0 时不写。
- 命令表识别：有 `pyproject.toml`、没有 `uv.lock` 的最上层 Python 目录，ruff 填 `uvx ruff check .`（uv workspace 成员等上层已有 `pyproject.toml` 的目录不重复）；测试一行并列「待确认：填项目跑测试的命令」，不再写「无，跳过」。有 `uv.lock` 的项目与前端识别不变。
- 项目工具里有 OpenCode 时，init 收尾的下一步与 `check` 报告在「运行 /rulemason」之后加一行：OpenCode 里对它说「用 rulemason skill」。`check` 第一行与 `--json` 的 `next` 不变。
- 不做：改 `✓` 等其他符号；检测控制台字体；猜项目的测试命令（venv、conda、Docker 各不相同）；改其他工具的叫法提示。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `judge-engine`：「判断引擎读配置出错时给可读提示」「key 含无效字符时给一句话提示」两条的「以「✗」开头」改为以错误标记开头（Windows 旧控制台为 `×`）。
- `rulekit-cli`：新增四条——报错标记按终端选字形；计划只在有未提交改动时写数量；没有 `uv.lock` 的 Python 项目的命令表；OpenCode 项目写明 skill 的叫法。

## Impact

- 代码：`src/rulemason/shared.py`（旧控制台判断与报错标记）、`banner.py`（改用共享判断）、`judge/judge.py` 与 `key.py`（报错标记）、`init.py`（未提交改动行、命令表识别、OpenCode 一行）、`check.py`（OpenCode 一行）；对应测试。
- 接入项目：无需操作。已接入项目的命令表不会被改写，只有新接入的项目受第 3 项影响；已写着「无，跳过」的项目可运行 `/rulemason` 重新确认命令表。
