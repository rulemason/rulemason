## ADDED Requirements

### Requirement: prose_hygiene 检查与 severity
检查器 SHALL 支持类型 `prose_hygiene`。配置 MUST 含非空 `rules`。可选 `severity` 为 `hint`（默认）或 `strict`；非法 severity MUST 输入错误。推荐短名可启用：`chatbot_closer`、`signpost_opener`、`not_just_contrast`；`em_dash` 可选。`hint` 下命中 MUST 记状态「提示」且不得单独使 exit_code 非零；`strict` 下命中 MUST 失败且总体非零。若同次运行另有失败、无法判断或输入错误，exit_code MUST 仍非零（提示不得吞掉）。未包含该类型的 requirements MUST 行为不变。

#### Scenario: 默认 hint 命中仍 exit 0
- **WHEN** 仅有一项 `prose_hygiene`（缺省 severity）且正文命中推荐短名
- **THEN** 该项为「提示」，exit_code 为 0，overall_pass 为 true

#### Scenario: strict 命中非零
- **WHEN** `severity` 为 `strict` 且命中
- **THEN** 该项失败，exit_code 为 1

#### Scenario: hint 不吞掉其他失败
- **WHEN** 同次有 `prose_hygiene` 提示项与另一项 `must_contain` 失败
- **THEN** exit_code 为 1

#### Scenario: 非法配置
- **WHEN** `severity` 或短名非法
- **THEN** 输入错误，exit_code 为 2

### Requirement: prose_hygiene 预设入口
CLI SHALL 支持 `--preset hint` 或 `--preset strict`，在未传 `--requirements` 时加载对应预设（项目 `.rulemason/result-check/prose-hygiene.*.json` 若存在则优先，否则包内模板）。预设 MUST 含推荐三短名；hint 预设 severity 为 hint，strict 为 strict；MUST NOT 默认启用 `em_dash`。

#### Scenario: preset hint 可运行
- **WHEN** 调用方提供 `--record` 与 `--preset hint`
- **THEN** 使用 hint 预设执行检查且无需另传 requirements 路径
