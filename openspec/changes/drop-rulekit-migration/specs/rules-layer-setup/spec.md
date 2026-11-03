## MODIFIED Requirements

### Requirement: 先识别项目再做事

每次运行 SHALL 先运行 `rulemason check --json`，按 `next.code` 决定这次做什么，并把其中的 `text`（报告全文）原样放进汇报。项目没有 `.rulemason.yaml` 时，skill MUST 停下，提示先运行 `rulemason init`，不写任何文件；`.rulekit.yaml` 不再被识别，有它的项目同样按没有清单处理。需要替用户运行 `rulemason init` 时，SHALL 先运行 `rulemason init --plan` 把计划给用户看，用户同意后再运行。本机没有 `rulemason` 命令时 MUST 给出安装命令并停下。

#### Scenario: 纯 Python 项目
- **WHEN** 在已运行过 `rulemason init` 的项目丙根目录运行 `/rulemason`
- **THEN** 汇报原样包含 `rulemason check` 的识别表：Python（两个子目录）、无前端构建、有 openspec、已归档 change 数、无 CI、未提交改动数、已选工具及各层状态

#### Scenario: 没有 openspec
- **WHEN** 在没有 `openspec/` 与 `.rulemason.yaml` 的目录运行 `/rulemason`
- **THEN** 提示先运行 `rulemason init`（它会询问是否代为运行 `openspec init`），skill 不写任何文件

#### Scenario: 尚未 init 的项目
- **WHEN** 在有 `openspec/` 但没有 `.rulemason.yaml` 的项目运行 `/rulemason`
- **THEN** 只输出识别结果与「先运行 rulemason init」，不写任何文件

#### Scenario: 尚未迁移的 rulekit 项目
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `/rulemason`
- **THEN** 与尚未 init 的项目相同：只输出识别结果与「先运行 rulemason init」，不提迁移，不写任何文件

#### Scenario: 本机没装 rulekit
- **WHEN** 在已接入项目运行 `/rulemason`，但 `rulemason` 命令不存在
- **THEN** 给出 `uv tool install` 安装命令并停下

#### Scenario: 用户请 AI 代为接入
- **WHEN** `next.code` 为 `init`，用户说「帮我接入」
- **THEN** skill 先运行 `rulemason init --plan` 给用户看计划，用户同意后再运行 `rulemason init --tools <所选> --yes`

### Requirement: 按安装状态而非归档数决定下一步

skill SHALL 按「补项目信息 → 日常巡检」的顺序找出第一个未完成的阶段，每次运行只做这一个阶段；接入共享规则由 `rulemason init` 完成，不由 skill 写入。「整理判断规则」与「启用判断」是可选功能：用户提出要启用判断时才做，归档数只决定能否启用。做之前 MUST 列出将新增与修改的文件，等用户确认后才写。

#### Scenario: 历史多但未接入
- **WHEN** 项目已归档 5 个 change，但没有 `.rulemason.yaml`
- **THEN** skill 提示先运行 `rulemason init`，不进入整理判断规则或启用判断

#### Scenario: 刚完成 init
- **WHEN** 项目刚运行完 `rulemason init`，`AGENTS.md` 的项目简介与红线仍是待补状态
- **THEN** 本次只补项目简介、红线与命令表确认，不进入整理判断规则或启用判断

#### Scenario: 用户未确认
- **WHEN** skill 列出将改动的文件后用户没有同意
- **THEN** 不写任何文件，汇报停在识别与计划

#### Scenario: 用户要启用判断
- **WHEN** 项目信息已补完、已归档 4 个 change，用户说要启用判断
- **THEN** skill 先整理候选判断规则，用户确认后再启用判断

### Requirement: 阶段一接入代码规矩与 gates

阶段一的文件写入 SHALL 由 `rulemason init` 完成（见 `rulekit-cli` 规格）。skill 在 init 之后 SHALL 补项目专属内容：`AGENTS.md` 中的项目简介、经用户确认的红线、对自动识别命令表的确认或修正；`rulemason init` 报告无法安全合并的 `openspec/specs/workflow-gates/spec.md` 也由 skill 合并。skill MUST NOT 修改 rulemason 标记块内的内容，也 MUST NOT 有专门处理旧名的步骤。此时判断层未装，命令表中判断与文案检查写明「判断层未装」。

#### Scenario: Python 项目没有 ruff 配置
- **WHEN** 项目有 Python 代码但没有任何 ruff 配置
- **THEN** `rulemason init` 新建一份只含 `extend` 与按需豁免的配置；运行 ruff 后把报出的问题列进汇报，不自动修代码

#### Scenario: 命令表待确认
- **WHEN** 命令表带有「自动识别，请确认」标注
- **THEN** skill 向用户展示识别出的命令，按用户确认或修改后的内容写入并去掉标注

#### Scenario: 已有 config.yaml context
- **WHEN** 项目 `openspec/config.yaml` 已有 `context` 段
- **THEN** skill 从中提红线候选，不改动 `context` 本身

#### Scenario: 迁移后处理旧名残留
- **WHEN** 项目的命令表仍写着 `jev-judge --change <name>`，`.gitignore` 放行 `!.claude/skills/rulekit/`
- **THEN** `rulemason check` 不报告这两处，skill 不主动修改；用户要求时按普通的项目文件改动处理
