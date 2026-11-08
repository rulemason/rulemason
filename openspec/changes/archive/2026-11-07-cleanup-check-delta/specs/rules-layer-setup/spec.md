## MODIFIED Requirements

### Requirement: 先识别项目再做事

每次运行 SHALL 先运行 `rulemason check --json`，按 `next.code` 决定这次做什么。除存量清理外，SHALL 把其中的 `text`（报告全文）原样放进汇报。存量清理的展示见「清理时只展示巡检变化」。项目没有 `.rulemason.yaml` 时，skill MUST 停下，提示先运行 `rulemason init`，不写任何文件；`.rulekit.yaml` 不再被识别，有它的项目同样按没有清单处理。需要替用户运行 `rulemason init` 时，SHALL 先运行 `rulemason init --plan` 把计划给用户看，用户同意后再运行。本机没有 `rulemason` 命令时 MUST 给出安装命令并停下。

#### Scenario: 纯 Python 项目
- **WHEN** 在已运行过 `rulemason init` 的项目丙根目录运行 `/rulemason`，且这次不是存量清理
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

## ADDED Requirements

### Requirement: 清理时只展示巡检变化

存量清理可以继续时，汇报 MUST NOT 包含识别表，MUST NOT 列出各层里写着「齐全」的行，也 MUST NOT 列出巡检里值为「一致」的项。这次对话的第一次清理 SHALL 写一行 `next.code`，并列出巡检里值不是「一致」的项及其子行、各层里不是「齐全」的行；汇报第一行不是「日常巡检：一切一致」时 SHALL 带上该行。同一对话里再次清理时，这些行没变 SHALL 只写「巡检与这次清理开始时相同」；有变 SHALL 只列变了的行。收尾同样遵守，MUST NOT 以报告全文开头。MUST NOT 把上次巡检写入文件。新对话的第一次清理重新列出不是「一致」的项。`next.code` 要停下时 MUST 把 `text` 原样放进汇报，不诊断也不改文件。

#### Scenario: 这次对话第一次进入模块
- **WHEN** 这次对话还没有做过存量清理，`next.code` 为 `none`，巡检里有一项不是「一致」，其余为「一致」，各层都是「齐全」
- **THEN** 汇报有一行 `none` 和那一项及其子行，没有识别表，没有「齐全」和「一致」的行，然后是该模块的计划

#### Scenario: 下一个模块的巡检没变
- **WHEN** 同一对话里进入下一个模块，`next.code` 仍为 `none`，上次列出的那些行都没变
- **THEN** 汇报写「巡检与这次清理开始时相同」，不重复那些行，没有识别表，然后是计划

#### Scenario: 同一对话里巡检变了
- **WHEN** 同一对话里再次清理，有一项从「一致」变成了别的内容，其余没变
- **THEN** 只列出变了的那一项，不贴识别表，也不重复没变的行

#### Scenario: 入口要停下
- **WHEN** 用户要求存量清理，`next.code` 为 `update`
- **THEN** 汇报原样包含 `text`，不诊断，不改文件

#### Scenario: 收尾不把全文放在最前
- **WHEN** 同一对话里一个模块已经做完，收尾重算下一个
- **THEN** 收尾不以报告全文开头；巡检行没变时写「巡检与这次清理开始时相同」

#### Scenario: 不保存上次巡检
- **WHEN** 清理汇报按上面的规则少贴了巡检
- **THEN** 仓库和 `.rulemason/` 都不新增上次巡检的记录
