# Proposal

## Why

两份公开 PM skill 仓库提供了大量「产品需求 / 验收 / 证据 / 规划评审」工作流。rulemason 已是工程向的规则分发与确定性 `result-check` 工具：需要的是**可进共享层的最小融合**，而不是把 rulemason 变成全套 PM 助手。用户已确认实施 **A+B**。

## What Changes

- **新增共享规矩（自研正文）**：写工程交接用的产品产物（PRD/用户故事/验收/验证证据）时阅读——强调可检验成功标准、非目标、证据边界、禁止编造用户/指标；经 `init`/`update` **自动分发**，**不**自动扫仓、**不**默认 CI 阻断、**不**进默认判断红线。
- **可选结构预设（复用既有类型）**：包内 `product-artifact.hint|strict`，用 `pattern`（标题锚定）检查约定小节；默认 hint；严格显式。`--preset hint|strict` **仍**为 prose-hygiene，不偷换。
- **最小兼容增强**：`must_contain` / `pattern` 支持可选 `severity`（缺省 `strict` 保持旧「缺失即失败」）；非法 severity → 输入错误；提示不吞失败/无法判断/输入错误。
- **不引入**：付费模型、REA 运行时依赖、整包 PM slash 命令、商业成功/主观优先级自动打分、新 CLI 子命令。

## Capabilities

### New Capabilities

- `product-artifact-caution`：工程向产品产物写作与证据边界的共享规矩（自研；行为启发注明来源）。

### Modified Capabilities

- `rulekit-cli`：必复制新规矩；可选 result-check 种子预设（幂等、不覆盖用户配置）；入口引用。
- `run-result-check`：`must_contain`/`pattern` 的 severity；`product-artifact.*` 预设入口；旧 prose 预设语义不变。
- `result-check-contracts`：一句指向产品产物字段与夹具同步约定。

## Impact

- 旧项目：未声明新产品检查时行为与退出码不变；`--preset hint|strict` 仍为文案卫生。
- 许可证：`phuryn/pm-skills` MIT 可作行为启发；`deanpeters/Product-Manager-Skills` 为 **CC BY-NC-SA 4.0**——**不得**把其正文/模板/词表拷进 Apache-2.0 的 rulemason 包；只允许独立改写想法并归因。
- REA：仅作只读分析证据；不进产品依赖。

## Non-Goals

- 不移植完整 42/77 条 PM 技能或 marketplace 命令面。
- 不把主观产品决策、市场研究结论、简历/NDA/定价策略写成可自动验证。
- 本轮不归档、不推送、不发版（仅本地提交）。
