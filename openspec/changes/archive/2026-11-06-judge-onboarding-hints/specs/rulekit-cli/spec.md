## MODIFIED Requirements

### Requirement: init 结尾引导配置 key

交互运行且未带 `--yes` 时，写入完成后：项目已满足判断条件（在 git 里且已归档至少 3 个 change）、判断未启用时，本机没有 key 则 `init` SHALL 问一句是否现在配置 Jev 的 key，附申请地址 https://typesafe.ai/ ，回答是则进入与 `rulemason key` 相同的不回显输入，否则提示以后运行 `rulemason key`；本机已有 key 则 SHALL 只输出一行：条件已满足，判断只审 OpenSpec 方案与界面文案，要启用时在 AI 工具中运行 `/rulemason` 并说明要启用判断。条件未满足时 SHALL 只提示一行启用条件。`--yes`、`--plan` 或非交互运行 MUST NOT 提问或输出这些说明。`init` MUST NOT 接受或打印 key。

#### Scenario: 条件满足且没有 key
- **WHEN** 项目已归档 3 个 change、本机没有 key，在终端运行 `rulemason init` 并写入完成
- **THEN** 结尾问「现在配置 Jev 的 key 吗」并附申请地址；回答 y 后进入不回显输入，写入 `~/.config/rulemason/env`

#### Scenario: 条件未满足
- **WHEN** 项目只归档了 1 个 change，本机没有 key
- **THEN** 结尾只提示「判断功能需要至少 3 个已归档 change；满足后运行 rulemason key」，不提问

#### Scenario: 已有 key 或非交互
- **WHEN** 本机已有 key，或运行 `rulemason init --tools claude --yes`
- **THEN** 结尾不出现任何关于 key 的提问

#### Scenario: 已有 key、条件满足、未启用
- **WHEN** 项目已归档 60 个 change、没有 `openspec/judgments.yaml`、本机已有 key，在终端运行 `rulemason init` 并写入完成
- **THEN** 结尾多一行：判断条件已满足，判断只审 OpenSpec 方案与界面文案，要启用在 AI 工具中运行 `/rulemason` 并说明要启用判断；不提问

## ADDED Requirements

### Requirement: 识别表写接入后归档数

`rulemason check` 的识别表 SHALL 有一行「接入后归档 change」：日期前缀晚于接入日期的已归档 change 个数（与「最近归档的检查点记录」用同一个接入日期与同一种比较）。接入日期推算不出来时 SHALL 写「—」。`--json` 的 `facts` 里同名的键 SHALL 带同样的值。

#### Scenario: 接入后归档过两个
- **WHEN** 接入日期 `2026-11-02`，已归档 `2026-10-30-a`、`2026-11-02-b`、`2026-11-04-c`、`2026-11-05-d`
- **THEN** 识别表写「接入后归档 change：2」（接入当天的 b 不算）

#### Scenario: 推算不出接入日期
- **WHEN** 清单没有 `joined`，项目不在 git 里
- **THEN** 识别表写「接入后归档 change：—」
