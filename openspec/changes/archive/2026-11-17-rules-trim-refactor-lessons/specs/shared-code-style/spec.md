## MODIFIED Requirements

### Requirement: React 落法写明重构等价性

React 落法 SHALL 有「重构等价性」一节，写明从旧写法改过来时要保持的八点：抽出的组件放在模块顶层，不在组件内部定义；状态留在原组件，hook 的调用顺序与次数不变；三元改映射表时键必须是封闭的联合类型，键来自接口任意字符串时用 `Map` 或 `if`；会给每个子元素包一层的布局容器里，不从「不渲染」改成「渲染一个返回 `null` 的组件」；惰性初始化的 `useState(() => …)` 不改成每次渲染求值；条件表达式搬进函数时短路顺序不变；抽取后 `react-hooks/exhaustive-deps` 要求改依赖数组时放弃这处抽取，不改依赖数组；同一位置的两个 JSX 分支不抽成两个不同组件。这一节 MUST NOT 出现某个 UI 库或组件库的名字。

#### Scenario: 清理嵌套三元
- **WHEN** AI 按 React 落法把一个嵌套三元改成映射表，键来自接口返回的任意字符串
- **THEN** AI 按等价性一节改用 `Map` 或 `if`，汇报写明原因是键不封闭

#### Scenario: 共享正文不带库名
- **WHEN** 查看 `rules/react.md` 的「重构等价性」一节
- **THEN** 布局容器那一条用通用说法描述，没有任何 UI 库的名字

#### Scenario: 抽取后 lint 要求改依赖数组
- **WHEN** 代理把 effect 里的一段逻辑抽成函数，`react-hooks/exhaustive-deps` 随即要求把依赖数组从 `[id, page]` 改成 `[location]`
- **THEN** 代理撤回这处抽取，保持原依赖数组，汇报写明放弃的原因

#### Scenario: 同一位置的两个分支
- **WHEN** 一个组件在同一位置按条件渲染列表或详情两段 JSX，清理时打算抽成 `ItemList` 与 `ItemDetail` 两个组件
- **THEN** 外层元素留在父组件只抽内部，或抽成一个组件在内部分支，避免切换时整块重挂载丢失滚动与焦点

## ADDED Requirements

### Requirement: 重构时不动被按名字或原文依赖的东西

九条之外 SHALL 写明：重构时，别处按名字或原文依赖的东西不改、不搬：被测试打桩或导入的名字（要收拢时保留原名做转调）、被测试按原文截取的源码片段、会进入对外接口文档的文本、日志原文。这一条 MUST 不分语言，MUST NOT 写具体测试框架或 Web 框架的名字。

#### Scenario: 收拢被打桩的函数
- **WHEN** 清理时要把多个模块里相同的 `_notify_ready` 收进共用模块，而测试按原模块里的名字给它打桩
- **THEN** 原模块保留 `_notify_ready` 这个名字，改成一行转调共用函数，测试的桩仍然生效

#### Scenario: 会进入接口文档的 docstring
- **WHEN** 清理一个路由函数，它的 docstring 会被渲染进对外的接口文档
- **THEN** 清理不改这段 docstring 的原文，即使它不是中文

### Requirement: 注释默认不写

九条第 5 条 SHALL 写明：前几条要求写注释的地方之外默认不写注释，也不写改动经过（如「改为」「新增」），这些属于提交信息。React 落法 SHALL 与九条一致：提前返回与条件渲染只在原因看不出时写「走到这里说明」；按编号写步骤只要求数据加载与路由处理，不再按语句条数要求事件处理写步骤。收紧只约束新写的代码，MUST NOT 要求回头删除已有注释。

#### Scenario: 一看就懂的提前返回
- **WHEN** 新写的组件里有 `if (!item) return null`
- **THEN** 不要求写「走到这里说明」注释

#### Scenario: 四行的事件处理函数
- **WHEN** 新写的点击处理函数有四条语句
- **THEN** 不要求按编号写步骤

#### Scenario: 记录改动经过的注释
- **WHEN** 改代码时打算在旁边写「改为按文件读取」
- **THEN** 不写这行注释，改动经过写进提交信息

#### Scenario: 旧代码里的注释
- **WHEN** 接入项目的旧组件里已有按旧口径写的「走到这里说明」注释，本次改动没有碰到这段
- **THEN** 不因这次收紧去删除它

### Requirement: 常驻规则正文有字数上限

`rules/` 中每次会话常驻加载的正文（`code-style.md`、`python.md`、`react.md`、`agent-coding-caution.md`、`workflow-gates.md`）合计 SHALL 不超过 10300 个字符，由本仓库的测试检查。超出时 MUST 先合并或删掉已有句子再加新句，MUST NOT 只为通过测试而调高上限。

#### Scenario: 加规则后超限
- **WHEN** 某次改动给 `workflow-gates.md` 加了一节，五份文件合计变为 10420 个字符
- **THEN** 本仓库测试失败，改动须同时删减已有正文直到合计不超过 10300

#### Scenario: 写作类规则不计入
- **WHEN** `prose-hygiene.md` 增加了一段
- **THEN** 字数上限的测试不受影响
