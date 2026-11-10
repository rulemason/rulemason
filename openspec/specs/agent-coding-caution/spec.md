# agent-coding-caution Specification

## Purpose

共享编码审慎规矩（自研意译）：先澄清、简单优先、外科手术改动、目标可验证；自动分发；非 result-check。

## Requirements

### Requirement: 编码审慎规矩自动分发
本仓库 SHALL 提供 `rules/agent-coding-caution.md`，经 `init`/`update` 对所有接入项目必复制。正文 MUST 自研意译四条行为原则，MUST 归因社区整理的 Karpathy-inspired 指南（非官方）与公开观察链接，MUST NOT 嵌入第三方 skill 全文，MUST NOT 实现为 result-check 类型。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/agent-coding-caution.md` 存在且含四条意译与非官方归因
