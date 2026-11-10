# Spec Delta

## MODIFIED Requirements

### Requirement: 产品产物规矩自动分发
本仓库 SHALL 提供自研 `rules/product-artifact-caution.md`，经 `init`/`update` 对接入项目必复制。正文 MUST 要求：成功标准可检验、写明非目标、区分证据与推断、禁止编造用户引言或指标、不把结构提示说成产品验证通过。MUST 写明：确定性结构检查仅经 `rulemason result-check`（含 `--preset product-artifact.*`）；`init`/`update` 只分发规矩与缺失种子，不扫仓。MUST NOT 在规矩正文中写第三方仓库名、URL、commit 或许可证代号。MUST NOT 嵌入第三方 skill 全文或模板。MUST NOT 列入默认判断红线。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/product-artifact-caution.md` 存在且含可检验标准与证据边界说明，且正文不含第三方仓库名、URL 或 commit
