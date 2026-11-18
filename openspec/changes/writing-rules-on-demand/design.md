## Context

动机见 proposal.md「Why」。与做法相关的现状：

- Claude 入口块模板 `src/rulemason/templates/claude.block.md` 导入 9 份规则；OpenCode 模板 `src/rulemason/templates/opencode.jsonc.tmpl` 第 4–12 行是同样 9 份。`copy-voice.md` 本来就不在里面，只在 `AGENTS.md` 里列出阅读场合。
- `check` 要求入口必须引用的只有九条、适用的语言落法与检查点（`src/rulemason/check.py:271` 的 `rule_refs`，被 `check_tool_entries` 用于 CLAUDE.md 与 OpenCode 检查）。去掉 4 份写作类规则的导入，不会让巡检报错。
- 已有 OpenCode 配置：`plan_opencode`（`src/rulemason/init.py:558`）只追加缺的条目，从不删除。
- Claude 入口块是 rulemason 标记块，`update` 会按当前模板刷新（`src/rulemason/update.py:51` 的 `stale_blocks`）。
- `check` 的识别表已经算出「已归档 change」「接入后归档 change」与判断状态（`check.py:397-407`、`judge_label` 在 `check.py:1047`）。报告第一行之后的补充行来自 `report.next_notes`（`check.py:100`，渲染在 `render` 里），JSON 输出的 `text` 也包含它们。
- 检查点「归档」第 5 步共 306 字。换成一句转述后，常驻五份文件合计实算 10057 字（在内存里替换原文后相加）。
- 本仓库的 `CLAUDE.md` 被测试要求等于 Claude 入口模板按本仓库语言过滤后的结果（`tests/test_templates.py` 的 `test_claude_block_imports_rules_and_maps_simplify_step`），模板一改它必须同步。
- `tests/test_templates.py` 的 `test_gates_archive_merges_without_asking_and_hints_key_once` 按原文断言了第 5 步的条件（「正好是 3」等）。

## Goals / Non-Goals

**Goals:**

- 写代码的会话只加载常驻规则；写作类规则在需要时由 AI 按 `AGENTS.md` 写的阅读场合去读。
- 判断层提示的条件只在 `check` 一处计算。

**Non-Goals:**

- 不给 `check --json` 加新字段；提示只出现在报告文字里。
- 不记录「已经提示过」：没有状态文件，靠计数正好等于 3 或 1 只出现一次。

## Decisions

1. **编码审慎 `agent-coding-caution.md` 仍然导入**。否决：一起改成按需读。它管的是每一次写码、改码，按需读就会在最需要的时候漏掉；它也已计入常驻字数上限。
2. **已有 OpenCode 配置只提示、不改写**。否决：用现有的 `instructions_array` 安全改写逻辑删掉这 4 项。那要新写删除逻辑并改动用户的 JSONC；多出来的条目只是多读几份文件，`check` 也不管它们。`update` 在计划里列出可以手动删去的条目即可。
3. **启用提示放进 `report.next_notes`，显示在报告第一行之后**（补项目信息阶段排在 skill 提示之后）。否决：给 `check --json` 加 `hints` 字段，只有检查点这一个用处，而 JSON 的 `text` 本来就带着这一行；也否决改变 `next.code`，那会改变 CI 看到的下一步与退出码含义。
4. **提示条件保持原来的「正好 3 个」或「接入后正好 1 个」**。否决：记录是否提示过。rulemason 约定不写状态文件；计数正好相等时，任何一次 `check`（包括日常巡检）都会显示，这在条件刚满足时是有用的。
5. **字数上限定 10100**（用户选定）。否决：坚持 10000，要再删几句讲原因的话、留 0 余量。
6. **精简 `AGENTS.md` Code style 块的阅读场合行，只写何时读**。否决：保持原样。这一块每次会话都会读，`--preset` 名称等命令用法已写在被指向的规则里。
7. **旧测试 `test_gates_archive_merges_without_asking_and_hints_key_once` 按规格改动处理**：归档一节只断言「运行 check、转述提示、不代配 key」；原先断言的条件（3、1、两种提示、覆盖范围）改由 `check` 的新测试逐条覆盖。这是规格本身改了，不属于「改既有测试时」的等价改写，汇报里逐条列出搬到了哪里。

## 措辞草稿

- `check` 提示是同一个模板，只在没有 key 时多一段配置说明：「判断条件刚满足：〔运行 `rulemason key` 配置 key（申请地址 https://typesafe.ai/），之后〕在 AI 工具中运行 `/rulemason` 并说明要启用判断；判断审 OpenSpec 方案、界面文案与直接改动的说明。」
- 检查点第 5 步：「5. **判断层提示**：归档后运行 `rulemason check`，第一行之后有启用判断的提示时，在汇报末尾原样转述一次；不代用户配置 key，也不代为启用。」
- `AGENTS.md` Code style 块：文案卫生「写给人读的文案时阅读」；编码审慎「写码、改码时阅读」；产品产物「写需求、验收、验证走查等工程交接产物时阅读」。
- `update` 对 OpenCode 的提示：「<配置文件> 的 instructions 仍有 <条目>：这些规则已改为按需阅读，可手动删去」。

## Risks / Trade-offs

- [写文档时代理没去读写作类规则] → `AGENTS.md` 在会话开始就被读到，Code style 块逐条写明阅读场合；这与 `copy-voice.md` 一直以来的做法相同。
- [已有 OpenCode 项目仍加载 4 份] → `update` 列出可删条目，由用户决定；不影响正确性。
- [接入项目升级后 check 先报标记块与模板不一致] → 预期行为，`next.code` 为 `update`；发版说明写明升级产出要一起提交。
- [日常巡检也出现启用提示] → 只在计数正好相等时出现，不改变下一步与退出码。
- [字数降到 10100 后余量只有约 40 字] → 下一个 change（重写清理流程）只动 `cleanup.md`，不碰常驻规则。

## Migration Plan

1. 本仓库合并本 change，发补丁版本。
2. 接入项目升级本机 rulemason 后运行 `rulemason update`：`CLAUDE.md` 的 rulemason 块去掉 4 行导入，`AGENTS.md` 的 Code style 块更新阅读场合；用 OpenCode 的项目按提示决定是否手删 4 项。
3. 按 AGENTS.md「额外步骤」，在一个接入项目用开发版只读运行 `rulemason update --dry-run` 与 `rulemason check`。

回滚：还原本 change 的提交并发补丁版本；接入项目再运行 `rulemason update`，标记块恢复导入 4 份规则，OpenCode 配置本来就没被改。

## 新增与修改的文件

| 文件 | 估计改动行数 |
|---|---|
| `src/rulemason/templates/claude.block.md` | 删 4 行 |
| `src/rulemason/templates/opencode.jsonc.tmpl` | 删 4 行 |
| `src/rulemason/templates/code-style.block.md` | 约 3 行 |
| `src/rulemason/check.py` | 约 20 行 |
| `src/rulemason/init.py` | 约 6 行 |
| `rules/workflow-gates.md` | 1 行 |
| `CLAUDE.md`（本仓库） | 删 4 行 |
| `AGENTS.md`（本仓库） | 约 3 行 |
| `tests/test_templates.py` | 约 20 行 |
| `tests/test_check.py` | 约 40 行 |
| `tests/test_init.py` 或 `tests/test_update.py` | 约 15 行 |
