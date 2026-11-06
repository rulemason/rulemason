## MODIFIED Requirements

### Requirement: init 结尾引导配置 key

交互运行且未带 `--yes` 时，写入完成后：项目已满足判断条件（在 git 里且已归档至少 3 个 change）、判断未启用时，本机没有 key 则 `init` SHALL 问一句是否现在配置 Jev 的 key，附申请地址 https://typesafe.ai/ ，回答是则进入与 `rulemason key` 相同的不回显输入，否则提示以后运行 `rulemason key`；本机已有 key 则 SHALL 只输出一行：条件已满足，判断审 OpenSpec 方案、界面文案与直接改动的说明，要启用时在 AI 工具中运行 `/rulemason` 并说明要启用判断。条件未满足时 SHALL 只提示一行启用条件。`--yes`、`--plan` 或非交互运行 MUST NOT 提问或输出这些说明。`init` MUST NOT 接受或打印 key。

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
- **THEN** 结尾多一行：判断条件已满足，判断审 OpenSpec 方案、界面文案与直接改动的说明，要启用在 AI 工具中运行 `/rulemason` 并说明要启用判断；不提问
