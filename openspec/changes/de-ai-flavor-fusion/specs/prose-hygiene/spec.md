# prose-hygiene Specification

## Purpose

面向人读文案的可选卫生规矩：推荐短名默认用于提示模式；破折号仅高级可选；非作者判别。

## ADDED Requirements

### Requirement: 文案卫生规矩自动分发
本仓库 SHALL 提供 `rules/prose-hygiene.md`，经 `init`/`update` 必复制到接入项目。正文 MUST 写明推荐短名 `chatbot_closer`、`signpost_opener`、`not_just_contrast`；`em_dash` 为高级可选且默认关闭；默认 `severity=hint` 只提示不单独阻断；`strict` 由用户显式选择。MUST 声明非作者判别，MUST NOT 要求自动改写事实。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/prose-hygiene.md` 存在且含推荐短名与 hint/strict 说明
