## ADDED Requirements

### Requirement: 产品产物规矩必复制
`init` 与 `update` SHALL 把 `rules/product-artifact-caution.md` 复制进 `.rulemason/rules/`（所有接入项目必复制），入口块 SHALL 引用并注明阅读场合。清单记录校验值；手改副本时 `check` 非 0。

#### Scenario: Go 项目也拿到
- **WHEN** 仅有 `go.mod` 的项目 `rulemason init --yes`
- **THEN** `.rulemason/rules/` 含 `product-artifact-caution.md`

### Requirement: 可选产物结构提示种子幂等
`init`/`update` SHALL 在 `.rulemason/result-check/` 下种入 `product-artifact.hint.json` 与 `product-artifact.strict.json`：**仅当目标文件不存在时写入**；已存在 MUST NOT 覆盖。种子 MUST NOT 进入落后必覆盖校验集。预设 MUST 默认 hint 语义（严格另文件）；MUST NOT 默认启用「商业成功」类主观规则。`remove` SHALL 删除已知种子文件名（含 prose 与 product-artifact）。MUST NOT 声称 `init`/`update` 本身检查文档正文。

#### Scenario: 重复 update 不覆盖用户种子
- **WHEN** 用户改过该种子后再 `rulemason update --yes`
- **THEN** 文件内容保持用户修改

#### Scenario: remove 删除产物结构种子
- **WHEN** 已种入 `product-artifact.*.json` 的项目运行 `rulemason remove --yes`
- **THEN** 这些种子文件被删除
