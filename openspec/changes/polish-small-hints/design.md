# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 报错标记 `✗` 写死在字符串里：`src/rulemason/judge/judge.py` 17 处（`grep -c "✗" src/rulemason/judge/judge.py`），`src/rulemason/key.py:14`、`:22`。旧控制台按 GBK 取字形，`✗`（U+2717）不在 GBK 里，`×`（U+00D7）在（Windows 10 实测截图，Notion 第 81 篇）。
- 旧控制台判断已有：`src/rulemason/banner.py:126` 的 `_can_draw_blocks`，Windows 上没有 `WT_SESSION` 与 `TERM_PROGRAM` 时返回 False；判断和「能否写出块字符」揉在一个函数里。
- 未提交改动行：`src/rulemason/init.py:738` 的 `untouched_line` 总是返回一行，由 `:752`（计划摘要）与 `:780`（完整清单）追加；update 复用同一渲染。
- 命令表识别：`src/rulemason/init.py:347` 的 `detect_commands` 只在 `pyproject.toml` 旁有 `uv.lock` 时填 ruff 与 pytest，否则三行都落到 `skip = "无，跳过"`（`:365`）。
- 下一步文字：`src/rulemason/init.py:59` 的 `NEXT_STEP`（`:860` 打印）；`src/rulemason/check.py:1080` 的 `Next("补项目信息", "fill_project_info", …)`，报告第一行由 `render`（`:1108`）写出。工具 id 为 `opencode`（`src/rulemason/shared.py:26`）。
- 主规格：judge-engine 两条写了「以「✗」开头」（`openspec/specs/judge-engine/spec.md:150`、`:162`）；rulekit-cli 的 check 第一行与 `--json` 的 `next` 逐字写着「在 AI 工具中运行 /rulemason」（`openspec/specs/rulekit-cli/spec.md:351`、`:419`）。

## Goals / Non-Goals

**Goals:**
- 旧控制台里报错开头不再是方框；其他终端输出不变。
- 计划不出现零个未提交改动；没有 `uv.lock` 的 Python 项目检查点也跑 lint，测试命令交给人确认。
- OpenCode 用户照着提示能找到 skill。

**Non-Goals:**
- 不改 `✓` 等其他符号，不检测控制台字体。
- 不猜项目的测试命令，不改已有项目的命令表。

## Decisions

1. **旧控制台判断抽到 `shared.py`（`legacy_console()`），报错整句由 `shared.fail(消息)` 按它加「×」或「✗」；`banner._can_draw_blocks` 改为调用它。** judge 与 key 的报错改用 `fail()`；OpenCode 那一行由 `shared.skill_hint_lines(tools)` 给出，init 与 check 共用。否决全平台改用「×」：macOS 与 Windows Terminal 上 `✗` 更醒目，且 judge-engine 规格的场景都按 `✗` 写。否决改成 ASCII「x」或「错误：」：改动所有报错与规格场景，收益只在旧控制台。否决做成模块级常量：测试要按平台切换，函数更好替身。
2. **`untouched_line` 改为 `untouched_lines`，返回要写的行：数量为 0 时为空列表，两处调用 `lines += …` 不用再判断。** 否决改写成「没有其他未提交改动」：多一行同样没有信息量。
3. **没有 `uv.lock` 时 ruff 用 `uvx ruff check .`，测试一行并列「待确认：填项目跑测试的命令」；上层已有 `pyproject.toml` 的目录跳过。** 跳过上层已有 Python 项目的目录，是因为上层那条 ruff 已覆盖它（uv workspace 成员没有自己的 `uv.lock`，否则每个成员都多一条重复的 lint；独立审查发现、用户确认）。「待确认」与其他测试命令并列而不是只在没有其他命令时写，免得混合仓库里 Python 测试被悄悄略过（同上）。uv 是安装 rulemason 的前提，`uvx` 不依赖项目环境，ruff 读项目里继承基础规则的 `ruff.toml`。否决 `ruff check .`：本机不一定装了 ruff。否决 `uv run ruff check .`：没有 uv 项目时 uv 会去建环境或报错。否决猜 `python -m pytest`：依赖装在 venv、conda 还是 Docker 猜不到；写「待确认」让 `/rulemason` 补项目信息时一起问。
4. **OpenCode 那一行加在第一行之后，不改 `Next.action`。** init 的 `NEXT_STEP` 后同样追加。否决改 `action` 文字：规格场景与 `--json` 的 `next` 都逐字写着原句，AI 按它查表。否决对所有项目都显示：没用 OpenCode 的项目多一行噪音。

## Risks / Trade-offs

- [ConEmu、ssh 登录 Windows 时没有 `WT_SESSION` 与 `TERM_PROGRAM`，能显示 `✗` 也会改用 `×`] → `×` 同样能读，只是字形不同，接受。
- [`uvx ruff` 首次运行要下载 ruff，离线时失败] → 检查点会报出 ruff 跑不了，人可在命令表改成本地命令；比悄悄跳过 lint 好。
- [「待确认」被检查点当成命令去跑] → 文字里没有反引号，不像命令；预计 AI 跑检查点时会在汇报里写明测试命令待确认（未核实）；命令表仍带「自动识别，请确认」，`check` 的下一步指向 `/rulemason`，补项目信息时会问到。

## Migration Plan

1. 改 `shared.py`、`banner.py`、`judge/judge.py`、`key.py`、`init.py`、`check.py`，补测试，跑 ruff 与测试。
2. 发版（版本号按发版时 PyPI 已有版本递增），发布说明写明四处变化；请 Windows 用户在旧控制台看一次报错标记。
3. 接入项目无需操作。

回滚：`uv tool install rulemason==<上一版>`；本次不改任何项目文件格式，已生成的命令表不受影响。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/shared.py` | `legacy_console()`、`fail()`、`skill_hint_lines()` | +12 |
| `src/rulemason/banner.py` | `_can_draw_blocks` 改用 `legacy_console()` | +1 / −1 |
| `src/rulemason/judge/judge.py` | 17 处报错改用 `fail()` | ±17 |
| `src/rulemason/key.py` | 2 处报错改用 `fail()` | ±2 |
| `src/rulemason/init.py` | `untouched_lines` 为 0 返回空列表与两处调用；`detect_commands` 识别没有 `uv.lock` 的目录；OpenCode 一行 | +18 / −4 |
| `src/rulemason/check.py` | 报告第一行后的 OpenCode 一行 | +4 |
| `tests/test_shared.py` | 旧控制台与标记 | +20 |
| `tests/test_init.py` | 零个未提交改动、没有 `uv.lock` 的命令表、OpenCode 一行 | +45 |
| `tests/test_check.py` | OpenCode 一行出现与不出现、`--json` 不变 | +25 |
| `tests/test_key.py`、`tests/judge/test_engine.py` | 旧控制台下报错以「×」开头 | +15 |
