# workflow-gates Specification

## Purpose
规定包住每个 OpenSpec change 的三个自动检查点（方案写完、写代码前、写完代码后）在本仓库只有一份，接入项目引用后只补自己的命令、红线规则清单与额外步骤，并提供可选的「阶段学习文档同步 Notion」步骤。

## Requirements

### Requirement: 检查点正文只住本仓库

三个检查点的触发时机、步骤顺序、block 与 review 的处理方式 SHALL 在本仓库 `rules/workflow-gates.md` 只有一份可编辑正文。接入项目持有由 `rulemason init` / `rulemason update` 生成的只读副本 `.rulemason/rules/workflow-gates.md`；项目通用指令和已选工具入口 SHALL 引用或加载该副本，MUST NOT 手改或另写一份。工具专属命令只负责调用映射，不承载检查点正文；运行 `openspec update` 后检查点仍须生效。

#### Scenario: 修改一个检查点
- **WHEN** 检查点的处理方式需要调整
- **THEN** 只改 rulemason 仓库的 `rules/workflow-gates.md` 并发布；接入项目运行 `rulemason update` 后，已选工具读到新正文

#### Scenario: openspec update 之后
- **WHEN** 在接入项目运行 `openspec update`
- **THEN** 检查点仍然生效，因为正文不在会被 openspec 重新生成的工具命令文件中

#### Scenario: 副本被手改
- **WHEN** 有人在项目里直接修改 `.rulemason/rules/workflow-gates.md`
- **THEN** `rulemason check` 报告该副本与记录不符并以非 0 退出

### Requirement: 项目只补命令、红线清单与额外步骤

接入项目 SHALL 在加载共享检查点后，记录所选工具运行本项目命令的映射（判断、ruff、测试、前端 lint、文案检查）、实质类红线规则清单及额外步骤。工具间命令差异 SHALL 保留在项目配置或适配入口中，检查点正文 MUST NOT 因工具不同而分叉。额外步骤 SHALL 在「写完代码后」汇报之前执行并逐项报告。

#### Scenario: 不同的命令前缀
- **WHEN** 项目甲用 `cd api && uv run`，项目乙用 `cd backend && . .venv/bin/activate && PYTHONPATH=.`
- **THEN** 两边检查点正文相同，差异只存在于各自的命令映射

#### Scenario: 项目额外步骤
- **WHEN** 项目乙改了 `frontend/index.html`
- **THEN** 在汇报前运行它自己的前端交互回归，结果与其他检查一起逐项汇报

### Requirement: 方案写完立即检查

proposal 或 design 刚写完时（经任一已选工具的 OpenSpec 流程或 explore 模式手写），SHALL 立即运行项目命令映射中的判断检查。格式类 block（产物格式 lint，含决策缺否决理由、Risks 格式与缺回滚说明；以及写明不做什么）是起草失误，由 AI 自行修改后重跑；实质类 block 或 review（项目红线、过度设计）等于改方案，MUST 报告给用户决定。最终结果与改动 SHALL 附在方案汇报中。

#### Scenario: 格式类 block
- **WHEN** 新写的 design 有一个决策缺少被否决的备选方案，`lint/design` 报 block
- **THEN** AI 补上备选后重跑，汇报中写明补了什么

#### Scenario: 实质类 block
- **WHEN** 新写的 design 触犯项目红线
- **THEN** AI 不自行改方案，把规则与原文报告给用户，等用户决定

### Requirement: 写代码前再检查一次

apply 写任何代码之前 SHALL 再运行一次判断检查。任一 block MUST 停下，不碰代码，逐条报告规则与原文，等用户决定；只有 review 时用一小段列出后继续。此时不静默修改方案，因为用户已经看过方案。

#### Scenario: 用户改过方案后出现 block
- **WHEN** 用户手改 design 后开始 apply，检查出一条 block
- **THEN** AI 不写代码，报告该条 block 并等待

#### Scenario: 只有 review
- **WHEN** 检查结果只有 review
- **THEN** AI 列出 review 后继续写代码

### Requirement: 写完代码后按顺序检查并逐项汇报

apply 最后一个任务做完、汇报完成之前，SHALL 按顺序执行：1. 按「Apply 后行为保持的自动精简」requirement 精简本次 diff。2. 按「自动代码审查不等待人工确认」requirement 独立审查、自动修复并限轮复审。3. 运行 ruff 并修复问题。4. 运行不联网测试；改判断规则或 `JEV_MODEL` 时加跑项目命令表的「判断回归」，命令表没有这一行时跳过并写明。5. 改前端时运行 lint 并修复。6. 改界面文案时运行文案检查，修复 block 并列出 review。7. 运行项目额外步骤。完成汇报 MUST 逐项报告结果与跳过原因，写进 change 的 `verification.md`，并对照 design 中各文件的估计行数，超出一倍写明原因。

#### Scenario: 只改了后端
- **WHEN** 一次 apply 只改了 Python 文件
- **THEN** 汇报包含自动精简、自动代码审查、ruff、测试的结果，并写明前端 lint 与文案检查已跳过、原因是未改动前端与文案

#### Scenario: 改了判断规则
- **WHEN** 一次 apply 修改了 `judgments.yaml`
- **THEN** 测试一步加跑命令表的「判断回归」，汇报中写明回归结果

#### Scenario: ruff 报错
- **WHEN** ruff 报出问题
- **THEN** 修掉后重跑直到通过，再进入下一步，汇报中写明修了什么

#### Scenario: 对照行数估计
- **WHEN** apply 完成，design 估计某文件 +40 行，实际 +95 行
- **THEN** `verification.md` 列出该文件的估计与实际行数，并写明超出的原因

### Requirement: 项目尚无判断层时只启用不依赖 Jev 的步骤

未装判断层的接入项目 SHALL 只执行「写完代码后」检查点中不依赖 Jev 的步骤（自动精简、自动代码审查、ruff、不联网测试、前端 lint、额外步骤）。文案检查依赖 Jev 时 MUST 跳过并汇报「判断层未装」；方案写完与写代码前两个检查点不执行判断。

#### Scenario: 新项目第一个 change
- **WHEN** 刚接入的项目完成第一个 apply
- **THEN** 汇报包含自动精简、自动代码审查、ruff、测试、前端 lint 与额外步骤的结果，并写明判断与文案检查因判断层未装而跳过

### Requirement: Apply 后行为保持的自动精简

实现者 SHALL 在独立只读审查前，对本次 diff 中的代码执行自动精简，重点消除重复、死代码、冗余抽象和过复杂逻辑。精简 MUST 保持需求、外部行为和 API 不变，MUST NOT 为减少行数而重写无关代码。已选工具 MAY 通过自己的入口（如 Claude Code 的 `CLAUDE.md` 标记块）把这一步映射到该工具的精简命令；映射只决定由谁执行，范围与约束仍以共享正文为准，共享正文 MUST NOT 写入某一工具的专属命令。

#### Scenario: 本次改动中有可安全消除的重复
- **WHEN** diff 中有重复逻辑，且合并不会改变需求、外部行为或 API
- **THEN** AI 自动精简该逻辑，再交独立只读审查并运行测试

#### Scenario: 精简可能改变行为或范围
- **WHEN** 某项精简会改变外部行为、API、规格或超出本次 diff
- **THEN** AI 不自动实施该精简，并在审查结果中说明原因

#### Scenario: Claude Code 用 /simplify 执行精简
- **WHEN** 选了 Claude Code 的项目在 apply 结束前，diff 改了代码逻辑
- **THEN** 用 `/simplify` 执行精简，只采纳行为保持的修改，之后照常做独立只读审查与测试

#### Scenario: 只改了文档或配置
- **WHEN** 本次 diff 只涉及文档、配置或生成副本
- **THEN** 不调用 `/simplify`，汇报中写明无代码改动、跳过精简

### Requirement: 自动代码审查不等待人工确认

自动代码审查 SHALL 由独立于实现者的审查者执行：有所有工具权限均拒绝的子代理时 MUST 使用该子代理；否则 MUST 使用独立的新会话、单独复审轮次或只能读一份文件的子代理，只允许读取实现者准备的那一份材料文件。审查者只分析实现者提供的材料，MUST NOT 读取仓库其他文件、运行命令、修改文件，也不接收密钥及无关用户内容。结果 SHALL 用 `pass`（通过且无发现）、`block`、`review` 表达。AI SHALL 自动修复 block 与范围内可修的 review，并重新审查，最多两轮；第二轮只剩 review 时，修复后不再审第三轮。只有修复需要改变方案、规格或扩大范围时，才 MUST 停止并报告原因，MUST NOT 把逐条代码审核转交用户。

#### Scenario: 审查发现可修问题
- **WHEN** 独立审查者报告一个可修复的 block
- **THEN** AI 自动修复并重新审查，不等待用户逐条确认代码

#### Scenario: 没有可限制为只读的子代理
- **WHEN** 当前工具不提供所有工具权限均拒绝的审查子代理
- **THEN** 实现者把材料写成一份文件，审查者只读这份文件、不运行命令、不修改文件，按同一审查清单复审，AI 继续自动修复与验证

#### Scenario: 两轮后仍有 block
- **WHEN** 第二轮审查后仍有未消除的 block
- **THEN** AI 停止实现并报告未消除项与原因，不继续无限重审

#### Scenario: 修复会超出范围
- **WHEN** 消除 block 需要改变方案、规格或扩大范围
- **THEN** AI 停止实现，报告问题与原因，不擅自改方案，也不要求用户逐行审核代码

#### Scenario: 第二轮只剩 review
- **WHEN** 第二轮审查没有 block，只有几条范围内可修的 review
- **THEN** AI 修复后跑完 ruff 与测试即可，不再发起第三轮审查，修复内容写进汇报

### Requirement: 可选步骤：阶段学习文档同步 Notion

接入项目 SHALL 能选择启用「阶段学习文档」步骤：项目通用指令或所选工具加载的项目指令中写明 Notion 落点后启用，未写明则不启用。启用后，每完成一个阶段（一个产物写完或一段 apply 完成），AI MUST 主动在落点下新建编号子页，写给零基础读者：做了什么、为什么、要敲的命令、应该看到什么，并注明仓库是权威记录，不等用户提醒。

#### Scenario: 已启用的项目
- **WHEN** 项目写明了 Notion 落点，且一个 change 的 design 刚写完
- **THEN** 使用所选工具的 AI 在落点下新建下一篇编号子页

#### Scenario: 未启用的项目
- **WHEN** 项目指令没有写 Notion 落点
- **THEN** 不同步 Notion，汇报中也不提这一步

### Requirement: OpenSpec operations 只放指向检查点的提示

本仓库 SHALL 维护一份 OpenSpec `operations` 基础版，`apply` 与 `archive` 的 `guidance` 各一到两条，只写「按检查点文件执行」或「归档前确认检查点已执行并写进汇报」这类指向。条目 MUST 引用检查点文件路径，MUST NOT 复制检查点正文、命令表或项目专属内容。检查点内容有冲突时 SHALL 以通用指令引入的检查点文件为准。

#### Scenario: AI 走 apply
- **WHEN** 已接入项目运行 `openspec instructions apply --change <name> --json`
- **THEN** `operationGuidance` 含指向 `.rulemason/rules/workflow-gates.md` 的提示，不含检查点的具体步骤

#### Scenario: 修改检查点
- **WHEN** 检查点正文新增或调整一步
- **THEN** 只改 `rules/workflow-gates.md`，`operations` 基础版不需要改

### Requirement: 提交信息格式

接入项目的提交信息 SHALL 写成「类型(范围): 中文说明（change 名）」，类型取 feat、fix、refactor、docs、chore 之一；归档提交写「chore: 归档 <change>，规格并入主 specs（…）」。与 change 无关的提交可以省略括号里的 change 名。

#### Scenario: 实现一个 change
- **WHEN** 提交 change `remove` 的实现
- **THEN** 提交信息形如「feat(rulemason): rulemason remove 卸载命令——…（remove）」
