## Why

一个接入项目连续五个模块的存量清理，记下了 59 条反馈。逐条审阅后，值得进共享规则的只有少数几条：代理在通用原则下仍会犯、又推不出来的那些。同时，常驻加载的规则正文已有约 10200 字，再逐条加会让代理漏读，所以这次加的和减的放在同一个 change 里，并给常驻正文设上限，以后加一句就得减一句。

## What Changes

加：

- 九条之外加一条：重构时不动别处按名字或原文依赖的东西（被打桩的名字、被测试截取的源码片段、进接口文档的文本、日志原文）。
- React「重构等价性」从六点加到八点：抽取后 `exhaustive-deps` 要求改依赖数组就放弃抽取；同一位置的两个 JSX 分支不抽成两个不同组件。
- 检查点新增「合并上游时」一节：合并后、提交前跑 ruff、测试与前端 lint，合并造成的断裂在合并提交里修，上游带来的违规另开提交。
- 检查点写明测试失败怎么归因：分不清是否本次引入时在改前提交上跑同一份测试；时有时无的失败，单次通过不算结论。
- skill 补项目信息时，命令表与红线只写项目自己的命令和事实，不抄共享规则里的口径。

减：

- 注释收紧，只对新代码生效：九条第 5 条补「其余地方默认不写，也不写改动经过」；React 落法第 2 条去掉「超过三条语句的事件处理」；第 3 条改回与九条一致，只在原因看不出时写。
- 检查点里重复三次的「只修本次引入的问题」改为定义一次、各步引用。
- 删掉检查点开头讲「为什么写在这份文件里」的说明句。
- **BREAKING**：「可选：阶段学习文档同步 Notion」一节移出共享规则。要继续用的项目把它写进自己的项目指令。

约束本仓库自己：

- `AGENTS.md` 写明共享规则的准入门槛：通用原则已在、代理仍违反，推不出来，不限于某个项目或库，三条都满足才进共享正文；只出过一次的事故留在接入项目。
- 加一条测试：常驻规则正文（`code-style.md`、`python.md`、`react.md`、`agent-coding-caution.md`、`workflow-gates.md`）合计不超过 10300 字。按起草措辞实算，本次落地后约 10250 字；后续把归档第 5 步的判断层提示改由 `rulemason check` 输出时，上限降回 10000。

不做：

- 不搬走 `prose-hygiene.md`、`product-artifact-caution.md` 里的工具说明：那些内容是主规格要求写的，且这两份不在常驻预算内，留到「写作类规则按需加载」那个 change 一起改。
- 不改 `rulemason update` 去提示口径变化。
- 不动 skill 的存量清理一节，也不做任何新命令。
- 不改归档第 5 步的判断层提示，留给后续由 `rulemason check` 输出。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `shared-code-style`：React 重构等价性从六点改为八点；新增重构时不动被依赖名字与原文、注释默认不写、常驻正文字数上限三条。
- `workflow-gates`：新增合并上游时的检查与测试失败归因；移除「阶段学习文档同步 Notion」。
- `rules-layer-setup`：补项目信息时不抄共享口径。

## Impact

- 改：`rules/code-style.md`、`rules/react.md`、`rules/workflow-gates.md`、`skills/rulemason/SKILL.md`、`AGENTS.md`、`tests/test_templates.py`；主规格 `workflow-gates` 的 Purpose 去掉 Notion 一句。
- 所有接入项目运行 `rulemason update` 后生效；用到 Notion 一节的项目要自己补项目指令，升级说明里写明。
- 本仓库自己的 `CLAUDE.local.md` 用到了 Notion 一节，要把正文搬进去（不入库）。
