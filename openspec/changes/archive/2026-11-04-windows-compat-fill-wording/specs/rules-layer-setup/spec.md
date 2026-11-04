## ADDED Requirements

### Requirement: 补齐计划改动的文件随升级一起提交

skill 解读 `rulemason update` 或其试运行结果时 SHALL 说明：补齐计划写进项目文件（如 `openspec/config.yaml` 追加的基础条目、新建的 ruff 配置）的内容来自 rulemason 基础配置，属于这次升级，提交升级时 SHALL 与副本、`.rulemason.yaml` 一起提交；MUST NOT 把它们说成项目自己加的规则。

#### Scenario: 升级后整理提交
- **WHEN** 升级后工作区有 `.rulemason/` 副本、`.rulemason.yaml` 与 `openspec/config.yaml` 多出的一条 design 基础条目，skill 汇报巡检结果
- **THEN** 汇报把 `openspec/config.yaml` 与副本一起列为「升级产出，提交时一起带上」，并说明这一行来自 rulemason 基础版；skill 自己不提交

#### Scenario: 无关改动仍不碰
- **WHEN** 同一工作区里还有用户自己改的 `AGENTS.md` 命令表
- **THEN** skill 不把它算进升级提交，列在「没碰的东西」里
