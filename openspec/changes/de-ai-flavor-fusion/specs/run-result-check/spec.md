## ADDED Requirements

### Requirement: 可选文案卫生检查（推荐短名）
检查器 SHALL 支持类型 `prose_hygiene`（确认实施后）。配置 MUST 含非空 `rules`。推荐用于「去套话」场景的短名：`chatbot_closer`、`signpost_opener`、`not_just_contrast`。若保留 `em_dash`，MUST 可单独启闭，MUST NOT 在文档或默认示例中将其等同于去 AI 味。未声明该类型时 MUST NOT 自动运行。失败时只报告，MUST NOT 自动改写正文。

#### Scenario: 推荐短名命中套话
- **WHEN** requirements 启用 `chatbot_closer` 且正文含自研表内收尾套话
- **THEN** 该项失败并给出可复核命中信息；总体不得宣称通过

#### Scenario: 未启用破折号规则
- **WHEN** requirements 仅启用推荐三短名且正文含合法编辑体 U+2014
- **THEN** 不因破折号失败
