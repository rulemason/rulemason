# Proposal

## Why

中文产品文案常混排拉丁字母与数字；空格、全角数字、叠用标点一类问题可用本地确定性规则检出，但现有 `result-check` 只有通用 `pattern`，难表达剥离 Markdown / URL / 代码后再检、以及产品名白名单。外部「中文文案排版指北」（MIT）的规则表已人工分类；需要在 rulemason 内**自研**可配置检查，而不是抄指北正文或依赖第三方分析器。

## What Changes

- 在 `result-check` 增加检查类型 `cjk_typography`：对调用方提供的正文做可开关的中文排版规则集。
- 首批规则（短名自拟）：禁用全角数字；禁止叠用标点（允许恰好一次的 `？！`/`?!`/`！？`/`!?`）；中英空格；中数空格；默认单位前空格与 °/% 不加空格；全角标点旁不加空格。
- 固定假阳性处理：检查前剥离围栏/行内代码、裸 URL、Markdown 链接/图片**目标**、行内 HTML；**可见链接文案参检**；支持产品名 allowlist。
- 失败报告带规则短名与原文位置；非法配置 → 输入错误（exit 2）；无该类型时既有检查不变。
- 对本仓库 README 与 `rules/` 跑一次样例并记入 verification；包版本 bump 至 **0.8.32**（含 README CI 钉版本）。
- **不做**：照抄指北长文；依赖 Promptfoo / Rea / Cedar / Ruler / pangu / autocorrect 代码；本期做专名大小写、生造缩写、中文语境半角标点、争议链接/引号规则；本期不改 `copy-voice`/`judge` 语义；本期不把本检查默认挂进 `rulemason check` 巡检。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `run-result-check`：新增中文排版确定性检查类型及其配置、预处理、报告与退出语义。

## Impact

- 代码：`result_check` 模块与 CLI 帮助；测试夹具。
- 调用方：在 requirements 中显式声明该类型才会生效。
- 版本：本 change 升至 **0.8.32**（additive）；合入后立刻打 tag 发 PyPI；不升 0.9.0。
