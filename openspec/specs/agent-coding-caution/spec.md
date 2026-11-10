# agent-coding-caution Specification

## Purpose

共享编码审慎规矩（自研）：先澄清、简单优先、外科手术改动、目标可验证，以及可测先行、先根因再修、完成须有当次证据、审阅反馈先核实；自动分发；非 result-check。

## Requirements

### Requirement: 编码审慎规矩自动分发
本仓库 SHALL 提供 `rules/agent-coding-caution.md`，经 `init`/`update` 对所有接入项目必复制。正文 MUST 自研行为原则（含先澄清、简单优先、外科手术改动、目标可验证，以及可测先行、先根因再修、完成须有当次证据、审阅反馈先核实），MUST NOT 嵌入第三方 skill 全文，MUST NOT 在规矩正文中写第三方仓库名、URL 或 commit，MUST NOT 实现为 result-check 类型，MUST NOT 列入默认判断红线。

#### Scenario: update 后可读
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** `.rulemason/rules/agent-coding-caution.md` 存在且含可测先行与完成证据相关原则，且正文不含第三方仓库名、URL 或 commit

### Requirement: 编码审慎不自动扫仓也不新增强制预设
`init`/`update`/`check` MUST NOT 因缺少失败测试记录或调试笔记而自动扫描仓库或单独失败。本期 MUST NOT 新增专用于可测先行或根因排查的 result-check 预设；既有 `verification-walkthrough.*` 语义不变。

#### Scenario: update 不因可测先行扫仓
- **WHEN** 项目运行 `rulemason update`
- **THEN** 工具只刷新规矩副本（及既有缺失种子策略），不遍历测试文件断言红绿循环
