## ADDED Requirements

### Requirement: 数组元素级约束
当 `field` 项声明 `items` 时，检查器 SHALL 先按既有规则解析路径得到数组，再对每个元素施加 `items` 内约束（值类型、长度、枚举、模式、数值范围，及对象元素的 `fields`）。`fields` 中未标 optional 的键 MUST 视为必填；标 `optional: true` 的键缺失 MUST NOT 因此失败。全部元素满足则通过；任一不满足则失败，解释 MUST 含失败下标与路径。空数组在仅有 `items`、无更大 `min_items` 时 MUST 通过。非法 `items`/`fields` 配置 MUST 为「输入错误」。未声明 `items` 的行为 MUST 不变。

#### Scenario: 每元素非空字符串通过
- **WHEN** 路径值为字符串数组，且 `items` 要求 string 与最小长度 1，且每个元素非空
- **THEN** 该项为「通过」

#### Scenario: 某下标元素失败并报告下标
- **WHEN** 路径值为字符串数组，且至少一个元素不满足 `items` 约束
- **THEN** 该项为「失败」，解释含该元素下标；总体不得宣称通过

#### Scenario: 对象元素缺必填子键失败
- **WHEN** `items` 含 fields，某元素缺少未标 optional 的键
- **THEN** 该项为「失败」，解释含下标与缺失键名

#### Scenario: fields 中 optional 键缺失仍通过
- **WHEN** `fields` 某键声明 optional 为真，且某元素缺少该键但其余必填键满足
- **THEN** 该项为「通过」

#### Scenario: 空数组与元素约束真空通过
- **WHEN** 路径值为空数组且声明了 `items`，未另要求最小元素个数
- **THEN** 该项为「通过」（真空成立；非空仅由 min_items 强制）

#### Scenario: 值非数组但声明 items
- **WHEN** 路径值存在但不是数组，且检查项声明了 `items`
- **THEN** 该项为「失败」

#### Scenario: items 配置非法
- **WHEN** `items` 或 `fields` 含未知约束键或与声明类型不自洽
- **THEN** 该项为「输入错误」，总体不得宣称通过

### Requirement: 数组元素约束沿用父级跳过规则
解析带 `items` 的字段路径时，若按既有嵌套规则因前缀 null 或键缺失而跳过，检查器 MUST 仍将该项记为「未检查/不适用」，MUST NOT 因 `items` 改为失败。

#### Scenario: 父缺失时 items 跳过
- **WHEN** 数组路径的前缀键缺失，且检查项含 `items`
- **THEN** 该项为「未检查/不适用」
