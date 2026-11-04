## MODIFIED Requirements

### Requirement: 项目只补命令、红线清单与额外步骤

接入项目 SHALL 在加载共享检查点后，记录所选工具运行本项目命令的映射（判断、ruff、测试、前端 lint、文案检查）、实质类红线规则清单及额外步骤。红线规则清单那一行 SHALL 写作「判断用的红线规则」，与项目通用指令里「红线（不可违反）」一节区分；判断未启用时写「判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）」。工具间命令差异 SHALL 保留在项目配置或适配入口中，检查点正文 MUST NOT 因工具不同而分叉。额外步骤 SHALL 在「写完代码后」汇报之前执行并逐项报告。

#### Scenario: 不同的命令前缀
- **WHEN** 项目甲用 `cd api && uv run`，项目乙用 `cd backend && . .venv/bin/activate && PYTHONPATH=.`
- **THEN** 两边检查点正文相同，差异只存在于各自的命令映射

#### Scenario: 项目额外步骤
- **WHEN** 项目乙改了 `frontend/index.html`
- **THEN** 在汇报前运行它自己的前端交互回归，结果与其他检查一起逐项汇报

#### Scenario: 新接入项目的红线规则一行
- **WHEN** 对一个新项目运行 `rulemason init`
- **THEN** AGENTS.md 的命令表之后写「判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）」，「## 红线（不可违反）」一节仍写「暂无」

### Requirement: 写完代码后按顺序检查并逐项汇报

apply 最后一个任务做完、汇报完成之前，SHALL 按顺序执行：1. 按「Apply 后行为保持的自动精简」requirement 精简本次 diff。2. 按「自动代码审查不等待人工确认」requirement 独立审查、自动修复并限轮复审。3. 运行 ruff，修复本次改动引入的问题（落在本次新增或修改的行上的问题、新加而未使用的 import，以及因本次改动在未改的行上新出现的问题）；改动前就存在的问题不修，汇报列出数量并建议运行 `/rulemason` 建立基线。4. 运行不联网测试；改判断规则或 `JEV_MODEL` 时加跑项目命令表的「判断回归」，命令表没有这一行时跳过并写明。5. 改前端时运行 lint 并修复。6. 改界面文案时运行文案检查，修复 block 并列出 review。7. 运行项目额外步骤。完成汇报 MUST 逐项报告结果与跳过原因，写进 change 的 `verification.md`，并对照 design 中各文件的估计行数，超出一倍写明原因。

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

### Requirement: 直接改动改完只跑 ruff 与测试

不起 change 的直接改动完成后，AI SHALL 运行命令表的 ruff 与测试（不联网部分），改了前端时加跑前端 lint，修掉本次改动引入的问题后重跑，直到这些问题消失；改动前就存在的 ruff 问题不修，汇报列出数量并建议运行 `/rulemason` 建立基线。MUST NOT 为此运行自动精简与独立审查。项目没有 `openspec/` 时，检查点只剩这一条。汇报 SHALL 写明各步结果。

#### Scenario: 改了一个后端函数
- **WHEN** AI 不起 change 直接改了一个 Python 函数
- **THEN** 改完运行 ruff 与测试并修到本次引入的问题消失，汇报写明结果，不调用精简与审查

#### Scenario: 没有 OpenSpec 的项目
- **WHEN** 只接入了规则层、没有 `openspec/` 的项目里，用户让 AI 改代码
- **THEN** AI 不找主规格，改完运行 ruff 与测试

#### Scenario: 改动所在文件带遗留豁免
- **WHEN** 直接改动碰到的文件在 `per-file-ignores` 里有「接入前遗留」豁免
- **THEN** AI 不强制清掉该文件的遗留豁免；汇报写明这个文件还有遗留豁免，可以顺手清掉
