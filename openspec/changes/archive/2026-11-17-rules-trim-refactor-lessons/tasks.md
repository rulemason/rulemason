## 1. 先写会失败的测试

- [x] 1.1 在 `tests/test_templates.py` 加字数上限测试：五份常驻文件（`code-style.md`、`python.md`、`react.md`、`agent-coding-caution.md`、`workflow-gates.md`）按 `len(read_text(encoding="utf-8"))` 相加不超过 10300。验证：此时运行通过（当前 10194），记下数字；确认把上限临时改成 10000 时会失败，再改回。
- [x] 1.2 按规格增量加或改断言：React「重构等价性」为 8 条且含 `exhaustive-deps` 与「重挂载」；`code-style.md`「九条之外」含「打桩」「日志原文」，第 5 条含「改动经过」；`react.md` 第 2 条不含「超过三条语句」，第 3 条不含 `if (!item) return null`；`workflow-gates.md` 有「## 合并上游时」且含「经用户同意」、有「在改前的提交上跑同一份测试」、不含「Notion」；`SKILL.md` 第 2 节含「不抄共享规则里的口径」。验证：`uv run pytest tests/test_templates.py` 只有这些新断言失败。

## 2. 改规则正文

- [x] 2.1 `rules/code-style.md`：第 5 条补「默认不写、不写改动经过」，「九条之外」加「重构时不动被依赖的东西」。验证：1.2 里 code-style 相关断言通过，九条编号仍是 1–9。
- [x] 2.2 `rules/react.md`：改第 2、3 条，「重构等价性」加两条，不出现任何 UI 库名。验证：React 相关断言通过。
- [x] 2.3 `rules/workflow-gates.md`：开头加「只修本次引入」定义段（含测试归因）；apply 第 2、4 步与直接改动第 4 步改为引用它；删开头的说明句与 Notion 一节（「没有判断层的项目」的括号原计划删除，因旧断言依赖其中「自动代码审查」一词而保留）；在「提交与推送」前加「合并上游时」。验证：逐段对照原文确认只有措辞变化、步骤编号不变；`grep -c '修掉本次改动引入的问题' rules/workflow-gates.md` 为 1。
- [x] 2.4 按「改既有测试时」更新受去重影响的旧断言（第 262 行的出现次数、第 411–412 行前端一步的原文），只改成等价内容。验证：`uv run pytest tests/test_templates.py` 全部通过；汇报逐条列出改前改后。
- [x] 2.5 运行字数测试并记录实际字数。验证：不超过 10300；若超出，回到 2.1–2.3 删减措辞，不调高上限。

## 3. skill、本仓库指令与主规格 Purpose

- [x] 3.1 `skills/rulemason/SKILL.md` 第 2 节第 4 步补「不抄共享口径」一句。验证：对应断言通过。
- [x] 3.2 `AGENTS.md` 新增「改共享规则」一节：三条准入条件、只出过一次的事故留在接入项目、字数上限由哪条测试检查。验证：读一遍确认不含私人项目名，`.githooks/pre-commit` 的私人词检查通过。
- [x] 3.3 改 `openspec/specs/workflow-gates/spec.md` 的 Purpose，去掉「阶段学习文档同步 Notion」的说法。验证：`openspec validate --specs --strict` 通过。
- [x] 3.4 把原 Notion 一节的做法写进本机 `CLAUDE.local.md`（不入库），落点不变。验证：`git status` 里不出现 `CLAUDE.local.md`。

## 4. 检查点与验证

- [x] 4.1 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行：自动精简（本次有测试代码改动）、独立审查、`uv run ruff check .`、`uv run pytest`。验证：ruff 与测试通过，结果写进 `verification.md`。
- [x] 4.2 额外步骤：在一个接入项目运行 `rulemason update --dry-run` 与 `rulemason check`（用本仓库的开发版），确认只有规则副本变化、巡检一致；只记录，不提交。验证：输出摘要写进 `verification.md`。
- [x] 4.3 `openspec validate rules-trim-refactor-lessons --strict` 通过。验证：命令退出码为 0。
- [x] 4.4 准备 PR 正文的升级说明：Notion 一节已移出、要继续用的项目抄进项目指令的原文、注释收紧只对新代码生效、字数上限 10300 将在后续降回 10000。验证：写进 `verification.md` 的「发版说明草稿」。

## Workflow follow-up

- 归档后在 Notion 审阅子页的落地顺序表里，把第一行的「落地版本」填上发布的版本号。
- 第二个 change（skill 多文件分发、第 7 节拆出、修清理完成标记、写作类规则按需加载、归档第 5 步改由 check 输出）的任务里列一条：字数上限降回 10000。
