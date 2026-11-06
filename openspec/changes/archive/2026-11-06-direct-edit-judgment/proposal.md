## Why

一个接入项目三天里的 21 项修复全走「不走 OpenSpec 改代码」，这条路上只有 lint 与测试兜底：没有方案可交 Jev 判断，也不跑独立审查。负责人最担心的是这类直接改动碰到红线（安全、数据、生产操作），而 Jev 现在只审 OpenSpec 方案与界面文案，碰不到这条路。

两层办法都不需要把源码发出去：

- 碰到项目声明的敏感区域的改动，不走直接改，回到 OpenSpec 起最小 change，现有的方案判断自然会对照红线；
- 其余改了代码逻辑的直接改动，让 AI 把这次改动写成一段固定格式的文字说明，交 Jev 对照红线规则与「判路是否绕开主规格」判断。Jev 擅长判文字，发出去的是说明，不是代码。

先按这两层跑一段时间，观察判断结果再调阈值与范围。

## What Changes

- 检查点「不走 OpenSpec 改代码时」：
  - 第 2 步判路加一条：改动落在项目指令列出的「先走 OpenSpec 的区域」时，即使主规格没写到，也按「改契约」起最小 change。
  - 第 3 步写明依据之后加一句：判断已启用且本次改了代码逻辑时，把依据写成「直接改动说明」（要做什么、改哪些文件、读了哪些主规格与检索命中、判在哪条路及理由，不贴代码），存进仓库外的临时文件，运行 `rulemason judge --direct <文件>`。block 按「冲突」停下问用户，review 列出后继续。
- 判断引擎：
  - 新增产物类型 `direct` 与参数 `--direct <文件>`；
  - 说明缺四段中任一段时 lint 直接 block；
  - 随引擎新增一条通用规则 `direct-route-respects-specs`：这次改动是否改变了检索命中的主规格行为，或改了主规格点名的测试的断言与白名单。block 阈值先取 0（只 review 不拦），按红线规则的惯例观察后再收紧。
- skill：
  - 补项目信息时按检测到的目录提「先走 OpenSpec 的区域」候选（迁移、部署、鉴权、表单与数据存储……），由用户确认后写在 AGENTS.md「红线」一节下；
  - 启用判断时，逐条问红线规则是否也用在直接改动上，确认的另写一条 `target: direct` 的规则（措辞改为「这次改动……」，block 起始 0）。
- 覆盖范围的说法同步：前一个 change 写进 `init` 结尾提示、归档后提示、skill 补项目信息与巡检的「判断只审 OpenSpec 方案与界面文案」，改为「判断审 OpenSpec 方案、界面文案与直接改动的说明」；接入后还没起过 change 时，说明改为「方案与文案的判断暂时用不上，直接改动的判断仍会用到」。
- 不做：
  - 把代码 diff 发给 Jev（B3，准确率未验证，且涉及源码外发）；
  - 在工具层拦截生产操作命令；
  - 按改动规模强制回到 OpenSpec；
  - 改 apply 那条路；
  - 改 `init` 生成的 AGENTS.md 模板。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `judge-engine`：修改「通用判断规则随引擎提供」（新增第三条通用规则）；新增「判断直接改动说明」。
- `workflow-gates`：修改「归档后提示一次启用判断」（覆盖范围的说法）；新增「敏感区域的直接改动先走 OpenSpec」「直接改动说明交判断」。
- `rulekit-cli`：修改「init 结尾引导配置 key」（覆盖范围的说法）。
- `rules-layer-setup`：修改「阶段一接入代码规矩与 gates」（覆盖范围的说法）；新增「补项目信息时确认先走 OpenSpec 的区域」「启用判断时问红线规则是否也判直接改动」。

## Impact

- 代码：`src/rulemason/judge/judge.py`（`direct` 产物、`--direct`、说明格式 lint）、`src/rulemason/judge/base/judgments.yaml`（第三条通用规则）；共享正文 `rules/workflow-gates.md`；`skills/rulemason/SKILL.md`；`README.md`；对应测试。
- 依赖：只有启用了判断的项目才会跑 B2，所以依赖 `judge-onboarding-hints` 让用户知道并启用判断；B1 不依赖判断层，接入项目写了敏感区就生效。
- 成本：启用判断的项目里，每次改了代码逻辑的直接改动多一次 Jev 调用。
