# run-result-check Specification

## Purpose
对调用方提交的一次已发生运行记录与明确检查要求做本地确定性核对，输出可复核的逐项结论与汇总结论，供脚本与 CI 读取；不运行 agent，不以未采集证据宣称通过。

## Requirements

### Requirement: 只检查调用方提供的记录
检查器 SHALL 只消费调用方提交的已发生记录与检查要求。MUST NOT 自行采集会话、启动 agent、拦截 LLM API，或改写接入项目既有护栏。缺少某类事实时该项 MUST 为「无法判断」，MUST NOT 默认通过。

#### Scenario: 未提供输出正文
- **WHEN** 检查要求含文本类项，且调用方未提供输出正文（字段缺失或显式未采集）
- **THEN** 对应项状态为「无法判断」，总体不得宣称通过

### Requirement: 文本必须包含
对每条「必须包含」要求，检查器 SHALL 在已提供的输出正文中查找给定文字。正文已提供且全部出现则该项通过；正文已提供但有缺则失败；正文未提供则无法判断。

#### Scenario: 必需文字齐全
- **WHEN** 调用方提供输出正文，且要求中的每段必需文字均出现
- **THEN** 该项为「通过」，结论含可复核依据（适度摘录或缺证据说明）

#### Scenario: 必需文字缺失
- **WHEN** 调用方提供输出正文，且至少一段必需文字未出现
- **THEN** 该项为「失败」，不得被其他通过项掩盖

### Requirement: 文本禁止包含
对每条「禁止包含」要求，检查器 SHALL 在已提供的输出正文中查找禁止文字。出现则失败；正文已提供且未出现则通过；正文未提供则无法判断。

#### Scenario: 命中禁止文字
- **WHEN** 输出正文已提供且含有禁止文字
- **THEN** 该项失败，并能指出命中内容；总体不得宣称通过

### Requirement: 文本模式检查
对每条模式要求，检查器 SHALL 用调用方给定的模式核对输出正文。模式合法且匹配则通过；合法但不匹配则失败；模式本身非法 MUST 记为「输入错误」，与检查失败分开展示。

#### Scenario: 非法模式
- **WHEN** 检查要求中的模式无法编译或非法
- **THEN** 该项为「输入错误」，总体不得宣称通过

### Requirement: 结构化可解析与必填字段
当检查要求含结构化核对时，检查器 SHALL 确认结构化输出可解析，并具备要求的必填字段。可解析且字段齐全则通过；不可解析或缺字段则失败；无结构化输出则无法判断。缺字段 MUST 指出缺什么；MUST NOT 把「字段名出现在正文」当作字段存在。

#### Scenario: 缺必填字段
- **WHEN** 结构化输出可解析但缺少至少一个必填字段
- **THEN** 该项失败并指出缺失字段名

#### Scenario: 无结构化输出
- **WHEN** 检查要求含结构化核对，且调用方未提供结构化输出
- **THEN** 该项为「无法判断」，总体不得宣称通过

### Requirement: 逐项结论与总体通过条件
每项结论 SHALL 含可追踪标识、状态与解释。总体通过 MUST 仅当全部必需项为「通过」，且不存在必需项的「无法判断」或任何「输入错误」。空检查要求集、空检查名等非法输入 MUST 为「输入错误」并阻止宣称通过。未检查/不适用 MUST NOT 计入通过，也 MUST NOT 被用来填充通过。

#### Scenario: 多项中一条必需失败
- **WHEN** 至少一个必需项失败，其余通过
- **THEN** 汇总不得宣称总体通过

#### Scenario: 空检查要求集
- **WHEN** 调用方提交的检查要求集合为空
- **THEN** 结果为「输入错误」或同等不予通过，不得视作通过

#### Scenario: 不适用不得充作通过
- **WHEN** 某项由调用方明确标为「未检查」或「不适用」，且要求集仍非空
- **THEN** 该项不计入必需通过集，也不得单独或汇总写成「通过」

#### Scenario: 缺正文与其它项混合
- **WHEN** 文本类必需项因缺正文为「无法判断」，同时另有必需项为「通过」
- **THEN** 总体不得宣称通过

### Requirement: 本期排除 Skill 出现检查
本期能力 MUST NOT 提供或宣称「已归一 Skill / 工具调用记录中是否出现指定 Skill」的检查。调用方未交 Skill 证据时 MUST NOT 因此通过；若检查要求仍点名 Skill 项，检查器 MUST 记为「输入错误」，MUST NOT 写成通过，且 MUST NOT 因该项宣称总体通过。

#### Scenario: 要求含 Skill 项
- **WHEN** 检查要求包含 Skill 出现类条目
- **THEN** 该项为「输入错误」，不得记为通过；总体不得宣称通过

### Requirement: 来源范围与限度
结果 SHALL 写明规则/输入的可核对标识、本次覆盖范围与未覆盖限度。来源标识用于追溯，MUST NOT 被宣传为防伪或真实性验证。首个接入场景为产品解读结构化输出时，限度 MUST 能区分离线 fixture、可选 eval 报告与未覆盖的真实在线会话。

#### Scenario: 仅 fixture 验收
- **WHEN** 输入来自离线 fixture 而非真实模型会话
- **THEN** 结果限度写明仅为 fixture/离线验收，不得暗示已检查真实线上解读

### Requirement: 本地确定性与安全默认
检查过程 SHALL 仅在本地处理提供的记录与要求：MUST NOT 上传记录，MUST NOT 启动 agent，MUST NOT 为完成本检查而额外调用模型或远程裁判。无外部密钥时 MUST 仍能完成确定性检查。「零 API 成本」仅指本检查本身。

#### Scenario: 无外部密钥
- **WHEN** 环境未配置任何模型或裁判密钥
- **THEN** 确定性检查仍可完成并给出逐项与汇总结论

### Requirement: 独立入口且不改变既有命令语义
本能力 SHALL 通过独立于 `check` / `update` / `judge` 的入口暴露。调用该入口 MUST NOT 改变上述三命令的参数含义、输出契约或退出码语义。入口须能被脚本与 CI 非交互调用。

#### Scenario: 并行调用既有 check
- **WHEN** 同一环境先或后运行 `rulemason check` 与本检查入口
- **THEN** `check` 的退出码与 `--json` 字段含义与未引入本能力时一致

### Requirement: 适合 CI 的退出语义
入口 MUST 以非零退出码表示「不得宣称总体通过」（含必需项失败、无法判断、输入错误）。总体通过时退出码为 0。MUST NOT 在存在失败、无法判断或输入错误时仍以 0 退出。具体码表由实现固定并在帮助中说明。

#### Scenario: 无法判断时非零退出
- **WHEN** 至少一个必需项为「无法判断」
- **THEN** 进程以非零退出码结束，且机器可读结果标明总体未通过

### Requirement: 默认报告不回显全文
默认面向人的报告 MUST NOT 回显完整输入原文；可含适度摘录或字段路径以支撑复核。MUST NOT 承诺自动秘密脱敏；调用方负责不把密钥写入记录。

#### Scenario: 默认输出
- **WHEN** 以默认选项运行检查且输入正文较长
- **THEN** 报告不含完整原文拷贝，仍能指出失败或命中位置的依据

### Requirement: 字段路径与约束核对
当检查要求含字段级核对时，检查器 SHALL 在已提供的结构化输出上按单条路径读取值，并核对该项声明的约束（类型、可选键、数值范围、字符串长度、枚举、字段值模式、数组长度）。路径可解析且约束均满足则通过；值不满足约束则失败并指出路径与哪条约束；结构化输出未提供则无法判断。MUST NOT 要求调用方改写仅含既有检查类型的要求文件。字符串长度 MUST 按 Unicode 码点计，MUST NOT 按字节计。一项 MUST 只含一条路径。

#### Scenario: 数值范围通过
- **WHEN** 结构化输出已提供，字段路径存在且值为整数并落在要求的最小与最大之间（含端点）
- **THEN** 该项为「通过」

#### Scenario: 数值范围失败
- **WHEN** 结构化输出已提供，字段路径存在但数值超出声明范围
- **THEN** 该项为「失败」，解释含路径与范围约束；总体不得宣称通过

#### Scenario: 字符串长度失败
- **WHEN** 结构化输出已提供，字段值为字符串且码点长度超出声明的最大长度
- **THEN** 该项为「失败」，解释含路径与长度约束，且 MUST NOT 回显该字段完整原文

#### Scenario: 对象上末段缺失
- **WHEN** 路径前缀均为对象，但末段键不存在
- **THEN** 该项为「失败」并指出缺失路径

#### Scenario: 允许 null 的联合类型
- **WHEN** 要求声明类型为对象或 null，且字段值为 null
- **THEN** 该项类型约束通过

#### Scenario: 可选键缺失视为通过类型
- **WHEN** 字段项声明 `optional` 为真，且该路径键不存在
- **THEN** 该项不因键缺失而失败（与值为 null 同等可接受于联合含 null 的类型检查）

#### Scenario: 字段值模式非法
- **WHEN** 字段级模式无法编译
- **THEN** 该项为「输入错误」，总体不得宣称通过

#### Scenario: 无结构化输出时字段核对
- **WHEN** 检查要求含字段级核对，且调用方未提供结构化输出
- **THEN** 该项为「无法判断」，总体不得宣称通过

### Requirement: 嵌套路径在父级 null 或缺失时跳过
解析多段字段路径时，若某一前缀段的值为 JSON null，或该前缀键缺失，检查器 MUST 将该项记为「未检查/不适用」，MUST NOT 记为失败或通过。若前缀存在但不是对象以致无法下降，MUST 记为失败。前缀为对象且末段存在时，仍按该项约束核对。

#### Scenario: 父值为 null 时子路径跳过
- **WHEN** 多段路径的某一前缀值为 null
- **THEN** 该项为「未检查/不适用」，不阻止其余必需项在全部通过时宣称总体通过

#### Scenario: 父键缺失时子路径跳过
- **WHEN** 多段路径的某一前缀键不存在
- **THEN** 该项为「未检查/不适用」

#### Scenario: 父为对象且子字段为空串失败
- **WHEN** 前缀为对象，末段值为空字符串，且要求最小长度至少为 1
- **THEN** 该项为「失败」，总体不得宣称通过

### Requirement: 既有结构化键检查保持兼容
既有「结构化可解析与必填字段」能力（仅核对接顶层键存在）SHALL 保持原语义。仅含该类要求、不含字段级核对的要求文件，在输入不变时 MUST 得到与扩展前同等的通过或失败结论（退出码语义不变）。

#### Scenario: 仅顶层键的旧要求仍通过
- **WHEN** 要求文件只含顶层必填键核对，且记录中这些键齐全
- **THEN** 总体可通过，且退出码为 0

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

### Requirement: 中文排版检查类型与配置
当检查项 type 为 cjk_typography 时，检查器 SHALL 对选定正文运行 rules 列出的已知规则。rules 必须为非空且仅含已文档化短名。未知短名、未知配置键或 units/allowlist 形状非法时 MUST 为输入错误。未提供正文 MUST 为无法判断。全部启用规则无命中则通过；任一命中则失败。省略 units 时 MUST 使用默认表 GB、TB、Gbps、MB、KB、ms、px。

#### Scenario: 合法配置且正文合规
- **WHEN** type 为 cjk_typography，rules 均为已知短名，正文在剥离后无违规
- **THEN** 该项为「通过」

#### Scenario: 未知规则短名
- **WHEN** rules 含未文档化的短名
- **THEN** 该项为「输入错误」，总体不得宣称通过

#### Scenario: 未提供正文
- **WHEN** 无 path 且记录未提供 text，或 path 指向的字符串字段未提供
- **THEN** 该项为「无法判断」，总体不得宣称通过

#### Scenario: 省略 units 使用默认表
- **WHEN** 配置未提供 units，启用 unit_space，正文含「10Gbps」
- **THEN** 该项为「失败」（默认表含 Gbps）

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

### Requirement: 产品名白名单
若配置含 allowlist 字符串数组，检查器 MUST 在报告命中前丢弃与某一 allowlist 项完全相等的违规子串命中。allowlist 项 MUST 为非空字符串。

#### Scenario: 白名单免除品牌写法
- **WHEN** allowlist 含某品牌串，正文仅该串触发中英空格类规则
- **THEN** 该项为「通过」

#### Scenario: 空字符串白名单项非法
- **WHEN** allowlist 含空字符串
- **THEN** 该项为「输入错误」

### Requirement: 排版失败须定位且不回显全文
失败解释 MUST 含规则短名、命中真实总数，以及至少一条带行号与列号（或等价码点偏移）的定位；若命中列表被截断，MUST 标明截断且 MUST NOT 把截断列表说成全部。MUST NOT 回显违规原文全文。证据可含多条命中摘要（规则、行、列、偏移、长度）。总体退出码语义不变：有命中为失败（非 0 且非输入错误），非法配置为输入错误。

#### Scenario: 全角数字失败含短名与位置
- **WHEN** 正文含全角数字且启用 fullwidth_digit
- **THEN** 该项为「失败」，解释含 fullwidth_digit 与位置；解释与证据不含整段原文

#### Scenario: 多处违规列出全部摘要
- **WHEN** 正文含两处及以上启用规则命中
- **THEN** 该项为「失败」，解释或证据含命中总数且不少于两条定位；不含整段原文

#### Scenario: 全角数字失败含短名与行列
- **WHEN** 正文含全角数字且启用 fullwidth_digit
- **THEN** 该项为「失败」，解释含 fullwidth_digit 与行号列号或偏移

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

### Requirement: 全角数字与叠用标点
规则 fullwidth_digit：剥离后文本若含 U+FF10–U+FF19 MUST 失败。stacked_punct：连续叹号或问号（全角或半角）长度大于等于 2 MUST 失败；恰好一次的允许组合 `？！`、`?!`、`！？`、`!?` MUST NOT 因此失败。

#### Scenario: 全角数字失败
- **WHEN** 正文含全角数字「３」且启用 fullwidth_digit
- **THEN** 该项为「失败」

#### Scenario: 双叹号失败
- **WHEN** 正文含「！！」且启用 stacked_punct
- **THEN** 该项为「失败」

#### Scenario: 全角叹问组合通过
- **WHEN** 正文仅含「？！」且启用 stacked_punct
- **THEN** 该项为「通过」

#### Scenario: 半角问叹组合通过
- **WHEN** 正文仅含「?!」且启用 stacked_punct
- **THEN** 该项为「通过」

#### Scenario: 全角问叹逆序组合通过
- **WHEN** 正文仅含「！？」且启用 stacked_punct
- **THEN** 该项为「通过」

#### Scenario: 半角叹问逆序组合通过
- **WHEN** 正文仅含「!?」且启用 stacked_punct
- **THEN** 该项为「通过」

#### Scenario: 允许组合后再叠失败
- **WHEN** 正文含「？！！」且启用 stacked_punct
- **THEN** 该项为「失败」

### Requirement: 中英与中数空格
规则 cjk_latin_space：汉字与拉丁字母相邻且无空白 MUST 失败。cjk_digit_space：汉字与阿拉伯数字相邻且无空白 MUST 失败。

#### Scenario: 中英缺空格失败
- **WHEN** 剥离后正文含「使用Git」且启用 cjk_latin_space
- **THEN** 该项为「失败」

#### Scenario: 中数有空格通过
- **WHEN** 剥离后正文为「共 3 项」且启用 cjk_digit_space
- **THEN** 该项为「通过」

### Requirement: 单位空格与度百分号
规则 unit_space：阿拉伯数字与 units 表（或默认表）中某一单位词相邻且无空白 MUST 失败。degree_percent_nospace：数字与度或百分号之间存在 ASCII 空白 MUST 失败。fw_punct_space：全角标点两侧紧贴 ASCII 空白 MUST 失败。

#### Scenario: 数字与单位缺空格失败
- **WHEN** 使用默认或显式含 Gbps 的 units，正文含「10Gbps」且启用 unit_space
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
