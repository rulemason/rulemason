## REMOVED Requirements

### Requirement: 归档够 3 个时提示一次配置 key
**Reason**: 只在「已归档正好 3 个、本机没有 key」时提示，接入时归档已多于 3 个的项目永远触发不到，已有 key 的项目也收不到「还要启用」的提示。
**Migration**: 由「归档后提示一次启用判断」取代，覆盖已有 key 与接入后第一次归档两种情况。

## ADDED Requirements

### Requirement: 归档后提示一次启用判断

归档完成后，`rulemason check --json` 的「判断」一行显示条件已满足且未启用，并且「已归档 change」正好是 3 或「接入后归档 change」正好是 1 时，AI SHALL 在汇报末尾提示一次：本机没有 key 时提示运行 `rulemason key`（申请地址 https://typesafe.ai/ ）；已有 key 时提示在 AI 工具中运行 `/rulemason` 并说明要启用判断。两种提示都 SHALL 附一句：判断只审 OpenSpec 方案与界面文案。AI MUST NOT 代为配置 key 或启用判断；其余情况 MUST NOT 提示。

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
