## ADDED Requirements

### Requirement: 编码审慎与文案卫生规矩的分发（确认后）
在用户确认分发策略后，`init`/`update` SHALL 将 `rules/prose-hygiene.md` 与 `rules/agent-coding-caution.md`（最终文件名以实施为准）按决议复制进 `.rulemason/rules/`，入口块可注明阅读场合（文案检查显式启用时 / 写码改码时）。`check` MUST 在已记录的副本被手改时非 0 退出。MUST NOT 因新增规矩文件而改变未使用 `prose_hygiene` 的项目的 result-check 行为。

#### Scenario: 补齐副本不改变旧检查
- **WHEN** 已接入项目升级并 `rulemason update` 补上上述规矩文件，且其 requirements 未声明 `prose_hygiene`
- **THEN** 既有 result-check 退出行为与升级前一致
