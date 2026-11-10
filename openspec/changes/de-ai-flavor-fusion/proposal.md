# Proposal

## Why

需要在「去 AI 味 / 表达更自然」上加强可解释能力，并把 anti-slop 候选 `prose_hygiene` 与社区整理的 Karpathy-inspired **编码行为**指南分轨融合。若把编码过程规则硬塞进禁词检测，或把禁破折号宣传成去 AI 味，会误导且误报高。本 change **仅规划**：等用户确认后再实现。

## What Changes

（确认后才实施；本轮不改运行时代码。）

- **文案轨**：在候选 `prose_hygiene` 上修订推荐短名集——保留 `chatbot_closer` / `signpost_opener` / `not_just_contrast`；将 `em_dash` 移出推荐默认组合（删除或降为高级可选，待决）；规则层强调非作者判别、不自动改事实。
- **编码轨**：新增自研共享规矩（建议 `rules/agent-coding-caution.md`），意译四原则（先想清、简单、外科手术、目标可验证），经 init/update 分发；**不做**新 result-check 类型。
- **明确不做**：搬迁对方 skill/安装器/EXAMPLES；复制词表；付费「AI 味」评分；默认 CI 全局阻塞；宣称 Karpathy 官方；在未确认前推送/合并 `bb187b2`。

## Capabilities

### New Capabilities

- `agent-coding-caution`：共享编码审慎规矩（规则层）。

### Modified Capabilities

- `prose-hygiene`：修订短名推荐集与文档边界（相对候选实现）。
- `run-result-check`：仅当确认保留/调整 `prose_hygiene` 短名时改检查契约。
- `rulekit-cli`：若确认必复制新规矩文件则改 init/update 清单。

## Impact

- 候选提交 `bb187b2` 保留为历史候选，不作为已批准上线。
- 确认后的实现应自 `main` 重做或另提交修订，保持旧 API：未声明 `prose_hygiene` 则行为不变。
- 第三方仅行为启发 + 归因；不嵌入对方正文（尤其对方缺 LICENSE 文件时）。

## Non-goals

- 本轮不实现、不勾实现任务为完成、不归档、不推送、不发版、不改 Yaomancy/Notion。
- 不把编码过程规则伪装成确定性文案检测。
