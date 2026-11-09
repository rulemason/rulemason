## ADDED Requirements

### Requirement: 中文排版与 result-check 契约规则必复制并被入口引用
`init` 与 `update` SHALL 把 `rules/cjk-typography.md` 与 `rules/result-check-contracts.md` 复制进项目 `.rulemason/rules/`（所有接入项目，与 code-style 同级必复制），清单记录校验值。AGENTS / Claude / OpenCode 等入口中的 code-style 类标记块 SHALL 引用这两份副本（可注明阅读场合）。`check` MUST 在副本缺失或被手改时非 0 退出。既有检查项与无新规则时的项目行为 MUST 在 `update` 补齐后恢复一致。

#### Scenario: 无前端项目也拿到两份规则
- **WHEN** 仅有 Python、无前端的项目运行 `rulemason update`
- **THEN** `.rulemason/rules/` 含 `cjk-typography.md` 与 `result-check-contracts.md`，入口块出现对二者的引用

#### Scenario: 手改排版规则副本被查出
- **WHEN** 项目手改 `.rulemason/rules/cjk-typography.md` 后运行 `rulemason check`
- **THEN** 以非 0 退出并报告该副本不一致

#### Scenario: 升级补齐不破坏旧命令表
- **WHEN** 已接入项目从无这两份规则的版本升级并 `rulemason update --yes`
- **THEN** 补上两份副本与入口引用，项目命令表与红线正文不被改写
