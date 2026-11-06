## MODIFIED Requirements

### Requirement: 通用判断规则随引擎提供

「写明不做什么」「不做过度设计」「直接改动不绕开主规格」三条通用判断规则 SHALL 随引擎提供，所有接入项目自动启用；「决策附备选」由产物格式 lint 检查，MUST NOT 再作为判断规则送模型。`design-no-speculative-extension` 的 block 阈值 SHALL 为 0.3；`direct-route-respects-specs` 的 block 阈值 SHALL 先为 0（只 review 不拦）。项目 `openspec/judgments.yaml` 只写本项目的规则；与通用规则同 id 时 SHALL 以项目规则为准。通用规则的 `enforces` MUST 按项目的 `AGENTS.md` 与 `openspec/config.yaml` 检查；没有 `AGENTS.md` 的旧项目 SHALL 回退到 `CLAUDE.md`。

#### Scenario: 迁移后项目规则文件变短
- **WHEN** 项目甲与项目乙的 `judgments.yaml` 不写任何通用规则
- **THEN** 运行判断时「写明不做什么」「不做过度设计」两条照常出现，「决策附备选」由 `lint/design` 检查

#### Scenario: 运行判断时的通用规则
- **WHEN** 在没有自己判断规则的项目运行 `rulemason judge --change x`
- **THEN** 只有 `proposal-states-non-goals` 与 `design-no-speculative-extension` 两条通用规则参与评估

#### Scenario: 项目收紧一条通用规则
- **WHEN** 项目在自己的 `judgments.yaml` 写了同 id 的 `proposal-states-non-goals` 并调高 block 阈值
- **THEN** 该项目使用自己的版本，其他项目仍用通用版本

#### Scenario: 过度设计被拦下
- **WHEN** design 为本次不使用的需求构建插件机制，`design-no-speculative-extension` 得分低于 0.3
- **THEN** 判断结果为 block

#### Scenario: 直接改动的通用规则
- **WHEN** 在没有自己判断规则的项目运行 `rulemason judge --direct note.md`
- **THEN** 只有 `direct-route-respects-specs` 一条通用规则参与评估，得分再低也只给 review

## ADDED Requirements

### Requirement: 判断直接改动说明

`rulemason judge` SHALL 接受 `--direct <文件>`：读取一份直接改动说明，先检查它有「要做什么」「改哪些文件」「主规格与检索命中」「判路与理由」四段，缺任一段 SHALL 记一条 block（`lint/direct`）且不送模型；四段齐全时 SHALL 用 `target: direct` 的规则（通用规则加项目规则）评估，输出与退出码同 `--change`。规则的 `target` SHALL 可取 `direct`。说明文件可以在项目之外。

#### Scenario: 说明缺一段
- **WHEN** 说明只有「要做什么」「改哪些文件」两段，运行 `rulemason judge --direct note.md`
- **THEN** 输出一条 `lint/direct` 的 block，写明缺哪两段，退出码非 0，不调用模型

#### Scenario: 说明合格
- **WHEN** 四段齐全，项目另有一条 `target: direct` 的红线规则，运行 `rulemason judge --direct note.md`
- **THEN** 通用规则与这条项目规则参与评估，按得分给出 pass、review 或 block

#### Scenario: 只看格式
- **WHEN** 运行 `rulemason judge --direct note.md --lint-only`
- **THEN** 只检查四段是否齐全，不需要 key 与网络
