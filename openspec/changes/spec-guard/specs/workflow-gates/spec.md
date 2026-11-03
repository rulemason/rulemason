## ADDED Requirements

### Requirement: 不走 OpenSpec 改代码前先读主规格

项目有 `openspec/specs/` 时，不走 OpenSpec 的代码改动开始前，AI SHALL 读取与改动相关的主规格，并按四条路处理：用户要的就是改变主规格已写的 requirement 或 scenario 时，SHALL 代起最小 change（proposal、规格增量、一两条 tasks，不写 design），停一次等用户确认后再走全套检查点与归档；用户要的是别的事、做法却会破坏主规格已写的条目时为冲突，MUST 停下问用户，用户选改规格则按前一种处理；主规格没写到或不改行为时 SHALL 直接改，MUST NOT 为此补写规格。汇报 SHALL 写明读了哪些主规格、判在哪条路。

#### Scenario: 动到已写的条目
- **WHEN** 用户让 AI 把登录失败的提示从「密码错误」改成「账号或密码错误」，主规格的一条 scenario 写着「提示密码错误」
- **THEN** AI 代起一个只改这条 scenario 的最小 change，用几句话说明要改哪条规格，等用户确认后才写代码

#### Scenario: 与主规格冲突
- **WHEN** 用户让 AI 加一个「一键导出全部」按钮，最省事的做法会跳过逐条确认，而主规格写着「导出 MUST 先确认」
- **THEN** AI 不改代码，指出会被破坏的 requirement，问用户换做法、改这条规格还是放弃

#### Scenario: 主规格没写到
- **WHEN** 用户让 AI 调整一个按钮的间距，相关主规格没有写到样式
- **THEN** AI 直接改，汇报写明读了哪条主规格、判为「主规格未覆盖」，不补写规格

#### Scenario: 修 bug 对齐规格
- **WHEN** 代码行为与主规格写的不一致，用户让 AI 修
- **THEN** AI 直接改，使行为符合主规格，汇报判为「不改行为」

### Requirement: 直接改动改完只跑 ruff 与测试

不起 change 的直接改动完成后，AI SHALL 运行命令表的 ruff 与测试（不联网部分），改了前端时加跑前端 lint，报出的问题修掉后重跑直到通过；MUST NOT 为此运行自动精简与独立审查。项目没有 `openspec/` 时，检查点只剩这一条。汇报 SHALL 写明各步结果。

#### Scenario: 改了一个后端函数
- **WHEN** AI 不起 change 直接改了一个 Python 函数
- **THEN** 改完运行 ruff 与测试并修到通过，汇报写明结果，不调用精简与审查

#### Scenario: 没有 OpenSpec 的项目
- **WHEN** 只接入了规则层、没有 `openspec/` 的项目里，用户让 AI 改代码
- **THEN** AI 不找主规格，改完运行 ruff 与测试

### Requirement: 归档自查后直接并入主规格

归档一个 change 时，AI SHALL 先自查：tasks 全部完成、`verification.md` 存在；通过后运行 `openspec archive <name> --yes` 把规格增量并入主规格，再运行 `openspec validate --specs --strict`。MUST NOT 就「是否同步主规格」询问用户。自查不过、归档失败或校验失败时 SHALL 停下，用一两句话说明原因与可选做法，不自行跳过。

#### Scenario: 正常归档
- **WHEN** 一个 change 的 tasks 全部完成、已有 `verification.md`
- **THEN** AI 运行 `openspec archive <name> --yes` 与 `openspec validate --specs --strict`，汇报归档位置与校验结果，过程中不问是否同步

#### Scenario: 合并后校验失败
- **WHEN** 归档后 `openspec validate --specs --strict` 报某条 requirement 正文超过 500 字
- **THEN** AI 停下，说明是哪条 requirement、为什么不合格，给出改法，等用户决定或按用户已授权的范围修正

#### Scenario: 还有未完成的任务
- **WHEN** 要归档的 change 还有 2 条任务没勾
- **THEN** AI 不归档，说明还差哪两条

### Requirement: 归档够 3 个时提示一次配置 key

归档完成后，已归档 change 数正好等于 3、项目判断层未启用且本机没有 Jev key 时，AI SHALL 在汇报末尾提示一次：判断条件已满足，可运行 `rulemason key` 配置（申请地址 https://typesafe.ai/ ）。AI MUST NOT 代为配置 key，归档数不等于 3 时 MUST NOT 提示。

#### Scenario: 第 3 个归档
- **WHEN** 项目归档第 3 个 change，没有 `openspec/judgments.yaml`，本机未配置 key
- **THEN** 汇报末尾有一句配置 key 的提示与申请地址

#### Scenario: 第 4 个归档
- **WHEN** 同一项目归档第 4 个 change，仍未配置 key
- **THEN** 汇报不再提示

## MODIFIED Requirements

### Requirement: 检查点正文只住本仓库

检查点的触发时机、步骤顺序、block 与 review 的处理方式 SHALL 在本仓库 `rules/workflow-gates.md` 只有一份可编辑正文。接入项目持有由 `rulemason init` / `rulemason update` 生成的只读副本 `.rulemason/rules/workflow-gates.md`；项目通用指令和已选工具入口 SHALL 引用或加载该副本，并写明改代码前（不论是否走 OpenSpec）读取它，MUST NOT 手改或另写一份。工具专属命令只负责调用映射，不承载检查点正文；运行 `openspec update` 后检查点仍须生效。

#### Scenario: 修改一个检查点
- **WHEN** 检查点的处理方式需要调整
- **THEN** 只改 rulemason 仓库的 `rules/workflow-gates.md` 并发布；接入项目运行 `rulemason update` 后，已选工具读到新正文

#### Scenario: openspec update 之后
- **WHEN** 在接入项目运行 `openspec update`
- **THEN** 检查点仍然生效，因为正文不在会被 openspec 重新生成的工具命令文件中

#### Scenario: 副本被手改
- **WHEN** 有人在项目里直接修改 `.rulemason/rules/workflow-gates.md`
- **THEN** `rulemason check` 报告该副本与记录不符并以非 0 退出

#### Scenario: 入口块覆盖直接改动
- **WHEN** 已接入项目运行 `rulemason update` 后查看 AGENTS.md 的 workflow-gates 标记块
- **THEN** 标记块写明开始 OpenSpec 方案、实现，以及不走 OpenSpec 改代码之前都读取检查点副本
