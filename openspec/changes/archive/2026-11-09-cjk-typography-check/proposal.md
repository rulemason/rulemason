# Proposal

## Why

中文混排空格等问题既要 AI 写的时候就守，也要本地确定性复核。现有 `result-check` 缺专用类型；共享 `rules/` 也没有中文排版与「改 schema 同步 requirements」的可读规矩。指北规则已人工分类（MIT）；需在 rulemason **自研**两层：规则正文 + 检查，并在本仓 CI 落地。

## What Changes

- `result-check` 新类型 `cjk_typography`（首批七条短名、预处理、allowlist、默认 units、exit 2、定位报告）——同前。
- 新增共享规则 `rules/cjk-typography.md`：用自拟短名写清七条，要求写文档/方案/规格时遵守，并点名 `cjk_typography` 为强制手段。
- 新增共享规则 `rules/result-check-contracts.md`：改被 result-check 覆盖的结构化输出 schema/prompt 时，同 change 更新 requirements JSON 与夹具并跑 `rulemason result-check`；项目约束仍只住各项目 requirements。
- 两份规则经 `init`/`update` 复制进 `.rulemason/`，入口块引用；`check` 校验副本；不破坏无此需求的既有项目（多几个只读文件/引用行）。
- 本仓 CI（`test` job）对约定中文文件跑 `cjk_typography`；本仓样例 + bump **0.8.32**。
- **不做**：照抄指北长文；依赖 第三方测试或分析框架/pangu/外部中文排版调研对象；专名大小写/生造缩写/半角标点/争议链接引号；改 `copy-voice`/`judge`；把排版检查默认塞进 `rulemason check` 巡检命令。

## Capabilities

### New Capabilities

- `cjk-typography`：共享中文排版规矩正文（给人与 AI 读）及其与检查类型的对应关系。
- `result-check-contracts`：改 schema/prompt 时同步 result-check 契约的共享规矩。

### Modified Capabilities

- `run-result-check`：`cjk_typography` 类型与语义。
- `rulekit-cli`：复制与入口引用上述两份规则；`check`/`update` 行为。
- `repo-ci`：本仓 CI 对约定文件跑中文排版检查。

## Impact

- 接入项目：`update` 后多两份规则副本与入口引用；未用 result-check 的项目无强制 CI 负担。
- 本仓：CI 对 README/`rules` 中文文件守排版；版本 **0.8.32**。
