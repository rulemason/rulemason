## ADDED Requirements

### Requirement: 既有 lint 问题建立基线

补项目信息或日常巡检时，命令表的 ruff 报出问题，skill SHALL 按规则代码统计，给出基线计划，用户确认后照做：可安全自动修复的 `I001`、`F401`（排除 `__init__.py`）给出 `ruff check --fix` 命令与预计数量，确认后才运行；依赖里有 `fastapi` 或 `typer` 时在项目 ruff 配置声明 `extend-immutable-calls`；脚本与命令行入口目录的 `T201` 写进 `per-file-ignores`；其余按文件写进 `per-file-ignores`，原因写「接入前遗留，改到该文件时清掉」。完成后 ruff SHALL 通过。MUST NOT 用 `# noqa`，MUST NOT 改动计划以外的代码。

#### Scenario: 大量既有问题
- **WHEN** 补项目信息时命令表的 ruff 报出 2886 个问题：I001 与 F401 约 1100 个，B008 874 个且依赖里有 `fastapi`，T201 318 个且大多在 `scripts/` 下，其余约 600 个
- **THEN** skill 列出四类各自的数量与做法，以及要写入 ruff 配置的段落原文，等用户确认；确认后照做，再运行 ruff 通过，汇报写明修复前后的问题数

#### Scenario: 用户不同意自动修复
- **WHEN** 用户确认了基线计划，但不同意运行 `ruff check --fix`
- **THEN** I001 与 F401 也按文件写进「接入前遗留」豁免，代码一行不改，ruff 通过

#### Scenario: 没有既有问题
- **WHEN** 命令表的 ruff 没有报出问题
- **THEN** 汇报写「ruff 通过，无需建立基线」，不改 ruff 配置

#### Scenario: 已接入项目在日常巡检时补基线
- **WHEN** 项目信息已补完，日常巡检时命令表的 ruff 报出既有问题
- **THEN** 巡检照常解读 check 结果，并列出基线计划；用户确认后才写入，未确认时不改任何文件

## MODIFIED Requirements

### Requirement: 阶段一接入代码规矩与 gates

阶段一的文件写入 SHALL 由 `rulemason init` 完成（见 `rulekit-cli` 规格）。skill 在 init 之后 SHALL 补项目专属内容：核对并修正 init 预填的项目简介（仍是占位时按 README 与代码写）、经用户确认的红线（init 写的「暂无」也要问用户一次）、对自动识别命令表的确认或修正；`rulemason init` 报告无法安全合并的 `openspec/specs/workflow-gates/spec.md` 也由 skill 合并。skill MUST NOT 修改 rulemason 标记块内的内容，也 MUST NOT 有专门处理旧名的步骤。此时判断层未启用，命令表中判断与文案检查写明「可选，未启用」。

#### Scenario: Python 项目没有 ruff 配置
- **WHEN** 项目有 Python 代码但没有任何 ruff 配置
- **THEN** `rulemason init` 新建一份只含 `extend` 与按需豁免的配置；运行 ruff 后把报出的问题列进汇报，按「既有 lint 问题建立基线」给出基线计划，未经用户确认不修代码

#### Scenario: 命令表待确认
- **WHEN** 命令表带有「自动识别，请确认」标注
- **THEN** skill 向用户展示识别出的命令，按用户确认或修改后的内容写入并去掉标注

#### Scenario: 已有 config.yaml context
- **WHEN** 项目 `openspec/config.yaml` 已有 `context` 段
- **THEN** skill 从中提红线候选，不改动 `context` 本身

#### Scenario: 迁移后处理旧名残留
- **WHEN** 项目的命令表仍写着 `jev-judge --change <name>`，`.gitignore` 放行 `!.claude/skills/rulekit/`
- **THEN** `rulemason check` 不报告这两处，skill 不主动修改；用户要求时按普通的项目文件改动处理

#### Scenario: 简介已由 init 预填
- **WHEN** `AGENTS.md` 的简介是 init 从 README 取的两句话，红线为「暂无」
- **THEN** skill 把简介念给用户核对，只在用户要改时改；红线仍从 README 与 `context` 找候选问一次，没有就保留「暂无」

### Requirement: 已装好的项目只巡检、不改文件

各阶段都已完成的项目，skill SHALL 运行 `rulemason check` 并逐项解读：已选工具入口与生成副本是否缺失或被手改；`.rulemason.yaml` 记录的版本是否落后于已安装版本；`openspec/config.yaml` 的 `rules` 与共享基础版的差异（基础条目缺失或改写才报，追加不报）；ruff 或 ESLint 仍写 `select` 或未继承；判断引擎副本、重复判断规则与重复词表词。巡检 MUST NOT 修改任何文件，唯一的例外是用户确认了「既有 lint 问题建立基线」的计划；未选择的工具不得报为缺失。

#### Scenario: 项目甲巡检
- **WHEN** 在已迁移的项目甲运行
- **THEN** 输出各项检查结果；没有差异的项写「一致」，有差异的列出文件与内容；工作区不出现任何改动

#### Scenario: CI 版本落后
- **WHEN** 项目 `.rulemason.yaml` 记录 `0.6.0`（CI 按此版本安装 rulemason），本机安装的是 `0.6.1`
- **THEN** 巡检报告版本落后，建议运行 `rulemason update` 后在项目跑一遍 lint 与测试

#### Scenario: 巡检时确认建立基线
- **WHEN** 巡检列出 ruff 基线计划，用户确认
- **THEN** 只改计划里的 ruff 配置与用户同意自动修复的文件，其余文件不变
