## Why

检查点写着「自动执行，无需提醒」，可用户无从知道它到底跑没跑。按规则，每个 change 的完成汇报写在 `verification.md` 里，里面应该有审查与测试的结果。可是接入项目最近一次归档的 change 里，项目甲、项目乙都没有这个文件。spec-guard 让归档前自查这份文件，但手动归档、或用了没读检查点的工具时，没有任何地方会发现。

## What Changes

- `rulemason check` 的巡检新增一项「最近归档的检查点记录」：取已归档 change 里日期最新的那一天的全部 change，逐个看 `verification.md` 是否存在、是否同时写到审查与测试（中文「审查」「测试」，或英文 review / test）。
- 缺文件或缺其中一项时列出 change 名与缺什么。这一项只报告，不影响退出码与下一步。
- 没有 `openspec/` 或没有已归档 change 的项目，这一项写「一致」。
- `/rulemason` 的日常巡检说明加一句：这一项是提醒下次归档前把检查点跑完并写进汇报，不要补写过去的汇报。
- 不做：检查全部历史归档；让这一项导致非 0 退出；要求 `verification.md` 用固定标题或模板；放进 `rulemason judge`；核对汇报内容是否属实。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：新增「巡检核对最近归档的检查点记录」一条 requirement。

## Impact

- 代码：`src/rulemason/check.py`（新函数与巡检项）。
- 文档：`skills/rulemason/SKILL.md` 的日常巡检说明。
- 测试：`tests/test_check.py`。
- 接入项目：升级后，项目甲、项目乙的 check 巡检会多出一条（最近的迁移 change 没有 `verification.md`），退出码不变。
