## ADDED Requirements

### Requirement: 巡检核对最近归档的检查点记录

`rulemason check` 的巡检 SHALL 有一项「最近归档的检查点记录」：取 `openspec/changes/archive/` 里日期前缀最新的那一天归档的全部 change，逐个检查目录里有没有 `verification.md`，以及文件里是否同时写到审查（「审查」或 review）与测试（「测试」或 test）。缺文件或缺其中一项时 SHALL 列出 change 名与缺什么。这一项 MUST NOT 影响退出码与下一步；没有已归档 change 时写「一致」。更早的归档 MUST NOT 被检查。

#### Scenario: 最近一次归档带完整汇报
- **WHEN** 最新归档的 change 有 `verification.md`，其中写了独立审查两轮的结果与 pytest 的结果
- **THEN** 这一项写「一致」

#### Scenario: 最近一次归档没有汇报
- **WHEN** 最新归档的是 `2026-11-01-migrate-x`，目录里没有 `verification.md`
- **THEN** 这一项列出「2026-11-01-migrate-x：没有 verification.md」，退出码与下一步不变

#### Scenario: 汇报缺审查
- **WHEN** 最新归档的 change 有 `verification.md`，只写了测试结果，没有提到审查
- **THEN** 这一项列出该 change 缺审查记录

#### Scenario: 同一天归档了两个
- **WHEN** 最新的日期下归档了两个 change，其中一个没有 `verification.md`
- **THEN** 只列出缺的那一个；更早日期的归档即使没有汇报也不列出

#### Scenario: 表格写法的汇报
- **WHEN** `verification.md` 没有小节标题，只有一张写着「独立审查第一轮」「测试：44 项通过」的表格
- **THEN** 这一项写「一致」
