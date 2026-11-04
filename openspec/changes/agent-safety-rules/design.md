# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- 不分语言的通用约定只有一处：`rules/code-style.md` 的「## 九条之外」，两条，其中密钥只写了「不提交」（`rules/code-style.md:15-18`）。这份文件对所有接入项目、所有工具都会加载：Claude Code 由 `CLAUDE.md` 导入（`src/rulemason/templates/claude.block.md:2`），OpenCode 写进 `instructions`（`src/rulemason/templates/opencode.jsonc.tmpl:4`），Cursor 与 Codex 经 `AGENTS.md` 的 Code style 块读到（`src/rulemason/templates/code-style.block.md:3`）。
- 九条第 8 条只管「兜底并给降级结果放在最外层、不吞异常」，没提内部函数静默换路径（`rules/code-style.md:12`）。
- skill 补红线时只从 README 与 `context` 找候选（`skills/rulemason/SKILL.md:40`）。
- 产物写法基础版 design 有四条，没有关于事实出处的条目（`openspec-base/artifact-rules.yaml:6-10`）。项目缺少基础条目时，`rulemason update` 的补齐计划会把缺的条目追加到项目 `openspec/config.yaml` 对应列表的末尾，原有文字逐字保留（`src/rulemason/init.py:386-415` 的 `add_artifact_rules`）；巡检只看是否包含，不看顺序（`src/rulemason/check.py:495-505`）。
- 判断层基础规则只有两条，每条的阈值都用真实 design 样本校准过（`src/rulemason/judge/base/judgments.yaml:5`、`:13` 两条规则与其注释）。
- 本仓库自己的 `openspec/config.yaml` 也照写了基础版（`openspec/config.yaml:20-24`），加了新条目后需要同步，否则对本仓库运行 `rulemason check` 会报出差异。

## Goals / Non-Goals

**Goals:**
- 接入项目升级并 `rulemason update` 后，所有工具都读到外部操作分级与密钥纪律，不需要项目改任何入口。
- 新条目全部是文字规则，不改 `src/rulemason/` 的代码。

**Non-Goals:**
- 不为新规则加机械检查：外部操作与密钥都发生在会话里，不在代码 diff 里，ruff 与判断层都看不到。
- 不按语言细化：外部操作分级不分语言，不写进 python.md、react.md。

## Decisions

1. **外部操作与密钥写进 `rules/code-style.md`，新开一节「## 外部操作与凭据」，放在「## 九条之外」之后。** 否决新建 `rules/agent-safety.md`：要改 init 的 CLAUDE.md 导入、OpenCode `instructions`、副本清单与对应测试，等于为两段文字加一套接入路径；而 code-style.md 已经对所有工具加载。否决塞进「九条之外」：那一节是写代码的约定，混进操作纪律后读者分不清哪条管代码、哪条管操作。文件名叫 code-style 而内容不全是代码风格，在文件第一行的说明里补「与外部操作纪律」。
2. **三级以「会不会销毁已有东西」为界。** 读（不含密钥值与个人数据）直接做；写逐次授权，包括能改回去的改动与发布、发送消息、推送 tag 这类收不回但不销毁已有东西的操作；删除或作废（含强推覆盖共享分支，它会抹掉别人的提交）只给入口与核对点。否决只分「读 / 写」两级：改一条 DNS 记录和删一个数据库会被同等对待，要么前者被拦得太死，要么后者被放得太松。否决按平台列清单（哪些 API 算写）：平台太多，规则会写成永远不全的清单。
3. **授权只管这一次。** 否决「同一会话内同类操作授权一次即可」：「同类」的范围说不清，后续操作很容易超出用户同意时想到的范围；逐次授权的成本只是多一句确认。
4. **密钥纪律落在「不经过会话」。** 让用户自己写进本机环境文件或密钥工具，AI 只引用变量名，确认时只查是否存在。否决「允许贴进对话、用完提醒删除」：会话记录会被保存和同步，删除提醒管不住已经发生的外泄。否决由 rulemason 提供密钥存取脚本：依赖具体平台，proposal 已列为不做。
5. **常见红线候选按项目里实际存在的文件触发。** 数据库访问、部署或发布流程、生产环境配置三类，各对应一条候选，出处写「rulemason 常见红线」加触发文件，仍逐条由用户确认。否决对所有项目一律提三条：没有数据库的项目问「线上数据库只读」是噪声，用户会学会无视候选。否决写进 init 模板直接生成：红线必须由人确认，模板生成等于代写。三条候选都比共享规则的「写要逐次授权」更严：线上库只读、生产发布由人触发、AI 不用生产写权限，三条同时确认也不互相矛盾；红线指名本项目的具体资源，启用判断后还能成为判断规则。
6. **「design 关键事实注明出处」进产物写法基础版，暂不配判断规则，由 apply 后的独立审查检查。** 否决新增判断基础规则：基础规则要用真实样本校准阈值，而「哪句是关键事实」很难让模型稳定判定，误报会拦住正常方案；独立审查已经读 change 产物，可以把缺出处列为 review。否决写成 lint（如要求 Context 每段都有反引号路径）：会逼出凑数的引用，失去意义。
7. **第 8 条只补半句，不新增第 10 条。** 「静默换路径」是「兜底掩盖失败」的同一类问题。否决新增一条：九条的编号已被多处规则与审查引用，加一条要改引用处，且两条会重叠。

## Risks / Trade-offs

- [code-style.md 变长，AI 每次会话多读几百字] → 新节控制在 15 行以内，只写规则不写举例，举例放在规格场景里。
- [「写」与「删除」的边界有灰区，例如覆盖一份线上配置算不算销毁] → 规则把发布、发送消息、推送 tag 这类收不回的操作归入「写」，逐次授权；说不清会不会销毁已有东西的按「删除或作废」处理，宁可多问一次。
- [用户嫌逐次授权烦，口头说「这些你都直接做」] → 规则写明授权只管这一次；用户要长期放开，写进项目指令（规则写明项目指令另有写明的从项目）或工具的权限设置，由人决定，不由 AI 记住。
- [常见红线的触发文件识别不准，如把测试用的 SQLite 当成线上数据库] → 候选附上触发文件，用户一眼能看出不适用并删掉；只提候选、不写入。
- [新 design 条目让已接入项目的 `rulemason check` 报出「产物写法与基础版的差异」] → 这是预期的升级提示，`rulemason update` 补齐计划追加一条即可，发布说明写明。
- [design 出处没有机械检查，执行靠 AI 自觉] → 独立审查把缺出处列为 review；积累到足够的归档样本后，再评估是否值得做成判断规则。

## Migration Plan

1. 本仓库改 `rules/code-style.md`、`skills/rulemason/SKILL.md`、`openspec-base/artifact-rules.yaml`，同步本仓库自己的 `openspec/config.yaml`，跑测试。
2. 发版（版本号按发版时 PyPI 已有版本递增），发布说明写明新增规矩与 design 新条目。
3. 接入项目运行 `uv tool upgrade rulemason`、`rulemason update`（刷新规则与 skill 副本），再运行 `rulemason update --yes` 追加 design 新条目；用户可再运行一次 `/rulemason` 看常见红线候选。

回滚：发布上一版本后，接入项目 `uv tool install rulemason==<上一版>` 再 `rulemason update`，规则与 skill 副本恢复；已追加到项目 `openspec/config.yaml` 的那条 design 条目属于项目文件，不会被自动删除，按需手动删去。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `rules/code-style.md` | 第一行说明；第 8 条补半句；新增「## 外部操作与凭据」 | +14 / −2 |
| `skills/rulemason/SKILL.md` | 补项目信息第 2 步加常见红线候选与出处写法 | +6 / −1 |
| `openspec-base/artifact-rules.yaml` | design 新增一条 | +1 |
| `openspec/config.yaml` | 本仓库同步 design 新条目 | +1 |
| `tests/test_templates.py` | 断言新一节、第 8 条措辞、skill 常见红线、基础版新条目 | +20 |
| `README.md`、`README.en.md` | 「规则」说明补「外部操作与密钥纪律」 | +2 / −2 |
