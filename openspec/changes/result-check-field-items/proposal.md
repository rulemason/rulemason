# Proposal

## Why

`field` 已能核对数组成员个数（`min_items`/`max_items`），但不能断言「每个元素」的类型与子字段。Yaomancy 的 STEPS 输出需要：`可做的一步` 每项为非空字符串；`待确认` 每项为对象且必有非空字符串键 `卦象所示`、`怎么确认`。缺元素级核对只能外写脆弱脚本。

## What Changes

- 扩展 `field`：支持对数组**每个元素**施加与标量/对象相同的约束子集（类型、长度、枚举、模式、以及对象元素的子字段）。
- 失败解释含**失败下标**与路径；非法配置仍 exit 2；父 null/缺失仍按既有规则 skip。
- 不改既有无 `items` 的 `field` 行为；退出码 0/1/2 不变；不调模型；不引重依赖。

### Non-goals（不做）

- 不做：完整 JSON Schema、`$ref`/`allOf`、grapheme 计长、数组下标通配之外的查询语言。
- 不做：改 Yaomancy / 打 tag / 发 PyPI；不借用 Promptfoo、Rea、Cedar、Ruler。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `run-result-check`: 为 `field` 增加数组元素级约束与失败下标报告；明确空数组与既有 skip 规则的关系。

## Impact

- 代码：`result_check.py`、CLI 帮助、测试/fixtures。
- 发版：见 design 版本建议（0.8.31 尚未打 tag）。
- 下游：Yaomancy 可在发版后用 `items`（或选定的等价语法）写 STEPS 约束。
