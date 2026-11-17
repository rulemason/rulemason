# 验证记录：rules-trim-refactor-lessons

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前的判断 | `rulemason judge --change rules-trim-refactor-lessons`：pass 3 / review 0 / block 0 |
| 1. 自动精简 | 按 `CLAUDE.md` 用 `/simplify`，范围只限 `tests/test_templates.py` 的新增与修改断言（规则正文是文档，不在范围内）。四个角度（复用、简化、效率、层级）各一个子代理，处理见下 |
| 1. 独立审查 | 两轮，审查者只读一份材料文件，不读仓库、不运行命令。第一轮 block 0 / review 5，第二轮 block 0 / review 2，处理见下；按规定不审第三轮 |
| 2. ruff | `uv run ruff check .`：All checks passed |
| 3. 测试 | `uv run pytest`：757 passed。本次没有改判断规则文件或 `JEV_MODEL`，不跑判断回归 |
| 4. 前端 lint | 本仓库无前端，跳过 |
| 5. 文案检查 | 本仓库无界面文案，跳过 |
| 6. 额外步骤 | 在一个接入项目用开发版只读运行，见下「接入项目验证」 |
| change 校验 | `openspec validate rules-trim-refactor-lessons --strict`：valid；`openspec validate --specs --strict`：15 passed |

## 自动精简的取舍

采纳（都不改断言含义）：

- 第 5 条那一行只取一次，存为 `fifth`，与文件里已有的 `eighth`、`ninth` 写法一致。
- 新加的长串 `and` 改成 `for … assert text in …, text`，失败时能看出缺的是哪个词。
- 「修掉本次改动引入的问题」的「只出现 1 次」挪到原来检查它出现的那条断言上，新测试里不再重复。
- 前端那步的「ESLint 基线」断言原先改成在全文里找，比旧断言宽，收回到「只修本次引入」定义那一行。

不采纳：

- 删掉前端那步的断言（理由是另一个测试的循环也覆盖了它）：它是旧断言改写出的等价断言，按「改既有测试时」不删。
- 加 `_read` 文件读取辅助函数：文件里原有约 30 处同样写法，改它超出本次范围。
- 字数测试改为从 Claude 入口模板读出全部导入的规则（会算进 9 份）：按已定方案，4 份写作类规则在下一个 change 改为按需加载，在那之前常驻清单按 5 份算，不改。
- 把 `"Notion" not in gates` 并进针对全部规则的专名检查：收益小，保留现状。

## 独立审查的处理

第一轮：

1. tasks 2.3 与 design 写了删掉「没有判断层的项目」里的括号，实际恢复了原样：已在 design「措辞草稿」与 tasks 2.3 写明保留及原因（见下「偏离」）。
2. 测试归因句只有直接改动第 4 步经引用走到，apply 第 3 步与「合并上游时」没有引用：不加引用句。常驻字数只剩 16 字余量；这一句放在检查点开头的定义段，`workflow-gates.md` 每次会话全文加载，靠通读生效。第二轮审查认可这个取舍。
3. 规格场景里的标识符像来自接入项目：已换成 `_notify_ready`、`ItemList` / `ItemDetail`、`[id, page]`。
4. 测试行尾注释写「两步」，实际检查三步：已改为「定义一次，下面三步引用它」。
5. 「超过三条语句」只查第 2 条那一行：已改为对 `react.md` 全文断言，更严。

第二轮：

1. 产物与实现不一致（括号）：已改 design 与 tasks。
2. 怀疑缺少 Notion 的 REMOVED 增量：已在 `specs/workflow-gates/spec.md` 的 `## REMOVED Requirements` 里，删开头说明句也已写进 proposal；第二轮材料没带上这两份，无需改动。

## 改既有测试（逐条）

| 位置 | 改前 | 改后 | 说明 |
|---|---|---|---|
| `test_workflow_gates_fix_only_problems_this_change_introduced` | `text.count("建议运行 `/rulemason` 建立基线") == 2` | `== 1`，并逐个断言 ruff、前端 lint、直接改动三步都含「按「只修本次引入」处理」 | 原文定义一次、三步引用；覆盖面等价 |
| 同上 | `"修掉本次改动引入的问题" in text` | `text.count("修掉本次改动引入的问题") == 1` | 更严 |
| `test_rules_wording_key_sections` | 前端那步含「修掉本次改动引入的问题」与「建立 ESLint 基线」 | 前端那步含「按「只修本次引入」处理」，定义那一行含「建立基线（前端是 ESLint 基线）」 | 等价 |
| `test_eslint_wording_per_file_and_react_equivalence` | 重构等价性 `count == 6` | `count == 8`，原有 `Map`、`useState` 检查保留，另加 `exhaustive-deps`、「不改依赖数组」「重挂载」 | 规格增量把六点改为八点 |

新增两个测试：`test_resident_rules_stay_within_budget`、`test_rules_refactor_lessons_and_comment_defaults`。先写它们并确认后者失败、前者在 10194 字时通过，再改正文。

## 字数

常驻五份（`code-style.md`、`python.md`、`react.md`、`agent-coding-caution.md`、`workflow-gates.md`）：改前 10194，改后 10284，上限 10300。design 草稿估算 10253，多出的 31 字是保留下来的那串括号。

## 偏离

- 「没有判断层的项目」的括号原计划删除，保留：旧断言 `"自动代码审查" in text` 只能在这串括号里找到，删掉就要放宽断言。

## 接入项目验证

在一个已接入、工作区干净、带全部 10 份规则副本（含 React）的项目里，用本仓库开发版（`uv run --project <本仓库> rulemason …`）只读运行：

- `rulemason update --dry-run`：将更新 `.rulemason/rules/code-style.md`、`react.md`、`workflow-gates.md`，两份 skill 副本与 `.rulemason.yaml`，与本次改动一致；未写文件。
- `rulemason check`：「接入 生成副本」报 5 个文件与本机版本应生成的不一致（即上面要更新的副本），其余层齐全。巡检另有两条是该项目原有的，与本次无关：一个 React 目录缺 ESLint 配置、一个归档 change 缺 `verification.md`。
- 运行前后该项目 `git status` 均为空。

## 估计行数对照

| 文件 | 估计 | 实际（增 / 删） |
|---|---|---|
| `rules/workflow-gates.md` | 约 15 | 10 / 10 |
| `rules/react.md` | 约 4 | 4 / 2 |
| `rules/code-style.md` | 约 2 | 2 / 1 |
| `skills/rulemason/SKILL.md` | 约 1 | 1 / 1 |
| `AGENTS.md` | 约 8 | 10 / 0 |
| `tests/test_templates.py` | 约 30 | 39 / 4 |
| `openspec/specs/workflow-gates/spec.md` | 1 | 1 / 1 |
| `CLAUDE.local.md`（本机，不入库） | 约 5 | 4 / 0 |

没有超出一倍的文件。

## 发版说明草稿

- 「可选：阶段学习文档同步 Notion」已移出共享检查点。要继续用的项目，把下面这段写进自己的项目指令（可以是不入库的本机指令），并写明落点：「每完成一个阶段（一个产物写完，或一段 apply 完成），主动在落点下新建下一篇编号子页，无需用户提醒。写给零基础读者：做了什么、为什么这样做、要敲的命令、应该看到什么；注明仓库是权威记录。」
- 注释规则收紧（九条第 5 条、React 落法第 2、3 条）只约束新写的代码，不要求回头删除已有注释。
- 新增：重构时不动被按名字或原文依赖的东西；React 重构等价性加两条；检查点新增「合并上游时」和测试失败的归因方法。
- 本仓库给常驻规则正文设了字数上限，目前 10300 字，后续把归档第 5 步的判断层提示改由 `rulemason check` 输出后降回 10000。
