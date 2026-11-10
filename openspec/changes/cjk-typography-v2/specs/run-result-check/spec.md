## MODIFIED Requirements

### Requirement: 排版失败须定位且不回显全文
失败解释 MUST 含规则短名、命中总数，以及至少一条带行号与列号（或等价码点偏移）的定位；MUST NOT 回显违规原文全文。证据可含多条命中摘要（规则、行、列、偏移、长度）。总体退出码语义不变：有命中为失败（非 0 且非输入错误），非法配置为输入错误。

#### Scenario: 全角数字失败含短名与位置
- **WHEN** 正文含全角数字且启用 fullwidth_digit
- **THEN** 该项为「失败」，解释含 fullwidth_digit 与位置；解释与证据不含整段原文

#### Scenario: 多处违规列出全部摘要
- **WHEN** 正文含两处及以上启用规则命中
- **THEN** 该项为「失败」，解释或证据含命中总数且不少于两条定位；不含整段原文

#### Scenario: 全角数字失败含短名与行列
- **WHEN** 正文含全角数字且启用 fullwidth_digit
- **THEN** 该项为「失败」，解释含 fullwidth_digit 与行号列号或偏移

### Requirement: 检查前剥离易误伤片段
在跑规则前，检查器 SHALL 按固定顺序剥离或占位：三反引号围栏、波浪号三重围栏、行内代码、缩进代码块、Markdown 图与链的目标 URL、引用式链接定义、裸 URL、尖括号自动链接、行内 HTML 标签。链接与图片的可见文案 MUST 保留并参检。MUST NOT 因占位片段本身报排版违规。

#### Scenario: 行内代码内无空格不失败
- **WHEN** 正文仅在行内代码中出现汉字紧贴拉丁字母，启用 cjk_latin_space
- **THEN** 该项为「通过」

#### Scenario: 裸 URL 不触发中英空格
- **WHEN** 正文含裸 URL，启用 cjk_latin_space
- **THEN** 不得因 URL 主机名与相邻汉字的边界误报（URL 已剥离）

#### Scenario: 链接可见文案缺空格仍失败
- **WHEN** 正文为 Markdown 链接且可见文案为「使用Git」，目标为 URL，启用 cjk_latin_space
- **THEN** 该项为「失败」（可见文案参检；目标已剥离）

#### Scenario: 仅链接目标含混排不失败
- **WHEN** 可见文案合规，仅链接目标 URL 含字母数字路径，启用 cjk_latin_space
- **THEN** 该项为「通过」

#### Scenario: 波浪围栏内混排不失败
- **WHEN** 仅在波浪号三重围栏代码中出现汉字紧贴拉丁字母，启用 cjk_latin_space
- **THEN** 该项为「通过」

#### Scenario: 自动链接不触发中英空格
- **WHEN** 正文含尖括号包裹的 https URL 且 URL 路径含汉字与拉丁紧贴，启用 cjk_latin_space
- **THEN** 不得因自动链接内混排误报

#### Scenario: 引用式链接定义不参检目标
- **WHEN** 正文含引用式链接定义且仅定义行的 URL 侧有混排，启用 cjk_latin_space
- **THEN** 该项为「通过」

## ADDED Requirements

### Requirement: 行内关闭与恢复排版检查
正文中的 HTML 注释含 rulemason-disable 或 rulemason-enable（可带规则短名列表）时，检查器 SHALL 控制其后片段是否参检，直到配对 enable 或文末。裸 disable MUST 关闭当前启用的全部规则。带名列表 MUST 仅关闭列出的已知短名；未知短名 MUST 为输入错误。关闭区间 MUST 不因被关规则产生命中。

#### Scenario: 裸关闭后反例不失败
- **WHEN** 注释裸 disable 后出现汉字紧贴拉丁字母，再 enable，且仅启用 cjk_latin_space
- **THEN** 关闭区间内不产生该规则命中

#### Scenario: 按名关闭单条规则
- **WHEN** disable 仅列出 halfwidth_punct_cjk，关闭区间含两汉字夹半角逗号，区间外另有未关闭规则的违规
- **THEN** 不因半角逗号报 halfwidth_punct_cjk，其余启用规则仍可失败

#### Scenario: 未知关闭短名非法
- **WHEN** disable 注释列出未文档化短名
- **THEN** 该项为「输入错误」

### Requirement: 全角标点旁空格的例外
规则 fw_punct_space：全角标点与 ASCII 空白相邻时，若该空白另一侧为已剥离的 URL 或自动链接占位、Markdown 星号强调标记边界、或表格竖线，MUST NOT 因此失败；其余情况仍 MUST 失败。

#### Scenario: 表格单元格末全角括号不报
- **WHEN** 表格行中全角右括号后为空格再接竖线，启用 fw_punct_space
- **THEN** 该项不因该处失败

#### Scenario: 普通全角逗号后空格仍失败
- **WHEN** 正文含「你好， 世界」且无上述例外，启用 fw_punct_space
- **THEN** 该项为「失败」

### Requirement: 汉字区间含扩展与兼容区
凡依赖汉字类别的规则（含中英与中数空格及新增夹标点类），汉字 MUST 含统一表意文字基本区、扩展 A 与兼容区码位；MUST NOT 仅限基本区。

#### Scenario: 扩展 A 汉字贴拉丁失败
- **WHEN** 正文含扩展 A 汉字紧贴拉丁字母，启用 cjk_latin_space
- **THEN** 该项为「失败」

### Requirement: 两汉字间半角标点
规则 halfwidth_punct_cjk：剥离后若两汉字之间恰好为一个半角逗号、分号、冒号、叹号或问号（不含半角句点），MUST 失败。调用方未把该短名列入 rules 时 MUST NOT 自动启用。

#### Scenario: 汉字夹半角逗号失败
- **WHEN** 正文含「你好,世界」且 rules 含 halfwidth_punct_cjk
- **THEN** 该项为「失败」

#### Scenario: 汉字夹半角句点不因此失败
- **WHEN** 剥离后正文为「你好.世界」且仅启用 halfwidth_punct_cjk
- **THEN** 该项为「通过」

#### Scenario: 未列入 rules 不启用
- **WHEN** rules 不含 halfwidth_punct_cjk，正文含「你好,世界」
- **THEN** 不得因该规则失败

### Requirement: 全角字母与表意空格
规则 fullwidth_alpha：剥离后含全角拉丁字母 MUST 失败。规则 ideographic_space：含表意空格（U+3000）MUST 失败。二者 MUST NOT 改变 fullwidth_digit 的语义。未列入 rules 时 MUST NOT 自动启用。

#### Scenario: 全角字母失败
- **WHEN** 正文含全角拉丁字母且 rules 含 fullwidth_alpha
- **THEN** 该项为「失败」

#### Scenario: 表意空格失败
- **WHEN** 正文含 U+3000 且 rules 含 ideographic_space
- **THEN** 该项为「失败」

#### Scenario: 仅全角数字仍属 fullwidth_digit
- **WHEN** 正文仅含全角数字，rules 含 fullwidth_digit 不含 fullwidth_alpha
- **THEN** 因 fullwidth_digit 失败，不得要求 fullwidth_alpha 才检出
