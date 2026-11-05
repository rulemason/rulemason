## ADDED Requirements

### Requirement: 报错标记按终端选字形

`rulemason` 各命令以错误标记开头的报错，SHALL 在 Windows 旧控制台（与启动画面同一判断：在 Windows 上，既没有 `WT_SESSION` 也没有 `TERM_PROGRAM`）用「×」，其他终端用「✗」。标记之后的文字 MUST NOT 因终端而变。

#### Scenario: Windows 旧控制台
- **WHEN** 在 Windows 的 cmd.exe 中运行 `rulemason key`，标准输入不是终端
- **THEN** 输出以「×」开头，说明要在终端里运行

#### Scenario: 其他终端
- **WHEN** 在 macOS 终端里运行 `rulemason judge`，当前目录不在 git 仓库里
- **THEN** 输出以「✗」开头

### Requirement: 计划只在有未提交改动时写数量

`init` 与 `update` 的计划 SHALL 只在计划以外有未提交改动时写「不会碰：其余 N 个未提交改动不变」；数量为 0 时 MUST NOT 写这一行。没有 git 时照旧说明无法统计。

#### Scenario: 没有其他未提交改动
- **WHEN** 工作区干净，运行 `rulemason init --plan`
- **THEN** 计划里没有「其余 0 个未提交改动不变」这一行

#### Scenario: 有其他未提交改动
- **WHEN** 项目有 2 个与 rulemason 无关的未提交改动，运行 `rulemason init --plan`
- **THEN** 计划写明「其余 2 个未提交改动不变」

### Requirement: 没有 uv.lock 的 Python 项目的命令表

`init` 识别命令表时，有 `pyproject.toml`、没有 `uv.lock`、且上层目录没有 `pyproject.toml` 的目录，ruff 一行 SHALL 填 `uvx ruff check .`（不在项目根时前面加 `cd <目录> &&`）；上层已有 `pyproject.toml` 的目录（如 uv workspace 成员）MUST NOT 另加一条。有这样的目录时，测试一行 SHALL 含「待确认：填项目跑测试的命令」，与识别出的其他测试命令并列，MUST NOT 写「无，跳过」。有 `uv.lock` 的目录与前端命令的识别不变。已有命令表的 `AGENTS.md` MUST NOT 被改写。

#### Scenario: 只有 pyproject.toml
- **WHEN** 项目根有 `pyproject.toml` 与 `tests/`，没有 `uv.lock` 与 `package.json`，运行 `rulemason init --yes`
- **THEN** 命令表的 ruff 一行为 `uvx ruff check .`，测试一行为「待确认：填项目跑测试的命令」

#### Scenario: 有 uv.lock
- **WHEN** 项目有 `pyproject.toml`、`uv.lock` 与 `tests/`
- **THEN** 命令表仍为 `uv run ruff check .` 与 `uv run pytest`

#### Scenario: uv workspace 成员
- **WHEN** 项目根有 `pyproject.toml`、`uv.lock` 与 `tests/`，`packages/a/` 有 `pyproject.toml` 没有 `uv.lock`
- **THEN** ruff 一行只有 `uv run ruff check .`，测试一行只有 `uv run pytest`

#### Scenario: 前端测试与没有锁文件的 Python 并存
- **WHEN** `web/package.json` 有 test 脚本，`api/` 有 `pyproject.toml` 没有 `uv.lock`
- **THEN** 测试一行为「`cd web && npm run test`；待确认：填项目跑测试的命令」

### Requirement: OpenCode 项目写明 skill 的叫法

清单的工具里有 OpenCode 时，`init` 收尾的下一步与 `check` 报告在「在 AI 工具中运行 /rulemason」之后 SHALL 另起一行写明：OpenCode 里 skill 不在 `/` 列表，对它说「用 rulemason skill」。`check` 第一行与 `--json` 的 `next` MUST NOT 因此改变；没有 OpenCode 时 MUST NOT 出现这一行。

#### Scenario: 接入了 OpenCode
- **WHEN** 清单工具为 OpenCode 与 Claude Code，项目信息待补，运行 `rulemason check`
- **THEN** 第一行仍是「补项目信息：在 AI 工具中运行 /rulemason」，紧接一行写明 OpenCode 里说「用 rulemason skill」；`check --json` 的 `next` 与原来相同

#### Scenario: 没有 OpenCode
- **WHEN** 清单工具只有 Claude Code，项目信息待补，运行 `rulemason check`
- **THEN** 报告里没有 OpenCode 那一行
