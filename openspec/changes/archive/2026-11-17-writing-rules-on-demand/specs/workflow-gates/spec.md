## MODIFIED Requirements

### Requirement: 归档后提示一次启用判断

归档完成后，AI SHALL 运行 `rulemason check`；报告第一行之后有启用判断的提示时，AI SHALL 在汇报末尾原样转述一次。提示何时出现、写什么由 `check` 决定（见 `rulekit-cli`「check 在判断条件刚满足时提示启用」），检查点正文 MUST NOT 另写这些条件。AI MUST NOT 代为配置 key 或启用判断；`check` 没有给出提示时 MUST NOT 自己提示。

#### Scenario: 第 3 个归档且没有 key
- **WHEN** 项目归档第 3 个 change，没有 `openspec/judgments.yaml`，本机未配置 key
- **THEN** 汇报末尾有一句配置 key 的提示与申请地址，附判断覆盖范围

#### Scenario: 接入后第一次归档且已有 key
- **WHEN** 接入时已归档 60 个 change，接入后归档第 1 个，没有 `openspec/judgments.yaml`，本机已有 key
- **THEN** 汇报末尾提示在 AI 工具中运行 `/rulemason` 并说明要启用判断，附判断覆盖范围

#### Scenario: 之后的归档
- **WHEN** 同一项目接入后归档第 2 个 change，仍未启用判断
- **THEN** 汇报不再提示

#### Scenario: 判断已启用
- **WHEN** 项目有 `openspec/judgments.yaml`，接入后归档第 1 个 change
- **THEN** 汇报不提示
