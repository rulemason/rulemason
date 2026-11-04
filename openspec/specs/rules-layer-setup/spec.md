# rules-layer-setup Specification

## Purpose
规定 `/rulemason` skill 在任一项目根目录运行时如何识别项目、判断已装到哪一层、补上下一层，以及对已装好的项目只做巡检，使新项目接入共享规则不再照手册手抄，已接入项目能发现自己与共享版本的差距。

## Requirements

### Requirement: skill 只住本仓库，任何项目可用

skill 的说明与模板 SHALL 只在本仓库 `skills/rulemason/` 编辑，skill ID 为 `rulemason`。项目里的 skill 是由 `rulemason init` 或 `rulemason update` 生成到已选工具发现路径的副本，随项目提交；副本 MUST NOT 被手工修改，`rulemason check` SHALL 报告与记录校验值不符的副本。

#### Scenario: 修改 skill
- **WHEN** skill 的某一步需要调整
- **THEN** 只改本仓库 `skills/rulemason/`，发布新版本后各项目运行 `rulemason update` 即用上新版本

#### Scenario: 副本被手改
- **WHEN** 有人直接修改了项目 `.claude/skills/rulemason/SKILL.md`
- **THEN** `rulemason check` 报告该文件与记录不符，`rulemason update` 将其恢复

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

### Requirement: 阶段一同步项目工作流规格

项目 `openspec/specs/workflow-gates/spec.md` SHALL 声明 apply 后自动精简与独立只读代码审查，并引用 `.rulemason/rules/workflow-gates.md`。文件不存在时由 `rulemason init` 按模板创建；文件已存在但缺少该 requirement 时由 skill 合并，MUST NOT 复制共享检查点正文，MUST 保留现有项目 requirements 与 scenarios，已有等价 requirement 时 MUST NOT 重复添加。写入 MUST 纳入文件计划并在用户确认后进行；无法安全合并时 MUST 停止并报告。

#### Scenario: 新项目尚无 workflow-gates 规格
- **WHEN** 首次运行 `rulemason init`，项目没有 `openspec/specs/workflow-gates/spec.md`
- **THEN** init 文件计划列出新建该规格，确认后创建，并引用 `.rulemason/rules/workflow-gates.md`

#### Scenario: 项目已有 workflow-gates 规格
- **WHEN** 项目已有该规格且含项目自有 requirements，但没有自动精简/审查 requirement
- **THEN** init 不修改该文件；skill 只合并缺少的 requirement，保留其余内容

#### Scenario: 已完整接入项目运行巡检
- **WHEN** 项目所有接入阶段已完成，rulemason 只执行只读巡检
- **THEN** 不自动修改 `openspec/specs/workflow-gates/spec.md`

### Requirement: 红线由人确认，skill 不代写

skill 提出的红线与判断规则候选 SHALL 注明出处（项目 README、`openspec/config.yaml` 的 `context`、或某个已归档方案），写入项目通用指令入口或 `judgments.yaml` 前 MUST 逐条请用户确认或改写；用户没有确认的候选 MUST NOT 写入。

#### Scenario: 从 context 提候选
- **WHEN** 项目丙的 `config.yaml` context 写着「无注册/登录/UGC」
- **THEN** skill 把它列为红线候选，等用户确认后才写进项目指令

### Requirement: 阶段二整理候选判断规则

阶段一完成、判断层未装时，SHALL 读已归档 change 的 proposal 与 design，整理反复出现、且能指回已写下规矩的问题，作为候选判断规则列在汇报里（规则 id、要问的一句话、enforces 指向哪条规矩、出现在哪几个 change）。已归档不足 3 个时 MUST 说明还不能装判断层，并在汇报里写明还差几个。

#### Scenario: 归档不足
- **WHEN** 项目只归档了 2 个 change
- **THEN** 汇报写明「判断层需至少 3 个已归档 change 作测试用例，还差 1 个」，不生成 `judgments.yaml`

### Requirement: 阶段三安装判断层

已归档至少 3 个 change、且用户确认了至少一条项目判断规则时，SHALL 产出：只含用户确认规则的 `openspec/judgments.yaml`（通用三条由引擎自带，不写入）；`openspec/judge.yaml`（项目有界面文案才写 `copy` 段）；`tests/judge_cases.yaml` 骨架；命令表的判断与文案检查改为 `rulemason judge --change <name>` 与 `rulemason judge --copy`。三份文件的模板 SHALL 用 `rulemason judge --template <名称>` 从安装包取得。项目不在 git 仓库时 MUST 说明判断层需要 git 并停在本阶段。缺 `rulemason` 命令时 MUST 给出安装步骤；没有 key（`~/.config/rulemason/env` 与旧位置 `~/.config/jev-judge/env` 都没有）时 SHALL 提示用户在终端运行 `rulemason key`，MUST NOT 代填 key。

#### Scenario: 没有 key
- **WHEN** 本机既没有 `~/.config/rulemason/env` 也没有 `~/.config/jev-judge/env`
- **THEN** 汇报提示在终端运行 `rulemason key`，判断层文件照常生成，`rulemason judge` 以人工模式运行验证

#### Scenario: 项目没有 git
- **WHEN** 归档已满 3 个，但项目目录不是 git 仓库
- **THEN** skill 说明判断层需要 git（文案检查要与主分支比较），不生成判断层文件

#### Scenario: 从安装包取模板
- **WHEN** skill 生成 `openspec/judgments.yaml`
- **THEN** 以 `rulemason judge --template judgments` 的输出为起点，项目里没有模板副本

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

### Requirement: 不提交、不碰用户未提交的改动

`rulemason init`、`rulemason update` 与 skill 都 MUST NOT 执行 git 提交或推送。工作区有用户未提交改动时，只新增、修改或删除本次文件计划中的文件，汇报末尾列出改了哪些文件，由用户或 gates 决定如何提交。

#### Scenario: 项目丙有 28 个未提交改动
- **WHEN** 在有 28 个未提交改动的项目丙运行 `rulemason init`
- **THEN** 只写文件计划中的文件，其余 28 个文件保持原样，汇报列出本次改动的文件

### Requirement: 每次运行以汇报结束

`rulemason init` 与 skill 每次运行 SHALL 以一份汇报结束，包含识别结果、已选择工具、本次阶段或巡检结果、验证命令与结果、改动文件清单、未触碰的用户改动及下一步建议。

#### Scenario: 阶段一完成
- **WHEN** `rulemason init` 写完
- **THEN** 汇报包含 `rulemason check` 的结果、改动文件清单，最后一行提示在 AI 工具中运行 `/rulemason` 补项目专属内容

### Requirement: 每个项目交互选择 agent 工具

工具选择 SHALL 由 `rulemason init` 提供按项目保存的交互式多选，至少支持 OpenCode、Claude Code、Cursor、Codex，记录在 `.rulemason.yaml`。只为已选工具生成和巡检入口；共享规则与 skill 只在 rulemason 仓库编辑，项目内为生成副本。

#### Scenario: 首次选择多个工具
- **WHEN** 用户在 `rulemason init` 中选择 OpenCode 与 Codex
- **THEN** 项目记录这两项选择，只生成两者需要的入口，且两者读取相同的共享规则与 skill 副本

#### Scenario: 后续调整选择
- **WHEN** 用户重跑 `rulemason init --tools` 新增 Cursor 或移除一个工具
- **THEN** 先列出受影响文件并等待确认，只调整对应入口，不覆盖标记块以外的用户内容

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
