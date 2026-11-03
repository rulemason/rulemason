## ADDED Requirements

### Requirement: init 预填项目信息

`init` 新建 `AGENTS.md` 时 SHALL 预填项目简介：取项目根 README 第一段正文（跳过标题、徽章与空行），截到两句以内；没有 README 或第一段不是文字时保留「待 /rulemason 补充」占位。红线一节 SHALL 写「暂无」。「本项目样板与豁免」与命令表的「自动识别，请确认」MUST 保留，使 `check` 的下一步仍指向 `/rulemason`。已有的 `AGENTS.md` MUST NOT 被改写简介或红线。

#### Scenario: 有 README 的新项目
- **WHEN** 项目 README 第一段写着「章法是一个给书法爱好者的字帖检索站，按书家与作品浏览单字。它只收录公有领域作品。」
- **THEN** 新建的 `AGENTS.md` 简介为这两句，红线一节为「暂无」，命令表仍带「自动识别，请确认」

#### Scenario: 没有 README
- **WHEN** 项目没有 README 文件
- **THEN** 简介保留「待 /rulemason 补充」占位，红线仍写「暂无」

#### Scenario: 已有 AGENTS.md
- **WHEN** 项目已有自己写的 `AGENTS.md`，简介是一句别的话
- **THEN** init 只补标记块，简介与红线原样保留

### Requirement: init 结尾引导配置 key

交互运行且未带 `--yes` 时，写入完成后：本机没有 key、而项目已满足判断条件（在 git 里且已归档至少 3 个 change）时，`init` SHALL 问一句是否现在配置 Jev 的 key，附申请地址 https://typesafe.ai/ ；回答是则进入与 `rulemason key` 相同的不回显输入，否则提示以后运行 `rulemason key`。条件未满足时 SHALL 只提示一行启用条件。本机已有 key、`--yes`、`--plan` 或非交互运行 MUST NOT 提问。`init` MUST NOT 接受或打印 key。

#### Scenario: 条件满足且没有 key
- **WHEN** 项目已归档 3 个 change、本机没有 key，在终端运行 `rulemason init` 并写入完成
- **THEN** 结尾问「现在配置 Jev 的 key 吗」并附申请地址；回答 y 后进入不回显输入，写入 `~/.config/rulemason/env`

#### Scenario: 条件未满足
- **WHEN** 项目只归档了 1 个 change，本机没有 key
- **THEN** 结尾只提示「判断功能需要至少 3 个已归档 change；满足后运行 rulemason key」，不提问

#### Scenario: 已有 key 或非交互
- **WHEN** 本机已有 key，或运行 `rulemason init --tools claude --yes`
- **THEN** 结尾不出现任何关于 key 的提问

## MODIFIED Requirements

### Requirement: init 预检

`rulemason init [path]` SHALL 按「项目根按最近的 .rulemason.yaml 确定」找项目根；给出 `path` 时以该路径为项目根。不要求 git。没有 git 时 MUST 提示「无法用 diff 查看改动、副本无法通过仓库共享」后继续。没有 `openspec/` 时：交互运行 SHALL 先问是否以同一份工具选择代跑 `openspec init --tools <所选> --language zh-CN`；`--yes`、用户拒绝或本机没有 `openspec` 命令时 SHALL 只接入「读」层（规则副本、入口块、lint 继承），不写方案写法规则、检查点提示与项目检查点规格，结尾写明「检查点与方案写法需要 OpenSpec，装好后运行 rulemason update 补齐」。`init` MUST NOT 识别 rulekit 0.5 的 `.rulekit.yaml`、`.rulekit/` 或 `../rulekit/` 引用。

#### Scenario: 空目录新项目
- **WHEN** 在一个既没有 git 也没有 `openspec/` 的目录运行 `rulemason init`，用户同意运行 openspec init
- **THEN** 先提示没有 git，再运行 `openspec init --tools <所选> --language zh-CN`，之后继续完成 rulemason 接入；`openspec/config.yaml` 的 `context` 含 zh-CN 语言声明

#### Scenario: 本机没有 openspec
- **WHEN** 项目没有 `openspec/`，且 `openspec` 命令不存在
- **THEN** 输出 openspec 的安装方法，只接入「读」层，结尾写明检查点需要 OpenSpec；项目里没有 `openspec/`

#### Scenario: --yes 且没有 openspec
- **WHEN** 在没有 `openspec/` 的项目运行 `rulemason init --tools claude --yes`
- **THEN** 不运行 `openspec init`，只接入「读」层；`.claude/` 下只有 rulemason 的 skill 副本

#### Scenario: 旧接入方式的项目
- **WHEN** 在 `AGENTS.md` 引用 `../rulekit/rules/` 的项目运行 `rulemason init`
- **THEN** 照常接入，不因该引用停止；旧引用留在原处，由用户自行清理

#### Scenario: rulekit 0.5 格式的项目
- **WHEN** 在有 `.rulekit.yaml`、没有 `.rulemason.yaml` 的项目运行 `rulemason init`
- **THEN** 当作尚未接入的项目接入：新生成 `.rulemason/` 与 `.rulemason.yaml`，`.rulekit.yaml` 与 `.rulekit/` 原样保留，计划里不出现它们

### Requirement: init 选择工具并记录版本

`init` SHALL 提供 OpenCode、Claude Code、Cursor、Codex 的多选：终端里用上下键（或 j / k）移动、空格勾选、回车确认、`a` 全选，一个都没选时回车 MUST 提示「至少选一个」；第一次接入默认全不勾，项目里已有某个工具的目录时只在该项旁标注「检测到」；清单已记录工具时预勾记录的工具。标准输入不是终端或平台不支持读单键时 SHALL 退回输入编号的方式。传 `--tools` 时 MUST NOT 提问。选择与 rulemason 版本 SHALL 写入 `.rulemason.yaml`。只为已选工具生成入口；取消某个工具时 SHALL 删除它的入口：skill 副本、`CLAUDE.md` 的 `rulemason:claude` 块（删后文件为空则删除文件）、内容与生成时相同的 `opencode.jsonc`；无法安全删除的 MUST 只报告。

#### Scenario: 非交互选择
- **WHEN** 运行 `rulemason init --tools claude,codex --yes`
- **THEN** 不出现任何提问，`.rulemason.yaml` 记录 `claude`、`codex` 与当前 rulemason 版本

#### Scenario: 第一次用空格勾选
- **WHEN** 项目有 `.claude/` 目录、尚未接入，用户在终端运行 `rulemason init`，按下移、空格、回车
- **THEN** 列表初始一个都没勾，Claude Code 一项旁标注「检测到」；最终只选中用户勾的那一项

#### Scenario: 重跑时预勾已记录的工具
- **WHEN** 清单记录了 `claude`、`codex`，用户在终端运行 `rulemason init` 直接回车
- **THEN** 两项预先勾选，回车后工具选择不变

#### Scenario: 追加工具
- **WHEN** 已接入 Claude Code 的项目再运行 `rulemason init --tools claude,cursor`
- **THEN** 只新增 Cursor 需要的入口，Claude Code 的入口保持不变

#### Scenario: 取消 Claude Code
- **WHEN** 已接入 Claude Code 与 Codex 的项目运行 `rulemason init --tools codex --yes`，`CLAUDE.md` 在 `rulemason:claude` 块外还有项目自己的一段说明
- **THEN** `.claude/skills/rulemason/` 被删除，`CLAUDE.md` 只删去 `rulemason:claude` 块，项目自己的那段说明逐字保留

### Requirement: init 生成项目内只读副本

`init` SHALL 把项目用得上的共享规则正文与 lint 基础配置复制到 `.rulemason/`：`code-style.md` 与 `workflow-gates.md` 必复制；`python.md` 与 `ruff-base.toml` 只在识别到 Python 时；`react.md` 只在识别到 React 目录时；`eslint-base.mjs` 在有 React 目录或已有 ESLint 配置时；`copy-voice.md` 只在有前端目录或判断已启用时。`rulemason` skill 的 `SKILL.md` SHALL 复制到每个已选工具的 skill 发现路径，`.rulemason.yaml` 记录每个生成文件的校验值，副本的有无以清单为准；项目后来出现新语言时由 `update` 补齐。判断层模板 MUST NOT 复制进项目。副本 SHALL 作为项目文件提交，MUST NOT 被手工修改。

#### Scenario: 同事克隆项目
- **WHEN** 同事克隆一个已接入并提交的项目，本机没有装 rulemason
- **THEN** 所选工具能读取 `.rulemason/` 中的规则正文并发现 `/rulemason` skill

#### Scenario: 项目不在 rulekit 的同级目录
- **WHEN** 项目位于任意目录，附近没有 rulemason 仓库
- **THEN** 接入与 ruff 继承照常生效，不出现读取项目外文件的确认

#### Scenario: skill 副本只有一个文件
- **WHEN** 选了 Claude Code 的项目运行 `rulemason init`
- **THEN** `.claude/skills/rulemason/` 下只有 `SKILL.md`，没有 `templates/`

#### Scenario: Go 项目只拿到通用规则
- **WHEN** 只有 `go.mod` 与 `.go` 文件的项目运行 `rulemason init --tools claude --yes`
- **THEN** `.rulemason/` 下只有 `rules/code-style.md`、`rules/workflow-gates.md` 与 `README.md`，没有 `python.md`、`react.md`、`copy-voice.md` 与 `lint/`；`check` 不报缺少副本

#### Scenario: 后来加了 Python
- **WHEN** 上述项目新增 `pyproject.toml` 后运行 `rulemason update`
- **THEN** 补上 `rules/python.md` 与 `lint/ruff-base.toml`，清单记录它们，入口块加上 python.md 的引用

### Requirement: init 补齐配置并识别命令

`init` SHALL 把共享产物写法基础版中缺少的条目补进 `openspec/config.yaml` 的 `rules`，保留 `context` 与项目追加的条目；为项目实际有的语言写 ruff 或 ESLint 继承，指向 `.rulemason/lint/`；项目没有 `openspec/specs/workflow-gates/spec.md` 时按模板创建。命令表只在 `AGENTS.md` 缺少命令表（表头为「名称 / 命令」或英文「Name / Command」）时，按识别到的包管理与测试目录填入，并标注「自动识别，请确认」；判断与文案检查写「可选，未启用」。

#### Scenario: uv 管理的 Python 项目
- **WHEN** 项目有 `pyproject.toml`、`uv.lock` 与 `tests/`，没有 ruff 配置
- **THEN** 新建继承 `.rulemason/lint/ruff-base.toml` 的 ruff 配置，命令表填入 ruff 与 pytest 命令并标注待确认

#### Scenario: 已有 workflow-gates 规格
- **WHEN** 项目已有 `openspec/specs/workflow-gates/spec.md`，但没有 rulemason 的 requirement
- **THEN** init 不修改该文件，在汇报中写明需由 `/rulemason` 合并

#### Scenario: 已有等价的 workflow-gates requirement
- **WHEN** 项目规格里已有以「Apply 后自动精简」开头的 requirement，并引用 `.rulemason/rules/workflow-gates.md`
- **THEN** init 不修改该文件，也不提示合并

#### Scenario: 英文命令表表头
- **WHEN** `AGENTS.md` 已有表头为 `| Name | Command |` 的命令表
- **THEN** init 不再插入自动识别的命令表

### Requirement: init 先列计划，一次确认

交互运行时 `init` SHALL 先显示计划摘要：新增文件按规则副本 / skill / 配置 / 入口计数，修改与删除的文件逐个列出，「需要你处理」逐条列出，再写不会触碰的未提交改动数量，提示 `[y/N/d]`；输入 `d` 展开完整清单后再问一次。`--plan` 与 `--json` SHALL 输出完整清单。`.gitignore` 会挡住生成副本（`.rulemason/` 或 skill 副本）时，放行规则（从被忽略的那一级目录起逐级放行，最后放行副本目录及其下全部文件）SHALL 作为「修改」进计划，与其他改动一起确认。`--yes` 跳过确认。写入后 SHALL 只输出 `check` 的第一行、「需要你处理」清单（ESLint 等配置附可粘贴的代码）与下一步，MUST NOT 打印整份报告。标题、路径与待办 SHALL 用启动画面的配色，设置 `NO_COLOR` 时不输出颜色。`init` MUST NOT 提交、推送或修改计划以外的文件。

#### Scenario: 用户拒绝计划
- **WHEN** init 列出计划后用户回答否
- **THEN** 不写任何文件，退出码为 0

#### Scenario: 有未提交改动
- **WHEN** 项目有 5 个与 rulemason 无关的未提交改动
- **THEN** 计划写明「其余 5 个未提交改动不变」，执行后这 5 个文件逐字不变

#### Scenario: 摘要与展开
- **WHEN** 计划要新增 13 个文件、修改 3 个，用户在提示处输入 `d`
- **THEN** 摘要写「新增 13 个文件：规则副本 5、skill 2、配置 6」并逐个列出 3 个修改；输入 `d` 后打印全部 16 个路径，再次出现 `[y/N/d]`

#### Scenario: 收尾只给结论
- **WHEN** 写入完成，`apps/client-web/eslint.config.js` 的格式无法自动改写
- **THEN** 输出「补项目信息：在 AI 工具中运行 /rulemason」一行、「需要你处理」下该文件及要粘贴的 import 与 rules 代码、下一步；不出现识别表与各层状态

#### Scenario: .gitignore 放行进计划
- **WHEN** 项目 `.gitignore` 写着 `.claude/`，用户选了 Claude Code
- **THEN** 计划的「修改」含 `.gitignore`（追加一行说明与 `!.claude/`、`.claude/*`、`!.claude/skills/`、`.claude/skills/*`、`!.claude/skills/rulemason/`、`!.claude/skills/rulemason/**`），确认后写入，`check` 不再报副本被忽略

### Requirement: check 只读检查并以退出码报告

`rulemason check` SHALL 只读，不要求 git，输出识别表、各层状态、巡检结果与下一步。以下任一情况 MUST 以非 0 退出：已选工具入口缺失、生成副本与 `.rulemason.yaml` 记录的校验值不符、标记块与当前模板不一致、项目在 git 仓库里而生成副本被 `.gitignore` 忽略、ruff 或 ESLint 未继承 `.rulemason/lint/`。记录的版本低于当前安装版本时 SHALL 报告落后，但不单独导致非 0 退出。判断层未启用 MUST NOT 被报告为缺，SHALL 显示「可选，未启用」与启用条件；条件已满足而本机没有 key 时 SHALL 提示运行 `rulemason key` 并附申请地址。没有 `openspec/` 的项目 MUST NOT 因缺方案写法规则与检查点规格而非 0 退出，识别表的 openspec 一行 SHALL 写明方案检查点未启用。巡检 MUST NOT 含「旧接入方式」与「旧名残留」两项。

#### Scenario: CI 中运行
- **WHEN** 项目 CI 安装 rulemason 后运行 `rulemason check`，有人手改了 `.rulemason/` 中的副本
- **THEN** 输出被改的文件，退出码非 0

#### Scenario: 一切一致
- **WHEN** 在刚完成 init 的项目运行 `rulemason check`
- **THEN** 各项写「一致」，退出码为 0

#### Scenario: rulekit 仓库自身
- **WHEN** 在 rulemason 仓库根目录运行 `rulemason check`
- **THEN** 按直接引用 `rules/` 的方式检查，不报告「判断引擎副本」或「缺少 `.rulemason/`」

#### Scenario: 副本被 .gitignore 忽略
- **WHEN** 项目的 `.gitignore` 整体忽略 `.claude/`，已选 Claude Code
- **THEN** `rulemason check` 列出被忽略的 skill 副本，退出码非 0

#### Scenario: 尚未迁移的 rulekit 项目
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason check`
- **THEN** 与没有任何清单的项目相同：第一行提示「接入：运行 rulemason init」，退出码非 0，不提迁移

#### Scenario: 判断层未启用
- **WHEN** 已接入且补完项目信息的项目没有 `openspec/judgments.yaml`，已归档 2 个 change
- **THEN** 判断显示「可选，未启用（需要 git 与至少 3 个已归档 change；还差 1 个）」，不列入缺失，下一步为「日常巡检」，退出码为 0

#### Scenario: 条件满足但没有 key
- **WHEN** 项目已归档 3 个 change、没有 `openspec/judgments.yaml`，本机没有 key
- **THEN** 判断显示「可选，未启用（条件已满足；本机未配置 key：运行 rulemason key，申请地址 https://typesafe.ai/ ）」，退出码不受影响

### Requirement: 不带参数运行显示常用命令

在交互终端不带任何参数运行 `rulemason` SHALL 显示启动画面与常用命令（`init`、`check`、`update`、`key`、`--help`），以 0 退出。非交互环境不带参数运行 MUST 保持原有的用法报错与退出码 2。

#### Scenario: 终端里只敲 rulemason
- **WHEN** 用户在终端运行 `rulemason`
- **THEN** 显示启动画面与常用命令，其中有一行 `rulemason key` 及其说明，退出码 0

#### Scenario: 脚本里不带参数
- **WHEN** 脚本以非交互方式运行 `rulemason`
- **THEN** 打印用法报错，退出码 2
