# agent-coding-caution Specification

## Purpose

共享「编码审慎」规矩：自研短名意译先想清、简单优先、外科手术改动、目标可验证；用于 AI/人阅读，不是文案检测器。

## ADDED Requirements

### Requirement: 编码审慎规矩只住本仓库一份
本仓库 SHALL 提供 `rules/agent-coding-caution.md`（文件名以实施时最终为准），用自拟表述写明四条：假设与歧义先澄清、避免投机扩展与过度抽象、只改请求所需并只清理自己产生的废弃物、把任务落到可验证成功标准。MUST 归因行为启发来源（社区整理的 Karpathy-inspired 指南及其指向的公开观察），MUST NOT 大段照抄第三方 skill 原文，MUST NOT 宣称其为 Karpathy 官方项目，MUST NOT 宣称可判定 AI 作者。

#### Scenario: 项目读到规矩
- **WHEN** 已接入项目按决议运行 `rulemason update` 后打开该副本
- **THEN** 文件存在且含四条意译与归因、并写明适用于写码/改码场合而非文案禁词检测

### Requirement: 不做编码过程的伪确定性检查
本期 MUST NOT 将「是否提问」「是否越界改码」「成功标准是否足够」实现为 `result-check` 短名或禁词表。此类要求留在规则层与现有 workflow/审查流程。

#### Scenario: 无过程伪检查类型
- **WHEN** 查阅 result-check 已知类型列表（实施完成后）
- **THEN** 不存在将 K1–K4 过程判断伪装成静态命中的类型
