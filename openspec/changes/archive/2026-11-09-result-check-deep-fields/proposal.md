# Proposal

## Why

`rulemason result-check` 的 `structured_keys` 只核对接顶层键是否存在。下游（Yaomancy CI）已接入单事/抉择顶层键检查，但仍无法表达「信心度在 1–5」「签语字数」「应期为对象或 null」等深层约束，只能另写脆弱脚本。需要在本包内以**产品无关**的通用字段核对补齐，且不破坏既有 requirements JSON。

## What Changes

- 扩展 `result-check`：新增**字段级**确定性检查（嵌套路径、类型、数值范围、字符串长度、枚举/正则、数组长度等）；既有 `structured_keys` 与其它类型语义不变。
- 默认报告仍不回显完整原文；失败指出路径与约束，不拷贝整段字段值（可短定位）。
- 退出码仍为 `0` / `1` / `2`；不调模型；不增加重依赖。
- 包内合成 fixture / 测试覆盖新类型；帮助说明新类型与向后兼容。
- 发版计划：合入后发 **0.8.31**（末位 +1）；Yaomancy 在发版后自行改 requirements（本 change 不改产品仓）。

### Non-goals（不做）

- 不做：引入完整 JSON Schema 校验引擎或 `jsonschema` 依赖；不做 `$ref` / `allOf` / `anyOf` 组合语法的通用实现。
- 不做：RR-05 / Skill 出现检查、采集器、Hook、改 `check`/`update`/`judge`。
- 不做：改 Yaomancy 代码或 CI；不把产品字段名写进共享规则正文。
- 不做：借用 Promptfoo / Rea / Cedar / Ruler 源码或测试文档。
- 不做：自动秘密脱敏产品；不为「日后万能断言 DSL」预留插件点。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `run-result-check`: 在既有结构化能力上增加字段路径与约束核对要求；明确与 `structured_keys` 并存及向后兼容。

## Impact

- 代码：`src/rulemason/result_check.py`、CLI 帮助、`tests/test_result_check.py` 与 fixtures。
- API：requirements JSON 可新增检查类型；旧文件无新字段时行为不变。
- 下游：Yaomancy 可在 `0.8.31` 发布后把深层约束写进自己的 requirements（阈值见 design 待决）。
