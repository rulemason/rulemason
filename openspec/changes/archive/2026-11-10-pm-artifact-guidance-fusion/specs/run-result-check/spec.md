## ADDED Requirements

### Requirement: must_contain 与 pattern 的可选 severity
`must_contain` 与 `pattern` SHALL 支持可选字段 `severity`，取值为 `hint` 或 `strict`。缺省 MUST 为 `strict`（缺失或未匹配记失败，与未引入本字段前一致）。`severity=hint` 时未满足 MUST 记状态「提示」且不得单独使 exit_code 非零；同次其他失败、无法判断或输入错误 MUST 仍使 exit_code 非零。非法 `severity` MUST 为输入错误（exit 2）。`must_not_contain`、`field`、`cjk_typography` 等类型 MUST NOT 因本要求改变既有语义。未声明 severity 的旧 requirements MUST 行为不变。

#### Scenario: 缺省 must_contain 缺失仍失败
- **WHEN** `must_contain` 未写 severity 且正文缺必需文字
- **THEN** 该项为「失败」，exit_code 为 1

#### Scenario: pattern severity=hint 单独不阻断
- **WHEN** 仅有一项 `pattern` 且 `severity` 为 `hint`，正文不匹配
- **THEN** 该项为「提示」，exit_code 为 0

#### Scenario: 文本 hint 不吞掉其他失败
- **WHEN** 同次有 `severity=hint` 的 pattern 提示与另一项失败
- **THEN** exit_code 为 1

#### Scenario: 非法文本 severity
- **WHEN** `must_contain` 或 `pattern` 的 severity 不是 hint 或 strict
- **THEN** 输入错误，exit_code 为 2

### Requirement: 产物结构提示不冒充产品验证
若提供产物结构相关的 result-check 预设或检查项，报告与文档 MUST 标明其为结构/标记存在性检查。`hint` 命中 MUST 为「提示」且不得单独使 exit_code 非零；同次其他失败/无法判断/输入错误仍非零。未包含该类检查的 requirements MUST 行为不变。MUST NOT 将「出现成功标准字样」解释为业务目标已达成。

#### Scenario: 仅结构提示命中仍可 exit 0
- **WHEN** 仅运行 `--preset product-artifact.hint` 且记录缺某约定小节标题
- **THEN** 项为「提示」，exit_code 为 0

#### Scenario: 提示不吞掉其他失败
- **WHEN** 同次有结构提示与另一项失败
- **THEN** exit_code 为 1

### Requirement: product-artifact 预设入口且不偷换 prose 短名
CLI SHALL 支持 `--preset product-artifact.hint` 与 `--preset product-artifact.strict`（项目 `.rulemason/result-check/product-artifact.*.json` 若存在则优先，否则包内模板）。`--preset hint` 与 `--preset strict`（及 `prose-hygiene.*`）MUST 仍加载文案卫生预设，MUST NOT 改指向产物结构预设。产物结构预设 MUST 用既有 `pattern`（或同等文本类型）检查约定小节标题；hint 预设各项 severity 为 hint，strict 为 strict。

#### Scenario: product-artifact.hint 可运行
- **WHEN** 调用方提供 `--record` 与 `--preset product-artifact.hint`
- **THEN** 使用产物结构 hint 预设执行检查且无需另传 requirements 路径

#### Scenario: hint 短名仍为 prose
- **WHEN** 调用方提供 `--preset hint`
- **THEN** 仍加载 prose-hygiene hint 预设（推荐三短名），不是 product-artifact
