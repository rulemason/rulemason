## ADDED Requirements

### Requirement: 数组元素级约束
当 `field` 项声明 `items` 时，检查器 SHALL 先按既有规则解析路径得到数组，再对每个元素施加 `items` 内声明的约束（值类型、长度、枚举、模式、数值范围，以及对象元素的子字段映射）。全部元素满足则该项通过；任一元素不满足则失败，解释 MUST 含失败下标与路径。`items` 配置非法（未知键、与类型不自洽等）MUST 为「输入错误」。未声明 `items` 的 `field` 行为 MUST 保持不变。

#### Scenario: 每元素非空字符串通过
- **WHEN** 路径值为字符串数组，且 `items` 要求 string 与最小长度 1，且每个元素非空
- **THEN** 该项为「通过」

#### Scenario: 某下标元素失败并报告下标
- **WHEN** 路径值为字符串数组，且至少一个元素不满足 `items` 约束
- **THEN** 该项为「失败」，解释含该元素下标；总体不得宣称通过

#### Scenario: 对象元素缺必填子键失败
- **WHEN** `items` 声明 value_type 为 object 且含 fields 映射，某元素缺少映射中的键
- **THEN** 该项为「失败」，解释含下标与缺失键名

#### Scenario: 空数组与元素约束
- **WHEN** 路径值为空数组且声明了 `items`，未另要求最小元素个数
- **THEN** 该项元素约束通过（真空成立）

#### Scenario: 值非数组但声明 items
- **WHEN** 路径值存在但不是数组，且检查项声明了 `items`
- **THEN** 该项为「失败」

#### Scenario: items 配置非法
- **WHEN** `items` 含未知约束键或与声明类型不自洽
- **THEN** 该项为「输入错误」，总体不得宣称通过

### Requirement: 数组元素约束沿用父级跳过规则
解析带 `items` 的字段路径时，若按既有嵌套规则因前缀 null 或键缺失而跳过，检查器 MUST 仍将该项记为「未检查/不适用」，MUST NOT 因 `items` 改为失败。

#### Scenario: 父缺失时 items 跳过
- **WHEN** 数组路径的前缀键缺失，且检查项含 `items`
- **THEN** 该项为「未检查/不适用」
