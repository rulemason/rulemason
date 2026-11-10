## MODIFIED Requirements

### Requirement: 中文排版规矩只住本仓库一份
本仓库 SHALL 提供 `rules/cjk-typography.md`，用自拟短名写明与 `cjk_typography` 一致的要求：既有七条，以及 halfwidth_punct_cjk、fullwidth_alpha、ideographic_space；并说明可用 HTML 注释 rulemason-disable / rulemason-enable 临时关闭检查。MUST NOT 大段照抄外部工具原文。接入项目经副本引用，MUST NOT 手改副本。

#### Scenario: 项目读到排版规矩
- **WHEN** 已接入项目运行 `rulemason update` 后打开 `.rulemason/rules/cjk-typography.md`
- **THEN** 文件存在且含上述短名与「写文档/方案/规格时遵守」的说明

#### Scenario: 点名强制手段
- **WHEN** 阅读该规则文件
- **THEN** 正文写明可用 `rulemason result-check` 的 `cjk_typography` 做确定性强制

#### Scenario: 点名强制手段与关闭注释
- **WHEN** 阅读该规则文件
- **THEN** 正文写明可用 `rulemason result-check` 的 `cjk_typography` 做确定性强制，并写明 disable/enable 注释约定

## ADDED Requirements

### Requirement: 规则层写明新增短名与关闭注释
`rules/cjk-typography.md` SHALL 用一两句意译说明 halfwidth_punct_cjk（两汉字间半角逗号分号冒号叹号问号，不含句点）、fullwidth_alpha、ideographic_space，以及反例可放行内代码或用 rulemason-disable 注释。MUST NOT 写入项目专名或上游工具配置键名。

#### Scenario: 规则文件含新短名
- **WHEN** 打开本仓库 `rules/cjk-typography.md`
- **THEN** 可见 halfwidth_punct_cjk、fullwidth_alpha、ideographic_space 与 disable 注释说明
