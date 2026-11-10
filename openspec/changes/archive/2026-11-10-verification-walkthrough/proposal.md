# Proposal

## Why

外部调研材料（外部归档调研对象 / 外部验证走查调研对象）里有可检验验收与验证走查的有用原则，但整套编排器与 rulemason「共享规矩 + 检查点」定位冲突。需要在不搬入 外部调研材料 运行时的前提下，把可增益点改造成自研指导与可选检查。

## What Changes

- 自研增补产品产物规矩中的「验证走查」原则（期望可观察 → 确认 → 记录差距；禁止编造已测），（规矩正文不写外部来源）。
- 新增可选 `result-check` 预设 `verification-walkthrough.hint|strict`（默认宣传 hint）；复用既有 severity/hint/strict，不新子命令。
- `init`/`update` 只分发规矩与（缺失时）种子，**不**自动扫仓、不改因缺走查小节而单独失败的 `check` 行为。
- 不做：外部调研材料 命令套件、多代理编排、Claude Agent SDK、MCP、安装器写 IDE home、`.planning/` 状态机、autonomous 自动推进、复制第三方正文/模板/代码。
- 不做：对本期以外的 REQ-ID 强制图式（待决，默认推迟）。
- **BREAKING**：无。保持 0.8.35 兼容；新能力为加法。

## Capabilities

### New Capabilities

- `verification-walkthrough-caution`：验证走查指导的分发边界，以及可选结构预设（结构存在 ≠ 质量合格）。

### Modified Capabilities

- `product-artifact-caution`：产品产物规矩正文增加验证走查相关原则，并保持「只分发不扫描」。
- `run-result-check`：登记新预设 id 与 hint/strict 语义（与既有 product-artifact 预设同模式）。

## Impact

规则正文、`shared`/`cli` 预设表、result-check 模板与测试；无新运行时依赖。上游对照基准见 design（双仓差异与 next/main tip 待决）。
