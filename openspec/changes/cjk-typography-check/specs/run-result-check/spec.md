## ADDED Requirements

### Requirement: 中文排版检查类型与配置
当检查项 type 为 cjk_typography 时，检查器 SHALL 对选定正文运行 rules 列出的已知规则。rules 必须为非空且仅含已文档化短名。未知短名、未知配置键或 units/allowlist 形状非法时 MUST 为输入错误。未提供正文 MUST 为无法判断。全部启用规则无命中则通过；任一命中则失败。

#### Scenario: 合法配置且正文合规
- **WHEN** type 为 cjk_typography，rules 均为已知短名，正文在剥离后无违规
- **THEN** 该项为「通过」

#### Scenario: 未知规则短名
- **WHEN** rules 含未文档化的短名
- **THEN** 该项为「输入错误」，总体不得宣称通过

#### Scenario: 未提供正文
- **WHEN** 无 path 且记录未提供 text，或 path 指向的字符串字段未提供
- **THEN** 该项为「无法判断」，总体不得宣称通过

### Requirement: 检查前剥离易误伤片段
在跑规则前，检查器 SHALL 按固定顺序把围栏代码、行内代码、Markdown 图片与链接目标、裸 URL、行内 HTML 标签从待检文本中剥离或替换为不含汉字与拉丁混排的占位。MUST NOT 因占位片段本身报排版违规。

#### Scenario: 行内代码内无空格不失败
- **WHEN** 正文仅在行内代码中出现汉字紧贴拉丁字母，启用 cjk_latin_space
- **THEN** 该项为「通过」

#### Scenario: 裸 URL 不触发中英空格
- **WHEN** 正文含裸 URL，启用 cjk_latin_space
- **THEN** 不得因 URL 主机名与相邻汉字的边界误报（URL 已剥离）

### Requirement: 产品名白名单
若配置含 allowlist 字符串数组，检查器 MUST 在报告命中前丢弃与某一 allowlist 项完全相等的违规子串命中。allowlist 项 MUST 为非空字符串。

#### Scenario: 白名单免除品牌写法
- **WHEN** allowlist 含某品牌串，正文仅该串触发中英空格类规则
- **THEN** 该项为「通过」

#### Scenario: 空字符串白名单项非法
- **WHEN** allowlist 含空字符串
- **THEN** 该项为「输入错误」

### Requirement: 排版失败须定位且不回显全文
失败解释 MUST 含规则短名与至少一个码点偏移或行号定位；MUST NOT 回显违规原文全文。证据字段可含路径或偏移摘要。

#### Scenario: 全角数字失败含短名与位置
- **WHEN** 正文含全角数字且启用 fullwidth_digit
- **THEN** 该项为「失败」，解释含 fullwidth_digit 与位置；解释与证据不含整段原文

### Requirement: 全角数字与叠用标点
规则 fullwidth_digit：剥离后文本若含 U+FF10–U+FF19 MUST 失败。stacked_punct：连续叹号或问号（全角或半角）长度大于等于 2 MUST 失败，但恰好一次的允许组合（实现按已决表）MUST NOT 因此失败。

#### Scenario: 全角数字失败
- **WHEN** 正文含全角数字「３」且启用 fullwidth_digit
- **THEN** 该项为「失败」

#### Scenario: 双叹号失败
- **WHEN** 正文含「！！」且启用 stacked_punct
- **THEN** 该项为「失败」

#### Scenario: 允许的一次叹问组合通过
- **WHEN** 正文仅含已决允许的一次叹问组合且启用 stacked_punct
- **THEN** 该项为「通过」

### Requirement: 中英与中数空格
规则 cjk_latin_space：汉字与拉丁字母相邻且无空白 MUST 失败。cjk_digit_space：汉字与阿拉伯数字相邻且无空白 MUST 失败。

#### Scenario: 中英缺空格失败
- **WHEN** 剥离后正文含「使用Git」且启用 cjk_latin_space
- **THEN** 该项为「失败」

#### Scenario: 中数有空格通过
- **WHEN** 剥离后正文为「共 3 项」且启用 cjk_digit_space
- **THEN** 该项为「通过」

### Requirement: 单位空格与度百分号
规则 unit_space：阿拉伯数字与 units 表中某一单位词相邻且无空白 MUST 失败。degree_percent_nospace：数字与度或百分号之间存在 ASCII 空白 MUST 失败。fw_punct_space：全角标点两侧紧贴 ASCII 空白 MUST 失败。

#### Scenario: 数字与单位缺空格失败
- **WHEN** units 含 Gbps，正文含「10Gbps」且启用 unit_space
- **THEN** 该项为「失败」

#### Scenario: 百分号前有空格失败
- **WHEN** 正文含「15 %」且启用 degree_percent_nospace
- **THEN** 该项为「失败」

#### Scenario: 全角逗号后空格失败
- **WHEN** 正文含「你好， 世界」且启用 fw_punct_space
- **THEN** 该项为「失败」

### Requirement: 可选路径定位正文
若检查项提供 path，检查器 SHALL 按既有 field 路径规则解析 structured；前缀 null 或键缺失 MUST 记未检查/不适用；取值为非字符串 MUST 失败。无 path 时检记录 text 字段。

#### Scenario: 父缺失时排版项跳过
- **WHEN** path 为嵌套路径且前缀键缺失，检查项为 cjk_typography
- **THEN** 该项为「未检查/不适用」

#### Scenario: path 值非字符串失败
- **WHEN** path 存在但值为数组或对象
- **THEN** 该项为「失败」

### Requirement: 无排版类型时行为不变
未声明 type 为 cjk_typography 的既有检查项行为 MUST 不变。

#### Scenario: 旧 requirements 仍通过
- **WHEN** 要求文件不含 cjk_typography，且记录满足原有检查
- **THEN** 总体可通过，退出码为 0
