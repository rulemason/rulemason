# Proposal

## Why

分发规矩与规格里仍要求或保留第三方来源标识；同时编码审慎规矩缺少可测先行、根因、完成证据与审阅核实四条过程原则。需要在同一版本去掉来源痕迹并补齐原则。

## What Changes

- 删除分发规矩（编码审慎、文案卫生、产品产物）中的来源小节；README 删除致谢段；代码注释与主规格去掉须归因/须写来源的要求。
- `agent-coding-caution` 增补四条自研原则：可测先行、先根因再修、完成须有当次证据、审阅反馈先核实；不新增 result-check 预设，不进默认红线。
- 测试改为负向断言：分发规矩正文不含第三方仓库名、URL、commit。
- 历史归档：删除分析 artifacts 与完整补丁；正文改写去专名；含第三方名的归档目录改为中性名。
- 版本 **0.8.37**。
- **不做**：合并/打 tag/发版；付费判断；新增预设；在规矩正文写任何第三方名或链接；改写已推送 git 历史。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-coding-caution`：增补四条原则；禁止规矩正文写第三方来源。
- `product-artifact-caution`：去掉须归因要求；禁止规矩正文写第三方来源。
- `verification-walkthrough-caution`：去掉须归因要求；禁止规矩正文写第三方来源。

## Impact

- `rulemason update` 覆盖用户项目中的规矩副本后，来源小节消失；新增四条编码原则可见。
- `result-check` 预设与退出码不变。
- 旧版已发布包不 yank。
