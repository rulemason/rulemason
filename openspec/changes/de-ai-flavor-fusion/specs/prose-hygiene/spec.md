# prose-hygiene Specification

## Purpose

面向人读文案的可选卫生规矩与检查短名：强调显式启用、非作者判别、推荐短名不含「破折号=去 AI 味」。

## ADDED Requirements

### Requirement: 文案卫生规矩与推荐短名
本仓库 SHALL 提供 `rules/prose-hygiene.md`，说明检查类型 `prose_hygiene` 须在 requirements 中显式列出 `rules`。推荐短名 SHALL 包含 `chatbot_closer`、`signpost_opener`、`not_just_contrast`。`em_dash` 若实现存在，MUST 在文档中标为高误报可选，MUST NOT 作为「去 AI 味」的推荐默认。MUST 声明非作者/生成来源判别，MUST NOT 要求工具自动改写事实或引用。

#### Scenario: 推荐组合不含破折号叙事
- **WHEN** 阅读 `rules/prose-hygiene.md` 的推荐启用说明
- **THEN** 推荐列表含上述三短名，且破折号规则不作为去 AI 味默认手段

#### Scenario: 显式启用
- **WHEN** 项目未在 requirements 声明 `prose_hygiene`
- **THEN** 不得因套话或破折号形态自动失败
