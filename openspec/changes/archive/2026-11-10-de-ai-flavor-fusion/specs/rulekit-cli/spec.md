## ADDED Requirements

### Requirement: 文案卫生与编码审慎规矩必复制
`init` 与 `update` SHALL 把 `rules/prose-hygiene.md` 与 `rules/agent-coding-caution.md` 复制进 `.rulemason/rules/`（所有接入项目必复制），入口块 SHALL 引用二者并注明阅读场合。清单记录校验值；手改副本时 `check` 非 0。

#### Scenario: Go 项目也拿到两份
- **WHEN** 仅有 `go.mod` 的项目 `rulemason init --yes`
- **THEN** `.rulemason/rules/` 含 `prose-hygiene.md` 与 `agent-coding-caution.md`

### Requirement: result-check 预设种子幂等
`init` 与 `update` SHALL 在 `.rulemason/result-check/` 下种入 `prose-hygiene.hint.json` 与 `prose-hygiene.strict.json`：**仅当目标文件不存在时写入**；已存在则保留用户内容，不得覆盖。这些种子 MUST NOT 进入与共享规则相同的「落后必覆盖」校验集。

#### Scenario: 重复 update 不覆盖种子
- **WHEN** 用户改过 `.rulemason/result-check/prose-hygiene.hint.json` 后再 `rulemason update --yes`
- **THEN** 该文件内容保持用户修改
