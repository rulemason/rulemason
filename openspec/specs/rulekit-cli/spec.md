# rulekit-cli Specification

## Purpose

规定 `rulemason` 命令行如何一次安装、在任一项目目录用 `init` 接入共享规则、用 `update` 升级、用 `check` 只读检查，使新项目像使用 OpenSpec 一样一条命令完成接入，接入结果可在任何机器、云端 agent 与 CI 中复现。

## Requirements

### Requirement: 一条命令安装

`rulemason` 命令 SHALL 由 PyPI 上名为 `rulemason` 的包提供，判断引擎作为它的子命令 `rulemason judge` 随包安装，不再提供单独的 `jev-judge` 命令。用户 SHALL 能用一条 `uv tool install rulemason` 装好，不需要克隆 rulemason 仓库，也不需要建任何符号链接。包的版本号 MUST 与发布 tag 一致。Jev 的 key MUST NOT 由安装或任何子命令代填。

#### Scenario: 新机器安装
- **WHEN** 用户在一台从未用过 rulemason 的机器上执行 `uv tool install rulemason`
- **THEN** `rulemason --version` 与 `rulemason judge --help` 都可运行，版本号等于 PyPI 上的最新版本

#### Scenario: 没有 key
- **WHEN** 安装完成但 `~/.config/rulemason/env` 与 `~/.config/jev-judge/env` 都不存在
- **THEN** 不创建任何 key 文件；`rulemason judge` 按现有规则走人工模式

#### Scenario: 旧命令不再提供
- **WHEN** 安装 rulemason 后在新环境运行 `jev-judge`
- **THEN** 命令不存在；判断引擎只通过 `rulemason judge` 使用

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

### Requirement: init 只写 rulekit 标记块

`init` 与 `update` 在 `AGENTS.md`、`CLAUDE.md` 等用户也会编辑的文件中，SHALL 只写 rulemason 标记块（`<!-- rulemason:NAME -->` 与 `<!-- /rulemason:NAME -->` 之间）内的内容；标记块以外的内容 MUST NOT 被修改。`AGENTS.md` SHALL 保留 `## Code style` 与 `## Workflow gates` 标题，并在标记块内引用 `.rulemason/rules/` 下的副本。选了 Claude Code 时，`CLAUDE.md` 的标记块 SHALL 导入 `AGENTS.md` 与适用的共享正文副本，使会话开始即加载九条。该标记块还 SHALL 写明 Claude Code 下自动精简一步使用 `/simplify` 的映射（调用条件、只采纳行为保持的修改、不可用时退回手工精简）；其他工具的入口不写这条映射。

#### Scenario: 已有 AGENTS.md
- **WHEN** 项目已有自写的 `AGENTS.md`，没有 rulemason 标记块
- **THEN** init 只插入标记块，原有各段文字逐字不变

#### Scenario: Claude Code 会话
- **WHEN** 在已接入且选了 Claude Code 的项目开始 Claude Code 会话
- **THEN** 会话上下文包含九条与 workflow-gates 正文，不需要 AI 再去读取文件

#### Scenario: Claude Code 入口带精简映射
- **WHEN** 选了 Claude Code 的项目运行 `rulemason init` 或 `rulemason update`
- **THEN** `CLAUDE.md` 的 `rulemason:claude` 块包含导入与 `/simplify` 映射说明，`AGENTS.md` 与 OpenCode instructions 中不出现 `/simplify`

### Requirement: init 补齐配置并识别命令

`init` SHALL 把共享产物写法基础版中缺少的条目补进 `openspec/config.yaml` 的 `rules`，保留 `context` 与项目追加的条目；为项目实际有的语言写 ruff 或 ESLint 继承，指向 `.rulemason/lint/`（ESLint 认 `export default [`、`export default defineConfig([`、`export default tseslint.config(` 三种写法；已有引用指向不存在或项目外的同名基础配置时改正该路径，不另加引入；新建的 ruff 配置在只有一个 Python 目录且 Python 文件都在其中时放进该目录）；项目没有 `openspec/specs/workflow-gates/spec.md` 时按模板创建。命令表只在 `AGENTS.md` 缺少命令表（表头为「名称 / 命令」或英文「Name / Command」）时，按识别到的包管理与测试目录填入，并标注「自动识别，请确认」；判断与文案检查写「可选，未启用」。

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

#### Scenario: defineConfig 写法的 ESLint 配置
- **WHEN** `web/eslint.config.js` 写 `export default defineConfig([`，没有引入基础规则
- **THEN** init 计划在该文件加入 `import rulemasonBase from "../.rulemason/lint/eslint-base.mjs"` 与数组第一项 `{ rules: rulemasonBase }`，不报「格式无法自动识别」

#### Scenario: tseslint.config 写法的 ESLint 配置
- **WHEN** ESLint 配置写 `export default tseslint.config(`
- **THEN** init 计划把 `{ rules: rulemasonBase }` 作为第一个参数加入，并加上引入

#### Scenario: 引用指向不存在的基础配置
- **WHEN** `apps/admin-web/eslint.config.js` 从 `../../../.rulekit/lint/eslint-base.mjs` 引入，该文件不存在
- **THEN** init 计划把这条路径改为 `../../.rulemason/lint/eslint-base.mjs`，文件里只保留一条基础规则引入

#### Scenario: 唯一的 Python 目录
- **WHEN** 项目的 Python 文件都在 `apps/api/`（有 `pyproject.toml`、没有 ruff 配置），项目根没有 Python 文件
- **THEN** init 新建 `apps/api/ruff.toml`，继承 `../../.rulemason/lint/ruff-base.toml`，项目根不出现 `ruff.toml`

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

### Requirement: init 可重复运行，冲突只报告

对已接入且未改动的项目重复运行 `init` SHALL 不产生任何文件改动。遇到无法安全写入的情况（ruff 配置仍写 `select`、无法识别的 ESLint 配置格式、标记块不成对），`init` MUST 跳过该文件并在汇报中说明，不强行改写。`CLAUDE.md` 还没有 `rulemason:claude` 块、`@AGENTS.md` 在全文只出现一次且顶格独占一行（不在代码块里）时，`init` 与 `update` SHALL 用新块替换这一行，不算冲突；其他写法的块外导入（如 `@./AGENTS.md`、缩进或夹在文字里）MUST NOT 修改，照旧报重复导入。

#### Scenario: 第二次运行
- **WHEN** init 成功后立即再次运行 `rulemason init --yes`
- **THEN** 汇报「没有需要改动的文件」，工作区无变化

#### Scenario: ruff 配置写了 select
- **WHEN** 项目 `pyproject.toml` 的 `[tool.ruff.lint]` 写了 `select`
- **THEN** init 不改该文件，汇报写明 `select` 所在的行号与原文、会覆盖基础规则，并给出改为 `extend-select` 或删去该行两种做法，由用户处理

#### Scenario: 卸载后再接入的 CLAUDE.md
- **WHEN** 项目运行过 `rulemason remove`，`CLAUDE.md` 是「`@AGENTS.md`」一行加一段项目自己的说明，之后运行 `rulemason init --tools claude --yes`
- **THEN** 那一行被 `rulemason:claude` 块替换，块内第一行是 `@AGENTS.md`，全文只导入一次 `AGENTS.md`，项目自己的说明逐字不变，「需要你处理」里没有重复导入

#### Scenario: 块外导入写法不同
- **WHEN** `CLAUDE.md` 块外写的是 `@./AGENTS.md`，没有 `rulemason:claude` 块，运行 `rulemason init --tools claude --yes`
- **THEN** 新块照常写入，`@./AGENTS.md` 那一行不变，汇报报出块外重复导入，请用户删去块外那一行

#### Scenario: 代码块里的示例
- **WHEN** `CLAUDE.md` 只在 ``` 代码块里写了一行 `@AGENTS.md` 作为示例，运行 `rulemason init --tools claude --yes`
- **THEN** 代码块逐字不变，新块加在文末，不报重复导入（代码块里的导入不生效）

### Requirement: update 刷新副本

`rulemason update` SHALL 用当前安装的版本刷新 rulemason 自己管的文件（`.rulemason/` 副本、skill 副本、已有的标记块与 `.rulemason.yaml`），MUST NOT 提问选工具。缺的配置（ruff / ESLint 继承、基础 rules、workflow-gates 规格、缺的标记块）SHALL 按 `init` 的规则补齐：先列计划，交互确认或带 `--yes` 才写；非交互且没有 `--yes` 时 MUST NOT 修改，只列为「待补齐」。`update` SHALL 删除清单记录过、不再生成且未改的旧副本，改过的只报告；被手改的副本与块 SHALL 列出。`update` MUST NOT 修改标记块以外的命令表、红线或判断层文件。项目没有 `openspec/` 时，`update` 结尾 SHALL 写明方案检查点未启用及补齐方法。

#### Scenario: 升级共享规则
- **WHEN** 用户升级到 rulemason 新版本后在项目运行 `rulemason update`
- **THEN** `.rulemason/rules/` 与 skill 副本变为新版本内容，`.rulemason.yaml` 记录新版本，`AGENTS.md` 标记块以外的内容不变

#### Scenario: 副本被手改
- **WHEN** 有人手改了 `.rulemason/rules/code-style.md` 后运行 update
- **THEN** 该文件恢复为共享版本，汇报列出它被覆盖

#### Scenario: 旧格式项目运行 update
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason update`
- **THEN** 与没有任何清单的项目相同：报告「先运行 rulemason init」并以非 0 退出，不写任何文件，不提迁移

#### Scenario: 补齐缺的 ruff 继承
- **WHEN** 已接入项目新加了 Python 代码、还没有 ruff 配置，运行 `rulemason update --yes`
- **THEN** 新建继承 `.rulemason/lint/ruff-base.toml` 的 ruff 配置，汇报列出该文件

#### Scenario: 非交互且没有 --yes
- **WHEN** 同样的项目在非交互环境运行 `rulemason update`
- **THEN** 副本照常刷新，ruff 配置不写，汇报列出「待补齐」及运行 `rulemason update --yes`

#### Scenario: 清理旧模板副本
- **WHEN** 从 0.6.x 升级的项目有 `.claude/skills/rulemason/templates/` 下未改动的 3 个模板副本，运行 `rulemason update`
- **THEN** 这 3 个文件与空目录被删除，`.rulemason.yaml` 不再记录它们

#### Scenario: 没有 OpenSpec 的项目运行 update
- **WHEN** 项目没有 `openspec/`，运行 `rulemason update`
- **THEN** 输出最后写明「方案检查点未启用：安装 OpenSpec 并 openspec init 后再运行 rulemason update」，退出码为 0

### Requirement: check 只读检查并以退出码报告

`rulemason check` SHALL 只读，不要求 git，输出识别表、各层状态、巡检结果与下一步。以下任一情况 MUST 以非 0 退出：已选工具入口缺失、生成副本与 `.rulemason.yaml` 记录的校验值不符、标记块与当前模板不一致、项目在 git 仓库里而生成副本被 `.gitignore` 忽略、ruff 或 ESLint 未继承 `.rulemason/lint/` 或引用的基础配置不存在、本机版本应生成的副本与清单记录不一致。只有版本号落后、副本内容相同时 SHALL 报告，MUST NOT 因此非 0 退出。判断层未启用 MUST NOT 被报告为缺，SHALL 显示「可选，未启用」与启用条件；条件已满足而本机没有 key 时 SHALL 提示运行 `rulemason key` 并附申请地址。没有 `openspec/` 的项目 MUST NOT 因缺方案写法规则与检查点规格而非 0 退出，识别表的 openspec 一行 SHALL 写明方案检查点未启用。巡检 MUST NOT 含「旧接入方式」与「旧名残留」两项。

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

#### Scenario: 副本内容落后
- **WHEN** 项目记录 0.8.4，本机 0.8.5 改了 `rules/code-style.md`，项目未运行 update
- **THEN** 生成副本一层列出「副本与本机版本应生成的不一致」，退出码非 0

#### Scenario: 启用判断后副本要补文案语气
- **WHEN** 版本未变，项目新增 `openspec/judgments.yaml`，清单里没有 `copy-voice.md` 副本
- **THEN** 生成副本一层列出「副本与本机版本应生成的不一致」，下一步为 `rulemason update`

#### Scenario: 只有版本号落后
- **WHEN** 项目记录 0.8.4，本机 0.8.5 生成的副本与记录的校验值完全相同
- **THEN** 退出码为 0，第一行附一句版本号落后、副本内容相同

#### Scenario: lint 引用的文件不存在
- **WHEN** ESLint 配置引用的 `eslint-base.mjs` 路径不存在
- **THEN** lint 继承一层单独列出「引用的基础配置不存在」及该路径，退出码非 0

### Requirement: 项目根按最近的 .rulemason.yaml 确定

`rulemason init`、`update`、`check` SHALL 从当前目录往上找最近的 `.rulemason.yaml`，以它所在目录为项目根；向上查找 MUST NOT 越过当前目录所在 git 仓库的根目录。找不到时，`init` SHALL 以所在 git 仓库的根为项目根，不在 git 里则以当前目录为项目根；`check` 与 `update` SHALL 报告「先运行 rulemason init」并写明判断出的项目根。`rulemason init <path>` 显式给出路径时 SHALL 以该路径为项目根，不再向上查找。

#### Scenario: 在已接入项目的子目录运行
- **WHEN** 在已接入项目的 `app/` 子目录运行 `rulemason check`
- **THEN** 以项目根目录检查，结果与在项目根运行相同，不提示「先运行 rulemason init」

#### Scenario: 在子目录运行 init
- **WHEN** 在一个尚未接入的 git 仓库的 `web/src/` 目录运行 `rulemason init --tools claude --yes`
- **THEN** 在仓库根目录接入，`web/src/` 下不出现 `.rulemason.yaml` 或 `.rulemason/`

#### Scenario: 工作区里的独立仓库
- **WHEN** 工作区根目录已接入（有 `.rulemason.yaml`），在其中一个独立 git 仓库 `app-a/` 里运行 `rulemason check`
- **THEN** 不向上找到工作区的 `.rulemason.yaml`，报告 `app-a/` 尚未接入，提示「先运行 rulemason init」

#### Scenario: 显式给出路径
- **WHEN** 运行 `rulemason init packages/web --tools claude --yes`
- **THEN** 以 `packages/web/` 为项目根接入，不向上查找

### Requirement: 子仓库、子项目与第三方目录不属于本项目

列项目文件时，以下子目录 SHALL 视为不属于本项目、整个跳过：含 `.git` 的子目录（另一个 git 仓库，含子模块）、含 `.rulemason.yaml` 的子目录（另一个 rulemason 项目）、名为 `bower_components`、`uni_modules`、`third_party`、`jspm_packages`、`Pods` 的目录，以及含 Composer 的 `autoload.php` 或 Go 的 `modules.txt` 的 `vendor` 目录（第三方代码；没有这些标记的 `vendor` 属于项目自己）。项目在 git 仓库里与不在 git 仓库里时，跳过的结果 MUST 相同。`openspec/changes/` 下的方案草稿与原型 SHALL 静默跳过，不列入「跳过」。被跳过的目录 MUST NOT 参与语言与包管理识别、lint 继承与判断引擎副本的检查，也 MUST NOT 被 `init` 或 `update` 写入。

#### Scenario: 多仓库工作区
- **WHEN** 工作区根目录没有 git、已接入，下面有 3 个独立 git 仓库，各自有 ruff 或 ESLint 配置
- **THEN** check 不要求这 3 个仓库的配置继承基础规则，识别表「跳过」一行列出它们为「另一个仓库」，lint 继承不因它们报缺

#### Scenario: 第三方目录里的 lint 配置
- **WHEN** 项目里有 `static/bower_components/jquery/src/.eslintrc.json`
- **THEN** check 不报它没有引入基础规则，识别表列出 `static/bower_components` 为「第三方目录」，前端目录里也不出现它

#### Scenario: 项目自己的 vendor 目录
- **WHEN** 项目的 `frontend/vendor/` 里只有自己的图片与脚本，没有 `autoload.php` 或 `modules.txt`
- **THEN** 它照常属于本项目，不出现在「跳过」里

#### Scenario: 仓库里的子项目
- **WHEN** 已接入仓库的 `packages/web/` 自己有 `.rulemason.yaml`
- **THEN** 在仓库根运行 check 时不检查 `packages/web/` 下的文件，识别表列出它为「另一个 rulemason 项目」

#### Scenario: 有没有 git 结果一致
- **WHEN** 同一个目录结构（没有被 `.gitignore` 忽略的文件）分别在 git 仓库里与不在 git 仓库里运行 check
- **THEN** 两次的「跳过」一行相同

#### Scenario: 方案里的原型
- **WHEN** `openspec/changes/add-x/prototype/package.json` 依赖 react，没有 ESLint 配置
- **THEN** 前端目录与「React 目录缺少 ESLint」都不出现它，「跳过」一行也不列它

### Requirement: 识别表列出被跳过的目录

`check` 的识别表 SHALL 用「项目根」一行写明判断出的项目根，用「跳过」一行列出被跳过的目录与原因（另一个仓库、另一个 rulemason 项目、第三方目录）；多于 10 个时 SHALL 只列前 10 个并写明总数，没有时写「—」。被跳过的目录 MUST NOT 被报告为「缺」。

#### Scenario: 跳过的目录很多
- **WHEN** 工作区下有 12 个独立仓库
- **THEN** 「跳过」一行列出前 10 个，并写「等共 12 个」

#### Scenario: 没有跳过的目录
- **WHEN** 一个仓库一个项目、没有子仓库与第三方目录
- **THEN** 「跳过」一行写「—」

### Requirement: check 第一行给结论与下一步

`rulemason check` 输出的第一行 SHALL 是结论与下一步要做的事，下一步 SHALL 按原因给出具体命令或动作，同时有多个原因时按以下顺序取第一个：清单无效 → 先修正清单；尚未接入 → `rulemason init`；生成副本被 `.gitignore` 忽略 → 修改 `.gitignore` 放行 `skills/rulemason/`；副本或标记块与模板不一致、副本与本机应生成的不一致、入口缺失、配置待补齐 → `rulemason update`；接入只剩 update 改不了的 lint 项 → 第一行写明手动修改的文件，具体行号、原文与做法写在报告里；项目信息待补 → `/rulemason`。只有版本号落后时第一行 SHALL 附一句，不改变下一步。阶段名 SHALL 使用：接入、补项目信息、日常巡检；判断相关为可选的「整理判断规则」「启用判断」。`next.code` MUST NOT 再出现 `legacy`、`migrate`、`fix_residue`。

#### Scenario: 刚接入的项目
- **WHEN** 刚运行完 `rulemason init`，项目简介与红线待补
- **THEN** 第一行写「补项目信息：在 AI 工具中运行 /rulemason」

#### Scenario: 副本被忽略
- **WHEN** skill 副本被 `.gitignore` 忽略
- **THEN** 第一行的下一步是修改 `.gitignore` 放行 `skills/rulemason/`，而不是 `rulemason update`

#### Scenario: 一切就绪
- **WHEN** 项目接入完整、项目信息已补、没有任何偏离
- **THEN** 第一行写「日常巡检：一切一致」，退出码为 0

#### Scenario: 只剩手动 lint 项
- **WHEN** 接入只剩 `apps/client-web/eslint.config.js` 一项，其写法 update 无法自动改
- **THEN** 第一行写「接入：手动修改 apps/client-web/eslint.config.js」，报告的「接入 lint 继承」下列出要加的引入与数组项，第一行不写「运行 rulemason update」

#### Scenario: 能沿继承链补齐时不算手动项
- **WHEN** 接入只剩 `ruff.toml` 继承项目内 `config/ruff-shared.toml`、末端尚未接上基础配置
- **THEN** 第一行的下一步是「运行 rulemason update」

#### Scenario: 只有版本号落后
- **WHEN** 项目一切一致，记录 0.8.4，本机 0.8.5 生成的副本内容相同
- **THEN** 第一行写「日常巡检：一切一致」并附「版本号落后（0.8.4 → 0.8.5），副本内容相同」

### Requirement: check 校验标记块内容

`.rulemason.yaml` 记录的版本与本机安装版本相同时，`rulemason check` SHALL 把 `AGENTS.md`、`CLAUDE.md` 中各 rulemason 标记块的内容与当前模板生成的内容比较；不同即报告「与当前模板不一致」（被手改，或项目新增了语言），SHALL 列出文件与块名并以非 0 退出。版本不同时 MUST NOT 报告为手改，由「版本落后」说明。`rulemason update` 恢复被手改的块时 SHALL 在汇报中列出。

#### Scenario: 手改了 code-style 块
- **WHEN** 版本一致的项目里，有人改了 `AGENTS.md` 中 `rulemason:code-style` 块的一行
- **THEN** check 报告 `AGENTS.md` 的 `code-style` 块与当前模板不一致，退出码非 0；运行 `rulemason update` 后该块恢复，汇报列出它被覆盖

#### Scenario: 升级后块内容变化
- **WHEN** 项目记录 0.6.1、本机是更新的版本，块内容与新模板不同
- **THEN** check 只报告版本落后，不报告块被手改

### Requirement: rulemason key 配置 Jev 的 key

`rulemason key` SHALL 交互提示输入 key，输入不回显；写入 `~/.config/rulemason/env` 的 `TYPESAFE_API_KEY` 一行，保留文件里的其他设置；目录权限 SHALL 为 700、文件为 600。命令 MUST NOT 接受从命令行参数或标准输入管道传入 key；非交互环境 SHALL 报错退出并说明需在终端里运行。写入后 SHALL 写明文件位置，MUST NOT 打印 key。

#### Scenario: 第一次配置
- **WHEN** 本机没有 `~/.config/rulemason/env`，在终端运行 `rulemason key` 并输入 key
- **THEN** 生成该文件（权限 600，目录 700），内容含 `TYPESAFE_API_KEY=<输入的值>`，屏幕上不出现 key

#### Scenario: 更新已有的 key
- **WHEN** 文件里已有 `TYPESAFE_API_KEY=旧值` 与 `JUDGE_PROVIDER=jev`
- **THEN** 只替换 `TYPESAFE_API_KEY` 一行，`JUDGE_PROVIDER=jev` 保留

#### Scenario: 非交互运行
- **WHEN** 在没有终端的环境（如 AI 工具或 CI）运行 `rulemason key`
- **THEN** 不写任何文件，提示在终端里运行，退出码非 0

### Requirement: check --json 输出结构化结果

`rulemason check --json` SHALL 向标准输出写一个 JSON 对象，不输出其他文字，退出码与文字版相同。对象 SHALL 含：`schema`（格式版本，当前为 1）、`root`（项目根）、`next`（`stage` 阶段名、`action` 下一步文字、`code` 稳定的动作代码）、`facts`（识别表，名称到值）、`layers`（各层名称到缺失项列表）、`findings`（巡检名称到偏离列表）、`exit_code`、`text`（与文字版完全相同的报告全文）。`code` SHALL 取以下之一：`legacy`、`fix_manifest`、`migrate`、`init`、`fix_gitignore`、`fix_residue`、`update`、`fill_project_info`、`upgrade_machine`、`upgrade_copies`、`none`。键名 MUST 为英文；值沿用文字版的中文。

#### Scenario: 刚接入的项目
- **WHEN** 在刚完成 `rulemason init` 的项目运行 `rulemason check --json`
- **THEN** 输出可被 JSON 解析，`next` 为 `{"stage": "补项目信息", "action": "在 AI 工具中运行 /rulemason", "code": "fill_project_info"}`，`exit_code` 为 0，`text` 与 `rulemason check` 的输出相同

#### Scenario: 副本被忽略
- **WHEN** skill 副本被 `.gitignore` 忽略，运行 `rulemason check --json`
- **THEN** `next.code` 为 `fix_gitignore`，退出码与 `exit_code` 都非 0

### Requirement: init --plan 只列计划不写入

`rulemason init --plan` SHALL 按 `init` 的同一套规则算出文件计划（含取消工具的删除、补齐配置），打印后以 0 退出；MUST NOT 写入或删除任何文件、MUST NOT 提问、MUST NOT 运行 `openspec init`，在非交互环境也可运行。没带 `--tools` 时 SHALL 用清单记录的工具，没有清单则按项目已有的工具目录推断。项目没有 `openspec/` 时，计划 SHALL 写明「将先运行 openspec init」。预检不通过时 SHALL 照常报告并以对应的非 0 退出码退出。

#### Scenario: AI 会话里先看计划
- **WHEN** 在非交互环境、尚未接入的项目运行 `rulemason init --plan`
- **THEN** 打印将新增的文件清单，退出码为 0，项目中没有任何文件变化

#### Scenario: 迁移计划的 JSON
- **WHEN** 在只有 `.rulekit.yaml` 的项目运行 `rulemason init --plan --json`
- **THEN** 与尚未接入的项目相同：`writes` 含 `.rulemason.yaml`，`deletes` 为空、不含 `.rulekit.yaml` 或旧副本，项目中没有任何文件变化

#### Scenario: 没有 openspec
- **WHEN** 在没有 `openspec/` 的目录运行 `rulemason init --plan --json`
- **THEN** `openspec_init` 为 true，不运行 openspec，不创建 `openspec/`

### Requirement: init --plan --json 的字段

`rulemason init --plan --json` SHALL 只输出一个 JSON 对象，含 `root`、`tools`、`writes`（每项 `path` 与 `action`：`add` 或 `modify`）、`deletes`、`overwritten`、`notes`、`untouched_dirty`（不会碰的未提交改动数，没有 git 时为 null）、`openspec_init`（是否需要先运行 openspec init）。`init` 带 `--json` 而不带 `--plan` 时 SHALL 报错退出，MUST NOT 写入任何文件。

#### Scenario: --json 不配 --plan
- **WHEN** 运行 `rulemason init --json` 或 `rulemason update --json`
- **THEN** 报错提示应配合 `--plan` / `--dry-run`，以非 0 退出，项目中没有任何文件变化

#### Scenario: 新增与修改区分
- **WHEN** 项目已有 `AGENTS.md`、还没有 `.rulemason/`，运行 `rulemason init --plan --json`
- **THEN** `AGENTS.md` 的 `action` 为 `modify`，`.rulemason/rules/code-style.md` 的 `action` 为 `add`

### Requirement: update --dry-run 只列计划不写入

`rulemason update --dry-run` SHALL 算出管理计划与补齐计划并打印，以 0 退出，MUST NOT 写入或删除任何文件、MUST NOT 提问。加 `--json` 时 SHALL 输出 JSON 对象，含 `root`、`managed`（`writes`、`deletes`、`overwritten`）、`fill`（补齐计划要写的文件）、`notes`。预检不通过（没有清单、仍是 rulekit 0.5 格式等）时 SHALL 照常报告并以非 0 退出。`update` 带 `--json` 而不带 `--dry-run` 时 SHALL 报错退出，MUST NOT 写入任何文件。

#### Scenario: 升级前先看
- **WHEN** 清单版本落后、缺 ruff 配置的项目运行 `rulemason update --dry-run --json`
- **THEN** `managed.writes` 含要刷新的副本与清单，`fill` 含 ruff 配置，项目中没有任何文件变化

### Requirement: 补齐 OpenSpec operations 提示

`init` 与 `update` 的补齐计划 SHALL 在项目 `openspec/config.yaml` 没有 `operations` 段时，把 `operations` 基础版追加到文末，其余内容逐字保留；已有 `operations` 段时 MUST NOT 修改它。`rulemason check` SHALL 在巡检「检查点提示与基础版的差异」中列出缺少的段或基础条目，MUST NOT 因此以非 0 退出。rulemason 源码仓库中条目引用 `rules/workflow-gates.md`，其他项目引用 `.rulemason/rules/workflow-gates.md`。

#### Scenario: 新接入
- **WHEN** 在 `openspec/config.yaml` 没有 `operations` 的项目运行 `rulemason init --tools claude --yes`
- **THEN** config.yaml 文末多出 `operations.apply.guidance` 与 `operations.archive.guidance`，`context` 与 `rules` 不变，`openspec instructions apply` 的 `operationGuidance` 含这些条目

#### Scenario: 已有 operations
- **WHEN** 项目 config.yaml 已有自己写的 `operations.apply.guidance`，缺少基础条目
- **THEN** `init` 与 `update` 不修改该段；`rulemason check` 在「检查点提示与基础版的差异」列出缺少的条目，退出码不受影响

#### Scenario: 已接入项目升级
- **WHEN** 0.7.1 接入的项目升级后运行 `rulemason update`
- **THEN** 补齐计划列出 `openspec/config.yaml`，确认或 `--yes` 后写入；未写入时 `rulemason check` 报告差异，退出码为 0

### Requirement: 项目配置写错时给可读提示

`rulemason check` 读取 `openspec/config.yaml`、`openspec/judgments.yaml` 或 `openspec/copy-lexicon.yaml` 时，文件不是合法 YAML、顶层类型不对，或 `judgments.yaml` 有一条不是带 `id` 的映射，SHALL 输出「rulemason check 失败：」加文件路径与原因（解析失败时含行号），以非 0 退出，MUST NOT 打印 Python traceback。`rulemason init` 写入完成后汇报用的 check 因此失败时，SHALL 照常列出本次改动的文件与下一步，并说明 check 未完成的原因，以 0 退出。

#### Scenario: config.yaml 语法错误
- **WHEN** 已接入项目的 `openspec/config.yaml` 第 2 行写成 `context: a: b`，运行 `rulemason check`
- **THEN** 输出「rulemason check 失败：openspec/config.yaml 不是合法的 YAML（第 2 行：…）」，退出码非 0，没有 traceback

#### Scenario: 顶层类型不对
- **WHEN** `openspec/config.yaml` 的内容是一个列表，运行 `rulemason check --json`
- **THEN** 输出说明该文件顶层应是映射，退出码非 0，没有 traceback

#### Scenario: init 写完后汇报失败
- **WHEN** 项目 `openspec/judgments.yaml` 不合法，运行 `rulemason init --tools claude --yes`
- **THEN** 文件照计划写入，输出列出本次改动的文件、「check 未完成」及原因与下一步，退出码为 0

#### Scenario: 判断规则缺 id
- **WHEN** `openspec/judgments.yaml` 第 2 条没有 `id`，运行 `rulemason check`
- **THEN** 输出「rulemason check 失败：openspec/judgments.yaml 第 2 条不是带 id 的映射」，退出码非 0，没有 traceback

### Requirement: 按项目语言引用 React 落法

某个 `package.json` 的 `dependencies`、`devDependencies` 或 `peerDependencies` 含 `react` 时，所在目录 SHALL 视为 React 目录。项目有 React 目录时，`init` 与 `update` 写的标记块和工具入口 SHALL 引用 `.rulemason/rules/react.md`，没有时 MUST NOT 引用；已有 OpenCode 配置缺少应引用的落法时，补齐计划 SHALL 追加到其唯一的 instructions 数组末尾，无法安全追加时只提示；识别表的前端目录 SHALL 只列依赖含界面框架（react、vue、svelte、@angular/core、preact、solid-js、next、nuxt）或同目录有 index.html 的目录，并标出 React。`rulemason check` SHALL 在巡检「React 目录缺少 ESLint」中列出本身及上级目录都没有 ESLint 配置的 React 目录，MUST NOT 因此以非 0 退出。

#### Scenario: React 项目
- **WHEN** `web/package.json` 依赖 `react`，运行 `rulemason init --tools claude,opencode --yes`
- **THEN** `AGENTS.md` 的 Code style 块、`CLAUDE.md` 的 rulemason 块与 `opencode.jsonc` 的 instructions 都含 `.rulemason/rules/react.md`

#### Scenario: 已有 OpenCode 配置
- **WHEN** 项目 `.opencode/opencode.jsonc` 的 instructions 没有 `react.md`，升级后运行 `rulemason update --yes`
- **THEN** `react.md` 追加在数组末尾，其余内容不变，check 的工具入口一层齐全

#### Scenario: 没有 React
- **WHEN** 项目只有 Python 与不依赖 react 的 `package.json`
- **THEN** 标记块与入口都不出现 `react.md`

#### Scenario: React 目录没有 ESLint
- **WHEN** 项目乙的 `studio/package.json` 依赖 react，`studio/` 与项目根都没有 ESLint 配置
- **THEN** `rulemason check` 在「React 目录缺少 ESLint」列出 `studio`，退出码不因此改变

#### Scenario: 工作区根与后端的 package.json
- **WHEN** 项目根的 `package.json` 只有工作区与工具依赖，`apps/api/package.json` 也没有界面框架，`apps/web/package.json` 依赖 vue
- **THEN** 识别表前端目录只列 `apps/web`

#### Scenario: 不用框架的网页前端
- **WHEN** `frontend/package.json` 只依赖 vite 与 typescript，`frontend/index.html` 存在
- **THEN** 识别表前端目录列出 `frontend`，不标 React

### Requirement: remove 卸载 rulemason

`rulemason remove` SHALL 先列计划，确认或 `--yes` 后才写，`--plan` 只列计划。计划 SHALL 删除清单记录且未被手改的副本与 skill、`.rulemason.yaml`、AGENTS.md 与 CLAUDE.md 的 rulemason 标记块、与模板相同的 OpenCode 配置或其中指向 `.rulemason/` 的条目、与追加时相同的 `operations` 段。手改过或无法安全修改的项 MUST 保留并列出；已成为项目内容的部分 MUST NOT 删除，只列在汇报里。源码仓库、rulekit 0.5 项目或没有清单时 SHALL 停下，不写任何文件。

#### Scenario: 卸载刚接入的项目
- **WHEN** 在刚运行 `rulemason init --tools claude,opencode --yes` 的项目运行 `rulemason remove --yes`
- **THEN** `.rulemason/`、skill 副本、`.rulemason.yaml` 与生成的 `opencode.jsonc` 都被删除，`CLAUDE.md` 只剩 `@AGENTS.md` 一行，AGENTS.md 没有 rulemason 标记块，`openspec/config.yaml` 没有 `operations`，项目的其他文件不变

#### Scenario: 只看计划
- **WHEN** 在非交互环境运行 `rulemason remove --plan`
- **THEN** 打印删除、修改与保留清单，退出码为 0，项目中没有任何文件变化

#### Scenario: 副本被手改
- **WHEN** `.rulemason/rules/code-style.md` 被手改后运行 `rulemason remove --yes`
- **THEN** 该文件保留，汇报中列出，其余照常删除

### Requirement: remove 保持 lint 可用

ruff 或 ESLint 配置仍引用 `.rulemason/lint/` 下的副本时，`rulemason remove` SHALL 把被引用的副本移到项目根的 `lint/` 目录，并把各配置中的引用改为指向新位置的相对路径，使 lint 结果不变。`lint/` 中已有同名而内容不同的文件时 SHALL 停下，不写任何文件。

#### Scenario: Python 项目卸载后 ruff 照常
- **WHEN** 项目 `ruff.toml` 写着 `extend = ".rulemason/lint/ruff-base.toml"`，运行 `rulemason remove --yes`
- **THEN** `lint/ruff-base.toml` 内容与原副本相同，`ruff.toml` 改为 `extend = "lint/ruff-base.toml"`，`.rulemason/` 不再存在

#### Scenario: 继承链末端引用副本
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者写着 `extend = "../.rulemason/lint/ruff-base.toml"`，运行 `rulemason remove --yes`
- **THEN** `config/ruff-shared.toml` 改为 `extend = "../lint/ruff-base.toml"`，`ruff.toml` 逐字不变，`lint/ruff-base.toml` 与原副本相同

#### Scenario: 子目录里的 ESLint 配置
- **WHEN** `web/eslint.config.mjs` 写着 `import rulemasonBase from "../.rulemason/lint/eslint-base.mjs"`
- **THEN** 卸载后改为 `"../lint/eslint-base.mjs"`，`lint/eslint-base.mjs` 与原副本相同

#### Scenario: 目标已被占用
- **WHEN** 项目已有内容不同的 `lint/ruff-base.toml`
- **THEN** `rulemason remove` 说明冲突并以非 0 退出，项目中没有任何文件变化

### Requirement: 交互运行时显示启动画面

标准输入与标准输出都是终端时，`rulemason init`（未带 `--plan`、`--json`、`--yes`）SHALL 在预检之前显示启动画面：半格像素图标（一匹奔马背上骑着一只兔，10 行、26 列）、其下空一行、半格块字标 RULEMASON 与版本号、口号「AI 写代码，也讲章法」、「只管三件事：」及读 / 守 / 查三行，末尾说明本次会做什么、先列计划确认后才写入。启动画面 MUST NOT 等待输入、MUST NOT 播放动画；其余子命令与非交互运行 MUST NOT 显示。

#### Scenario: 交互运行 init
- **WHEN** 用户在终端运行 `rulemason init`
- **THEN** 先显示启动画面与本次说明，再进入预检与工具选择

#### Scenario: 图标在字标上方
- **WHEN** 用户在宽度不小于 60 列的 UTF-8 终端运行 `rulemason init`
- **THEN** 启动画面的前 10 行是图标，第 11 行是空行，第 12 行起是 RULEMASON 字标；图标每行不超过 26 列

#### Scenario: 带参数或非交互
- **WHEN** 运行 `rulemason init --plan`、`rulemason init --tools claude --yes`，或输出被重定向
- **THEN** 不显示启动画面，输出与改动前相同

### Requirement: 不带参数运行显示常用命令

在交互终端不带任何参数运行 `rulemason` SHALL 显示启动画面与常用命令（`init`、`check`、`update`、`key`、`--help`），以 0 退出。非交互环境不带参数运行 MUST 保持原有的用法报错与退出码 2。

#### Scenario: 终端里只敲 rulemason
- **WHEN** 用户在终端运行 `rulemason`
- **THEN** 显示启动画面与常用命令，其中有一行 `rulemason key` 及其说明，退出码 0

#### Scenario: 脚本里不带参数
- **WHEN** 脚本以非交互方式运行 `rulemason`
- **THEN** 打印用法报错，退出码 2

### Requirement: 启动画面按终端能力降级

设置了 `NO_COLOR` 时启动画面 MUST NOT 输出颜色转义，图标 SHALL 以单一前景色画出。终端宽度小于 60 列，或标准输出的编码无法写出块字符时，MUST 不画图标与字标，改为一行「rulemason 版本号」，其余文字照常显示。有颜色时，图标里的马 SHALL 用天空蓝系的 256 色，兔身 SHALL 用白色 256 色，使两只动物在暗底终端上能分辨。

#### Scenario: NO_COLOR
- **WHEN** 设置 `NO_COLOR=1` 后在终端运行 `rulemason init`
- **THEN** 启动画面不含 ANSI 颜色转义，图标与字标仍以块字符画出

#### Scenario: 终端太窄
- **WHEN** 终端宽度为 50 列
- **THEN** 不显示图标与字标，只显示「rulemason 版本号」与口号、三行说明

#### Scenario: 马蓝兔白
- **WHEN** 未设置 `NO_COLOR`，在终端运行 `rulemason`
- **THEN** 马的像素带天空蓝系的 256 色转义，兔身的像素带白色 256 色转义；同一字符位上下两种颜色时，上像素做前景、下像素做背景画出

### Requirement: 推送 tag 发布到 PyPI

公开仓库推送 `v<版本>` tag 时，CI SHALL 依次运行 ruff 与测试、核对 tag 与包版本一致、构建并经 Trusted Publishing 发布到 PyPI；任一步失败 MUST 不发布。发布流程 MUST NOT 使用存放在仓库或 CI 密钥里的 PyPI token。

#### Scenario: 正常发布
- **WHEN** 包版本为 0.8.0，推送 tag `v0.8.0`
- **THEN** 测试通过后 PyPI 出现 `rulemason 0.8.0`，`uv tool install rulemason==0.8.0` 可安装

#### Scenario: 版本对不上
- **WHEN** 包版本仍为 0.7.8，推送 tag `v0.8.0`
- **THEN** 工作流在发布前失败，PyPI 不出现新版本

### Requirement: check 识别 CI 中钉的版本

`rulemason check` 的识别表 SHALL 列出 CI 工作流里安装或检出 rulemason 时钉的版本，识别 `rulemason==<版本>`、`git+https://github.com/rulemason/rulemason@<ref>` 与 `repository: rulemason/rulemason` 加 `ref:` 三种写法。CI 引用了其他来源或没有钉版本时 SHALL 显示「有，未引用 rulemason」。

#### Scenario: PyPI 钉版本
- **WHEN** 项目 CI 写着 `uv tool install rulemason==0.8.0`
- **THEN** 识别表的 CI 一行显示该工作流文件钉 `0.8.0`

#### Scenario: 其他来源
- **WHEN** 项目 CI 从公开仓库以外的 git 地址安装，如 `uv tool install git+https://github.com/<其他账号>/rulekit@v0.7.8`
- **THEN** CI 一行显示「有，未引用 rulemason」

### Requirement: init 预填项目信息

`init` 新建 `AGENTS.md` 时 SHALL 预填项目简介：取项目根 README 第一段正文（跳过标题、徽章、空行，以及语言切换、导航这类只有链接与分隔符的行），截到两句以内；没有 README 或第一段不是文字时保留「待 /rulemason 补充」占位。红线一节 SHALL 写「暂无」。「本项目样板与豁免」与命令表的「自动识别，请确认」MUST 保留，使 `check` 的下一步仍指向 `/rulemason`。已有的 `AGENTS.md` MUST NOT 被改写简介或红线。

#### Scenario: 有 README 的新项目
- **WHEN** 项目 README 第一段写着「章法是一个给书法爱好者的字帖检索站，按书家与作品浏览单字。它只收录公有领域作品。」
- **THEN** 新建的 `AGENTS.md` 简介为这两句，红线一节为「暂无」，命令表仍带「自动识别，请确认」

#### Scenario: 没有 README
- **WHEN** 项目没有 README 文件
- **THEN** 简介保留「待 /rulemason 补充」占位，红线仍写「暂无」

#### Scenario: 已有 AGENTS.md
- **WHEN** 项目已有自己写的 `AGENTS.md`，简介是一句别的话
- **THEN** init 只补标记块，简介与红线原样保留

#### Scenario: README 开头是语言切换行
- **WHEN** README 标题下第一段是「中文 · [English](https://example.com/README.en.md)」，下一段是「章法是一个字帖检索站。」
- **THEN** 新建的 `AGENTS.md` 简介为「章法是一个字帖检索站。」，不是「中文 · English」

#### Scenario: 正文里带链接
- **WHEN** README 第一段是「本工具是 [OpenSpec](https://example.com) 的配套检查器，给 AI 编码用。」
- **THEN** 简介取这一段，链接不影响判断

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

### Requirement: 巡检核对最近归档的检查点记录

`rulemason check` 的巡检 SHALL 有一项「最近归档的检查点记录」：取 `openspec/changes/archive/` 里日期前缀最新的那一天归档的全部 change，逐个检查目录里有没有 `verification.md`，以及文件里是否同时写到审查（「审查」或 review）与测试（「测试」或 test）。缺文件或缺其中一项时 SHALL 列出 change 名与缺什么。这一项 MUST NOT 影响退出码与下一步；没有已归档 change 时写「一致」。更早的归档 MUST NOT 被检查。

#### Scenario: 最近一次归档带完整汇报
- **WHEN** 最新归档的 change 有 `verification.md`，其中写了独立审查两轮的结果与 pytest 的结果
- **THEN** 这一项写「一致」

#### Scenario: 最近一次归档没有汇报
- **WHEN** 最新归档的是 `2026-11-01-migrate-x`，目录里没有 `verification.md`
- **THEN** 这一项列出「2026-11-01-migrate-x：没有 verification.md」，退出码与下一步不变

#### Scenario: 汇报缺审查
- **WHEN** 最新归档的 change 有 `verification.md`，只写了测试结果，没有提到审查
- **THEN** 这一项列出该 change 缺审查记录

#### Scenario: 同一天归档了两个
- **WHEN** 最新的日期下归档了两个 change，其中一个没有 `verification.md`
- **THEN** 只列出缺的那一个；更早日期的归档即使没有汇报也不列出

#### Scenario: 表格写法的汇报
- **WHEN** `verification.md` 没有小节标题，只有一张写着「独立审查第一轮」「测试：44 项通过」的表格
- **THEN** 这一项写「一致」

### Requirement: README 提供英文简版

仓库根目录 SHALL 有 `README.en.md`：用英文写明工具做什么、安装方法与常用命令，开头 MUST 说明命令行界面与规则正文都是中文。`README.md` 顶部 SHALL 有指向它的链接，链接 MUST 用 GitHub 完整网址，使其在 PyPI 页面上同样可用。`README.md`「常用命令」表中的每条命令 MUST 出现在 `README.en.md` 中。包简介 SHALL 中英并列。

#### Scenario: 在 PyPI 页面点 English
- **WHEN** 读者在 PyPI 的 rulemason 页面点 README 顶部的 English 链接
- **THEN** 打开 GitHub 上的 `README.en.md`，而不是 PyPI 上的死链

#### Scenario: 英文读者装之前就知道界面是中文
- **WHEN** 英文读者读 `README.en.md`
- **THEN** 第一屏就读到命令行输出与规则正文是中文的说明

#### Scenario: 新增常用命令后忘了改英文版
- **WHEN** `README.md` 的常用命令表新增 `rulemason foo`，`README.en.md` 没有提到它
- **THEN** 测试失败，指出缺少 `rulemason foo`

### Requirement: 识别旧位置的基础配置副本

ruff 的 `extend` 或 ESLint 的引入指向项目内另一份同名基础配置（`ruff-base.toml` 或 `eslint-base.mjs`，不在 `.rulemason/lint/` 下）时，该文件内容与 `.rulemason/lint/` 下的副本相同，`init` 与 `update` SHALL 把路径改为指向项目内副本，作为一条「修改」进计划，并提示旧文件已无人引用、可以删除；MUST NOT 代为删除。内容不同时 MUST NOT 修改，按「改不了的 lint 项写明怎么改」报告。这一判断 SHALL 先于沿继承链处理。

#### Scenario: 卸载后再接入
- **WHEN** 项目运行过 `rulemason remove`，`ruff.toml` 写 `extend = "lint/ruff-base.toml"`，之后运行 `rulemason init --yes`
- **THEN** `ruff.toml` 改为 `extend = ".rulemason/lint/ruff-base.toml"`，汇报写明 `lint/ruff-base.toml` 已无人引用、可以删除，「需要你处理」里没有 ruff 项，`lint/ruff-base.toml` 仍在

#### Scenario: 旧副本被改过
- **WHEN** `ruff.toml` 继承 `lint/ruff-base.toml`，其内容与 `.rulemason/lint/ruff-base.toml` 不同
- **THEN** 不改任何文件，说明写明先运行 `diff lint/ruff-base.toml .rulemason/lint/ruff-base.toml` 看差异、把要保留的设置写进 `ruff.toml`、把 `ruff.toml` 该行改为继承 `.rulemason/lint/ruff-base.toml`，最后运行 `rulemason update`

#### Scenario: check 的口径
- **WHEN** 接入只剩 `ruff.toml` 继承内容相同的 `lint/ruff-base.toml`
- **THEN** check 报该配置继承的是旧位置的基础配置副本，第一行的下一步是「运行 rulemason update」

#### Scenario: ESLint 引入旧位置副本
- **WHEN** `apps/admin-web/eslint.config.js` 只从 `../../lint/eslint-base.mjs` 引入，该文件与 `.rulemason/lint/eslint-base.mjs` 内容相同
- **THEN** init 计划把这条路径改为 `../../.rulemason/lint/eslint-base.mjs`，文件里只保留一条基础规则引入

### Requirement: check 报 ESLint 重复引入基础规则

一份 ESLint 配置既引入了 `.rulemason/lint/eslint-base.mjs`，又引入了其他位置的同名基础规则时，`check` SHALL 在「接入 lint 继承」报「重复引入基础规则」并以非 0 退出；`init` 与 `update` MUST NOT 自动删除任一引入，说明 SHALL 写明旧引入所在行号与原文，以及配置里使用它的那一项所在行号与原文，删去这两处后运行 `rulemason check`。

#### Scenario: 同时引入两份
- **WHEN** `apps/admin-web/eslint.config.js` 第 2 行从 `../../lint/eslint-base.mjs` 引入 `legacyBase`，第 3 行从 `../../.rulemason/lint/eslint-base.mjs` 引入 `rulemasonBase`，第 9 行是 `{ rules: legacyBase },`
- **THEN** check 报该文件重复引入基础规则并以非 0 退出，说明写明删去第 2 行与第 9 行，`init --yes` 不修改该文件

### Requirement: ruff 沿继承链接上基础配置

ruff 配置已用 `extend` 继承了别的配置、但没有接上 `.rulemason/lint/ruff-base.toml` 时，`init` 与 `update` SHALL 沿 `extend` 找到继承链末端那份配置（相对路径按所在配置文件的目录解析），在末端配置里加入继承项目内基础配置的一行，作为一条「修改」进计划。链上原有的 `extend` MUST 保持不变。末端在项目外、读不出、链上有循环或任一配置写了 `select` 时 MUST NOT 修改，按「改不了的 lint 项写明怎么改」报告。

#### Scenario: 两层继承
- **WHEN** 项目 `ruff.toml` 写 `extend = "config/ruff-shared.toml"`，该文件存在且没有 `extend` 与 `select`
- **THEN** init 计划的「修改」含 `config/ruff-shared.toml`，写入后它继承 `../.rulemason/lint/ruff-base.toml`，`ruff.toml` 逐字不变，「需要你处理」里没有这一项

#### Scenario: 三层继承
- **WHEN** `ruff.toml` 继承 `a.toml`，`a.toml` 继承 `b.toml`，`b.toml` 没有 `extend`
- **THEN** 只有 `b.toml` 被加入继承基础配置的一行

#### Scenario: 两份配置共用末端
- **WHEN** `apps/api/ruff.toml` 与 `apps/worker/ruff.toml` 都继承项目根的 `ruff-common.toml`
- **THEN** 计划只修改 `ruff-common.toml` 一次，两份子配置都不改

#### Scenario: 继承链有循环
- **WHEN** `a.toml` 继承 `b.toml`，`b.toml` 又继承 `a.toml`
- **THEN** init 不修改任何 ruff 配置，在「需要你处理」写明循环经过的文件

#### Scenario: 已接上时不再改
- **WHEN** 继承链末端已继承 `.rulemason/lint/ruff-base.toml`，再次运行 `rulemason update --yes`
- **THEN** 计划中没有任何 ruff 配置

### Requirement: check 沿继承链判断 ruff 是否接上

`check` 判断一份 ruff 配置是否接上基础配置时 SHALL 沿 `extend` 查整条继承链：链上任一配置继承了项目内的 `ruff-base.toml` 副本即为接上；判断 `select` 时 SHALL 同样查整条链。链上配置指向不存在的文件时 SHALL 报「引用的基础配置不存在」或继承链中断，并写明是哪一份配置的哪个引用。

#### Scenario: 末端接上即为接上
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者继承 `../.rulemason/lint/ruff-base.toml`
- **THEN** check 的「接入 lint 继承」没有问题，退出码不受 ruff 影响

#### Scenario: 链上的 select
- **WHEN** `ruff.toml` 继承 `config/ruff-shared.toml`，后者写了 `select`
- **THEN** check 报 `config/ruff-shared.toml` 写了 `select` 会覆盖基础规则，并以非 0 退出

### Requirement: 改不了的 lint 项写明怎么改

`init`、`update` 与 `check` 报告改不了的 lint 项时，SHALL 先写一行摘要（文件与原因），再分行写：要改的文件与行号、该行原文、可选做法（每种做法写出改后的原文）、改完运行的命令。覆盖：ruff 配置写了 `select`（做法为改成 `extend-select` 或删去该行）、继承链走到项目外（做法为把该行改成继承项目内副本，并提醒把需要的设置复制进项目）、继承链循环、旧位置副本被改过、ESLint 重复引入、ESLint 配置格式认不出。说明 MUST NOT 给出用 `sed` 等命令直接改文件的一行命令。

#### Scenario: ruff.toml 写了 select
- **WHEN** 项目 `ruff.toml` 第 3 行是 `select = ["E", "F"]`，运行 `rulemason init --yes`
- **THEN** 「需要你处理」写明 `ruff.toml` 第 3 行与原文 `select = ["E", "F"]`，列出「改为 `extend-select = ["E", "F"]`」与「删去这一行」两种做法，最后写「改完运行：rulemason update」

#### Scenario: 继承了项目外的配置
- **WHEN** `ruff.toml` 第 1 行是 `extend = "~/configs/ruff.toml"`
- **THEN** 说明写明 `ruff.toml` 第 1 行与原文、改后的原文 `extend = ".rulemason/lint/ruff-base.toml"`，提醒把 `~/configs/ruff.toml` 里需要的设置复制进 `ruff.toml`，并写「改完运行：rulemason update」

#### Scenario: ESLint 配置格式认不出
- **WHEN** `web/eslint.config.js` 不是认得出的三种导出写法
- **THEN** 说明写明在该文件第一条 `import` 之前加入的引入原文，以及加到导出配置数组第一项的 `{ rules: rulemasonBase },`

#### Scenario: 老格式 .eslintrc
- **WHEN** 项目只有 `web/.eslintrc.json`
- **THEN** 说明写明 rulemason 只接扁平配置，先运行 `npx @eslint/migrate-config web/.eslintrc.json` 生成 `eslint.config.mjs`，再运行 `rulemason update`
