## MODIFIED Requirements

### Requirement: 中文排版与 result-check 契约规则必复制并被入口引用
`init` 与 `update` SHALL 把 `rules/cjk-typography.md` 与 `rules/result-check-contracts.md` 复制进项目 `.rulemason/rules/`（所有接入项目，与 code-style 同级必复制），清单记录校验值。`AGENTS.md` 的 Code style 标记块 SHALL 列出这两份副本并写明阅读场合；Claude 入口块与新生成的 OpenCode 配置 MUST NOT 导入它们。`check` MUST 在副本缺失或被手改时非 0 退出。既有检查项与无新规则时的项目行为 MUST 在 `update` 补齐后恢复一致。

#### Scenario: 无前端项目也拿到两份规则
- **WHEN** 仅有 Python、无前端的项目运行 `rulemason update`
- **THEN** `.rulemason/rules/` 含 `cjk-typography.md` 与 `result-check-contracts.md`，`AGENTS.md` 的 Code style 块出现对二者的引用

#### Scenario: 手改排版规则副本被查出
- **WHEN** 项目手改 `.rulemason/rules/cjk-typography.md` 后运行 `rulemason check`
- **THEN** 以非 0 退出并报告该副本不一致

#### Scenario: 升级补齐不破坏旧命令表
- **WHEN** 已接入项目从无这两份规则的版本升级并 `rulemason update --yes`
- **THEN** 补上两份副本与 `AGENTS.md` Code style 块里的引用，项目命令表与红线正文不被改写

## ADDED Requirements

### Requirement: check 在判断条件刚满足时提示启用

`rulemason check` 在项目没有 `openspec/judgments.yaml`、启用判断的条件已满足（有 git、已归档至少 3 个 change），且「已归档 change」正好是 3 或「接入后归档 change」正好是 1 时，SHALL 在报告第一行之后给一条启用提示：本机没有 key 时提示运行 `rulemason key` 并给出申请地址；已有 key 时提示在 AI 工具中运行 `/rulemason` 并说明要启用判断。两种提示 SHALL 附一句判断审 OpenSpec 方案、界面文案与直接改动的说明。其余情况 MUST NOT 给这条提示，它也 MUST NOT 改变下一步与退出码。

#### Scenario: 第 3 个归档且没有 key
- **WHEN** 项目有 git，已归档 3 个 change，没有 `openspec/judgments.yaml`，本机未配置 key
- **THEN** 报告第一行之后有一条配置 key 的提示，含申请地址与判断覆盖范围；`next.code` 与退出码不变

#### Scenario: 接入后第一次归档且已有 key
- **WHEN** 接入时已归档 60 个 change，接入后归档了 1 个，没有 `openspec/judgments.yaml`，本机已有 key
- **THEN** 报告第一行之后有一条提示，请在 AI 工具中运行 `/rulemason` 并说明要启用判断，附判断覆盖范围

#### Scenario: 之后不再提示
- **WHEN** 已归档 4 个、接入后归档 2 个，仍未启用判断
- **THEN** 报告里没有这条提示

#### Scenario: 判断已启用
- **WHEN** 项目有 `openspec/judgments.yaml`，接入后归档了 1 个
- **THEN** 报告里没有这条提示
