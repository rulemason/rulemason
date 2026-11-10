# Spec Delta

## ADDED Requirements

### Requirement: 编码审慎规矩自动分发
本仓库 SHALL 提供 `rules/agent-coding-caution.md`，经 `init`/`update` 对所有接入项目必复制。正文 MUST 自研行为原则，MUST NOT 嵌入第三方 skill 全文，MUST NOT 在规矩正文中写第三方仓库名、URL 或 commit，MUST NOT 实现为 result-check 类型。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/agent-coding-caution.md` 存在且含自研原则，且正文不含第三方仓库名、URL 或 commit
