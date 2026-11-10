## ADDED Requirements

### Requirement: 产品产物结构与夹具同步
共享契约正文 SHALL 注明：改工程交接用产品产物且项目选用了结构预设时，同一次 change 须同步 requirements / 夹具并跑 `result-check`；结构命中 MUST NOT 被写成业务验证通过。种子文件名 SHALL 含 `product-artifact.*.json`（与 `prose-hygiene.*.json` 并列），仅首次写入。

#### Scenario: 契约提到产物结构预设
- **WHEN** 打开 `rules/result-check-contracts.md`
- **THEN** 正文含 `product-artifact` 预设或种子说明，并写明结构命中不等于业务验证通过
