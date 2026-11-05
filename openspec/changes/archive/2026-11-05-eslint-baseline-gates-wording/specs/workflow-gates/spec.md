## MODIFIED Requirements

### Requirement: 写完代码后按顺序检查并逐项汇报

apply 最后一个任务做完、汇报完成之前，SHALL 按顺序执行：1. 按「Apply 后行为保持的自动精简」requirement 精简本次 diff。2. 按「自动代码审查不等待人工确认」requirement 独立审查、自动修复并限轮复审。3. 运行 ruff，修复本次改动引入的问题（落在本次新增或修改的行上的问题、新加而未使用的 import，以及因本次改动在未改的行上新出现的问题）；改动前就存在的问题不修，汇报列出数量并建议运行 `/rulemason` 建立基线。4. 运行不联网测试；改判断规则或 `JEV_MODEL` 时加跑项目命令表的「判断回归」，命令表没有这一行时跳过并写明。5. 改前端时运行前端 lint，只修本次改动引入的问题，既有问题同第 3 步处理。6. 改界面文案时运行文案检查，修复 block 并列出 review。7. 运行项目额外步骤。完成汇报 MUST 逐项报告结果与跳过原因，写进 change 的 `verification.md`，并对照 design 中各文件的估计行数，超出一倍写明原因。

#### Scenario: 只改了后端
- **WHEN** 一次 apply 只改了 Python 文件
- **THEN** 汇报包含自动精简、自动代码审查、ruff、测试的结果，并写明前端 lint 与文案检查已跳过、原因是未改动前端与文案

#### Scenario: 改了判断规则
- **WHEN** 一次 apply 修改了 `judgments.yaml`
- **THEN** 测试一步加跑命令表的「判断回归」，汇报中写明回归结果

#### Scenario: ruff 报错
- **WHEN** ruff 报出本次改动引入的问题
- **THEN** 修掉后重跑直到这些问题消失，再进入下一步，汇报中写明修了什么

#### Scenario: 项目还没建立基线
- **WHEN** 改动前 ruff 就报出 2886 个问题，本次改动只新引入 1 个
- **THEN** 只修这 1 个，不改其余 2886 处涉及的代码；汇报写明「ruff 有 2886 个既有问题，未修，建议运行 /rulemason 建立基线」

#### Scenario: 对照行数估计
- **WHEN** apply 完成，design 估计某文件 +40 行，实际 +95 行
- **THEN** `verification.md` 列出该文件的估计与实际行数，并写明超出的原因

#### Scenario: 前端还没建立基线
- **WHEN** 改动前前端 lint 就报出 69 个基础规则问题，本次改动只新引入 1 个
- **THEN** 只修这 1 个，不改其余 69 处涉及的代码；汇报写明「前端 lint 有 69 个既有问题，未修，建议运行 /rulemason 建立 ESLint 基线」

### Requirement: 不走 OpenSpec 改代码前先读主规格

项目有 `openspec/specs/` 时，不走 OpenSpec 的代码改动开始前，AI SHALL 读取与改动相关的主规格：除按能力名筛选，还 SHALL 把本次要改的测试函数名、路由路径与被改函数名在 `openspec/specs/` 里检索，命中的 requirement 列进判路依据；改既有测试的断言或白名单前 MUST 先检索该测试名，命中主规格点名的测试时按「冲突」处理。然后按四条路处理：用户要的就是改变主规格已写的条目时，SHALL 代起最小 change（proposal、规格增量、一两条 tasks，不写 design），停一次等用户确认；用户要的是别的事、做法却会破坏主规格已写的条目时为冲突，MUST 停下问用户；主规格没写到或不改行为时 SHALL 直接改，MUST NOT 为此补写规格。汇报 SHALL 写明读了哪些主规格、检索命中了什么、判在哪条路。

#### Scenario: 动到已写的条目
- **WHEN** 用户让 AI 把登录失败的提示从「密码错误」改成「账号或密码错误」，主规格的一条 scenario 写着「提示密码错误」
- **THEN** AI 代起一个只改这条 scenario 的最小 change，用几句话说明要改哪条规格，等用户确认后才写代码

#### Scenario: 与主规格冲突
- **WHEN** 用户让 AI 加一个「一键导出全部」按钮，最省事的做法会跳过逐条确认，而主规格写着「导出 MUST 先确认」
- **THEN** AI 不改代码，指出会被破坏的 requirement，问用户换做法、改这条规格还是放弃

#### Scenario: 规格点名了要改的测试
- **WHEN** 用户让 AI 给一个后台操作补审计，做法要把几条 DELETE 路由加进测试 `test_admin_has_no_delete_routes` 的白名单，而一份名字与这个操作无关的主规格写着「管理端 MUST NOT 有 DELETE 路由」并点名了这个测试
- **THEN** AI 检索测试名命中这条 requirement，按「冲突」停下，指出改白名单会绕开规格，问用户换做法还是改规格

#### Scenario: 主规格没写到
- **WHEN** 用户让 AI 调整一个按钮的间距，相关主规格没有写到样式
- **THEN** AI 直接改，汇报写明读了哪条主规格、检索无命中、判为「主规格未覆盖」，不补写规格

#### Scenario: 修 bug 对齐规格
- **WHEN** 代码行为与主规格写的不一致，用户让 AI 修
- **THEN** AI 直接改，使行为符合主规格，汇报判为「不改行为」

### Requirement: 提交信息格式

接入项目的提交信息 SHALL 写成「类型(范围): 中文说明（change 名）」，类型取 feat、fix、refactor、docs、chore 之一；归档提交写「chore: 归档 <change>，规格并入主 specs（…）」；与 change 无关的提交可以省略 change 名。项目有 commitlint 时 SHALL 按其配置换行与限长。提交 SHALL 只带本次计划内的文件；共享分支上 MUST NOT 用 `--amend`，补漏另开新提交；推送前 SHALL 单独列出待推送的提交核对，与推送分两步，列表与预期不符时停下说明；并行会话 SHALL 建议各用 `git worktree`。共享正文 MUST NOT 写具体的 git 子命令选项。

#### Scenario: 实现一个 change
- **WHEN** 提交 change `remove` 的实现
- **THEN** 提交信息形如「feat(rulemason): rulemason remove 卸载命令——…（remove）」

#### Scenario: 项目有 commitlint
- **WHEN** 项目配置了 commitlint，正文单行上限 100 字符，AI 要写一段较长的中文说明
- **THEN** AI 按 100 字符换行，提交不被 commitlint 拦下

#### Scenario: 漏了一个文件
- **WHEN** 推送后发现 `openspec/config.yaml` 没带上，而同一分支可能有别的会话在提交
- **THEN** AI 另开一个新提交补上，不用 `--amend`

#### Scenario: 推送前核对
- **WHEN** AI 准备推送，待推送列表里多出一个不是本次计划的提交
- **THEN** AI 停下说明多出的提交，不推送

## ADDED Requirements

### Requirement: 改既有测试时保持源码文本断言等价

共享检查点 SHALL 有「改既有测试时」一节，写明：读源码再断言原文的测试，改代码时只允许把断言改成新写法下的等价内容，MUST NOT 删除或放宽断言，汇报 SHALL 逐条列出改了哪些断言；走 OpenSpec 的 apply 与不走 OpenSpec 的直接改动两条路都 SHALL 引用这一节。

#### Scenario: 清理嵌套三元碰到文本断言
- **WHEN** 一条测试读源码文件并断言里面有一段嵌套三元的原文，AI 按规矩把这段改成提前返回
- **THEN** AI 把断言改成新写法的对应原文，不删这条测试，汇报列出这条断言的改前改后

#### Scenario: 删掉断言
- **WHEN** AI 发现删掉这条文本断言最省事
- **THEN** 检查点不允许，AI 保留断言并改成等价内容；确实无法等价时停下说明，由用户决定
