## MODIFIED Requirements

### Requirement: 按安装状态而非归档数决定下一步

skill SHALL 按「补项目信息 → 日常巡检」的顺序找出第一个未完成的阶段，每次运行只做这一个阶段；用户要做存量清理时除外，见「cleanup 参数先诊断、确认后再修」。接入共享规则由 `rulemason init` 完成，不由 skill 写入。「整理判断规则」与「启用判断」是可选功能：用户提出要启用判断时才做，归档数只决定能否启用。做之前 MUST 列出将新增与修改的文件，等用户确认后才写。

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

#### Scenario: 项目信息未补完时要求清理
- **WHEN** `next.code` 为 `fill_project_info`，用户要求做存量清理
- **THEN** 本次进入清理，不补项目简介与红线

### Requirement: 存量清理按固定流程做

修一个模块或一批同类违规时，skill SHALL 按顺序做：规划（按模块分组，同一文件只属一组；范围是单个模块时只含该模块的文件；多组都要用的辅助函数先规划成共用模块，MUST NOT 为缩小改动面要求「不新建文件」）→ 先存改前证据（在改前提交的临时 worktree 上跑指标，MUST NOT 经 stdin 交改前代码）→ 给每组同一份代理指令 → 中断后先用 `git diff` 核对再继续 → 主会话复核 → 收尾。动手前 MUST 列出分组、计划与要落地的建议，等用户确认。修模块前 SHALL 通读该模块的文件，由用户选择落地哪些软建议。诊断的只读代理最多 5 个，改文件的代理最多 3 个；没有子代理时串行。这是用户提出时才做的可选功能。skill 不提交，收尾说明提交信息写成 `refactor(cleanup): <模块>`。

#### Scenario: 清理嵌套三元
- **WHEN** 用户让 AI 清掉前端 300 多处嵌套三元
- **THEN** skill 先列出按模块的分组（每组几个文件）、要先建的共用模块与改前要存的指标，等用户确认后才动手

#### Scenario: 改前证据
- **WHEN** 要记录改前的 lint 与复杂度数字，项目的 ESLint 配置带类型检查
- **THEN** 在改前提交的临时 worktree 里跑统计，不把改前代码经 stdin 交给 ESLint

#### Scenario: 被用量上限打断
- **WHEN** 并行的几组里有 3 组中途停下
- **THEN** 主会话先用 `git diff` 核对这几组哪些文件已经改完，只把没改完的交出去继续，不重做已完成的部分

#### Scenario: 几组都要同一个辅助函数
- **WHEN** 规划时发现 5 个组都要一个「取过期时间」的辅助函数
- **THEN** 先在一处建好这个函数，代理指令写明复用它，不让每组各写一份

#### Scenario: 只修一个模块
- **WHEN** 用户指定只清理某一个模块
- **THEN** 分组与改动只含该模块的文件，其他模块不改

#### Scenario: 用户只同意一部分建议
- **WHEN** 通读后列出 4 条软建议，用户只同意其中 2 条
- **THEN** 只落地这 2 条，其余不改

#### Scenario: 没有子代理
- **WHEN** 所用工具不能派子代理
- **THEN** 各组串行做，不并行

#### Scenario: 模块很多
- **WHEN** 仓库有 8 个模块要抽样诊断
- **THEN** 同时进行的只读代理不超过 5 个

## ADDED Requirements

### Requirement: cleanup 参数先诊断、确认后再修

用户要做存量清理时，skill SHALL 仍先运行 `rulemason check --json`。`next.code` 为 `init`、`fix_manifest`、`upgrade_machine` 或 `update` 时 MUST 按识别表停下，不诊断也不改文件。为 `fill_project_info`、`manual_lint`、`fix_gitignore` 或 `none` 时进入清理。不带模块名时 SHALL 只输出诊断、不改任何文件，汇报最后一行给出下一步怎么指定模块。带模块名时模块名只划定范围，MUST 先列出计划与建议，用户确认后才改文件。

#### Scenario: 副本还没更新
- **WHEN** `next.code` 为 `update`，用户要求做存量清理
- **THEN** 提示先运行 `rulemason update`，不诊断，不改文件

#### Scenario: 只诊断
- **WHEN** 用户要求清理但没有指定模块，且 `next.code` 为 `none`
- **THEN** 输出全仓诊断且不改任何文件，汇报最后一行说明下一步如何指定模块

#### Scenario: 模块名不是同意
- **WHEN** 用户指定了模块，计划尚未确认
- **THEN** 不改任何文件

### Requirement: 诊断分三层且不另存进度

全仓诊断 SHALL 覆盖每个模块，分三层。硬指标读 ruff 与 ESLint 的「接入前遗留」条目和复杂度。机械软指标用临时参数统计 ruff 的 `ARG`、`ERA`、`BLE`、`S110`、`T201`，并查重复块与缺少文件首行注释，MUST NOT 改项目的 lint 配置。每个模块再抽 2 到 3 个最大或最复杂的文件，给出高、中、低三档精简潜力，并举 1 到 2 个例子。有 Node 时用钉死版本的 `npx --yes jscpd` 查重复，否则仅对 Python 用钉死版本的 `uvx pylint`；离线或下载失败时跳过该列并写明原因。MUST NOT 把该工具写入项目依赖，也 MUST NOT 在安装或 init 时安装。诊断与进度 MUST NOT 写入 `.rulemason/` 或新的状态文件；进度用遗留条目是否还在，以及 `git log` 里 `refactor(cleanup):` 开头的提交。

#### Scenario: 不改 lint 配置
- **WHEN** 诊断统计 `ARG` 等未写入基础配置的规则
- **THEN** 使用临时参数，项目的 lint 配置文件保持不变

#### Scenario: 离线查不了重复
- **WHEN** 本机没有 Node，且 `uvx` 下载失败
- **THEN** 重复块这一列空着并写明原因，硬指标与抽样照常给出

#### Scenario: 再次诊断看出进度
- **WHEN** 上次诊断之后，用户提交了 `refactor(cleanup):` 开头、点名某模块的提交，且该模块的遗留条目已删除
- **THEN** 进度从这条提交和遗留条目读出，不读取上次诊断留下的文件
