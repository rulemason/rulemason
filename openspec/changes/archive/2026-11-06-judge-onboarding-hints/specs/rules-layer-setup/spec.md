## MODIFIED Requirements

### Requirement: 阶段一接入代码规矩与 gates

阶段一的文件写入 SHALL 由 `rulemason init` 完成（见 `rulekit-cli` 规格）。skill 在 init 之后 SHALL 补项目专属内容：核对并修正 init 预填的项目简介（仍是占位时按 README 与代码写）、经用户确认的红线（init 写的「暂无」也要问用户一次）、对自动识别命令表的确认或修正；`rulemason init` 报告无法安全合并的 `openspec/specs/workflow-gates/spec.md` 也由 skill 合并。skill MUST NOT 修改 rulemason 标记块内的内容，也 MUST NOT 有专门处理旧名的步骤。此时判断层未启用，命令表中判断与文案检查写明「可选，未启用」。补完时判断条件已满足的，SHALL 在汇报末尾问一次下一步是否整理判断规则，并说明判断只审 OpenSpec 方案与界面文案。

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

#### Scenario: 补完时判断条件已满足
- **WHEN** 项目已归档 60 个 change、本机已有 key、没有 `openspec/judgments.yaml`，接入后还没归档过 change，补项目信息完成
- **THEN** 汇报末尾问一次「下一步要不要整理判断规则」，说明判断只审 OpenSpec 方案与界面文案，并照实说明接入后还没起过 change、启用后暂时用不上；本次不进入整理
