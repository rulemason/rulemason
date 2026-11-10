# Proposal

## Why

在可解释的「去套话」与编码审慎指导上开箱可用：规则随 init/update 自动分发；文案检查默认只提示不阻断 CI；严格阻断由用户显式选择。避免把禁破折号或编码过程规则伪装成作者判别。

## What Changes

- **文案轨** `prose_hygiene`：推荐短名 `chatbot_closer` / `signpost_opener` / `not_just_contrast`；`em_dash` 仅高级可选（默认关闭）。新增 `severity`：`hint`（默认，命中为「提示」、不单独导致非零）/ `strict`（命中失败非零）。非法配置仍 exit 2；其他类型失败/无法判断仍非零；提示不得吞掉其他错误。
- **入口**：打包 hint/strict 预设；init/update **仅在缺失时**种入 `.rulemason/result-check/prose-hygiene.*.json`（不覆盖已有）；CLI `--preset hint|strict` 可直接跑（优先项目种子，否则包内模板）。**不**改 `rulemason check` 退出语义、**不**默认扫仓阻断。
- **编码轨**：自研 `rules/agent-coding-caution.md` 必复制；不做 result-check 类型。
- **规则层**：`rules/prose-hygiene.md` 必复制；入口块默认提示阅读场合与 hint/strict。
- **不做**：作者判别、大词表、`--fix`、付费模型、Yaomancy、推送/发版；不原样强推 `bb187b2`。

## Capabilities

### New Capabilities

- `agent-coding-caution`：编码审慎共享规矩。
- `prose-hygiene`：文案卫生规矩与推荐短名。

### Modified Capabilities

- `run-result-check`：`prose_hygiene` 类型、`severity`、提示状态与退出码交互。
- `rulekit-cli`：必复制两份规矩；种子预设幂等；CLI preset。

## Impact

- 未声明 `prose_hygiene` 的旧 requirements：行为与退出码不变。
- 旧 cjk/field 失败仍为 1；输入错误仍为 2。
- 第三方仅行为启发与归因。
