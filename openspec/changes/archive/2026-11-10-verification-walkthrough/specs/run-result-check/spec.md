# Spec Delta

## ADDED Requirements

### Requirement: verification-walkthrough 预设入口且不偷换既有短名
CLI SHALL 支持 `--preset verification-walkthrough.hint` 与 `--preset verification-walkthrough.strict`（项目种子优先，否则包内模板）。`--preset hint|strict|prose-hygiene.*|product-artifact.*` MUST 行为不变，MUST NOT 被改指向走查预设。走查预设 MUST 用既有 `pattern`（或同等文本类型）检查约定走查小节标题；hint 各项 severity 为 hint，strict 为 strict。

#### Scenario: verification-walkthrough.hint 可运行
- **WHEN** 调用方提供 `--record` 与 `--preset verification-walkthrough.hint`
- **THEN** 使用走查结构 hint 预设执行检查且无需另传 requirements 路径

#### Scenario: 既有 preset 短名不变
- **WHEN** 调用方提供 `--preset product-artifact.hint` 或 `--preset hint`
- **THEN** 仍分别加载产物结构或文案卫生 hint 预设，不是 verification-walkthrough

### Requirement: 走查结构提示不冒充验证通过
走查结构相关预设或检查项的报告与文档 MUST 标明其为结构/标记存在性检查。`hint` 缺标题 MUST 为「提示」且不得单独使 exit_code 非零；同次其他失败/无法判断/输入错误仍非零。MUST NOT 将「出现期望/走查字样」解释为功能已验证通过。

#### Scenario: 仅走查结构提示仍可 exit 0
- **WHEN** 仅运行 `--preset verification-walkthrough.hint` 且记录缺某约定小节标题
- **THEN** 项为「提示」，exit_code 为 0
