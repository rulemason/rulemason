# product-artifact-caution Specification

## Purpose

工程向产品产物（需求、故事、验收、验证证据）的共享写作规矩：可检验标准、非目标、证据边界；自动分发；非作者判别、非商业成功自动评分。

## Requirements

### Requirement: 产品产物规矩自动分发
本仓库 SHALL 提供自研 `rules/product-artifact-caution.md`，经 `init`/`update` 对接入项目必复制。正文 MUST 要求：成功标准可检验、写明非目标、区分证据与推断、禁止编造用户引言或指标、不把结构提示说成产品验证通过。MUST 写明：确定性结构检查仅经 `rulemason result-check`（含 `--preset product-artifact.*`）；`init`/`update` 只分发规矩与缺失种子，不扫仓。MUST 归因行为启发来源（MIT `pm-skills` 固定 commit；若提及 PMS 仅说明想法启发且未再分发 CC BY-NC-SA 材料）。MUST NOT 嵌入第三方 skill 全文或模板。MUST NOT 列入默认判断红线。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/product-artifact-caution.md` 存在且含可检验标准与证据边界说明
