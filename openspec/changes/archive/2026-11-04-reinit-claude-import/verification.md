# Verification：reinit-claude-import

「改契约」代起的最小 change：只有 proposal、规格增量与 tasks，没有 design。用户确认改主规格后 apply，按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。

## 写代码前检查点

`rulemason judge --change reinit-claude-import`：pass 1 / review 0 / block 0（只有 proposal 适用规则）。

## 1. 自动精简与独立审查

**自动精简（`/simplify`，四路并行）**，只采纳行为保持的修改：

- 采纳：把「原地替换」从 `plan_blocks` 的 `CLAUDE.md` 特判移进通用的 `set_block`（没有标题的块先找独占一行的正文首行），删去 `adopt_agents_import` 与空标记写法；重复导入判断改用已有的 `drop_block`，删去 `outside_block`；测试循环改为参数化。
- 跳过：把导入判断与 `check.py`、`remove.py` 的子串判断统一（超出本次范围）；`remove.keep_agents_import` 的字面量改为从模板派生（超出本次范围）；update 与 remove→init 用例与 init 用例走同一路径（规格分别写了这两个场景，保留）。
- 撤回：无。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 0，review 5，全部修复：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：单独一行 `@AGENTS.md` 另有别处导入时仍会替换，与规格「不止一处不改」不符 → 改为只在代码块外 `@AGENTS.md` 只出现一次时替换，规格与 proposal 改为这一口径 |
| 正确性 | review：保留换行用 `rstrip("\r\n")`，与 `splitlines` 的切法不一致 → 改为 `line[len(line.splitlines()[0]):]` |
| 安全 | review：代码块或缩进里的示例会被当成导入改掉 → 只匹配顶格行，跳过 ``` 与 ~~~ 代码块；规格新增「代码块里的示例」场景 |
| 代码质量 | review：proposal 与 tasks 写的是 `plan_blocks`，实际在 `set_block`；`@./AGENTS.md` 时提示仍写「已有 @AGENTS.md」 → 产物同步，docstring 写明依赖模板正文第一行，提示改为「块外已导入 AGENTS.md」 |
| 测试 | review：remove→init 没有逐字比对、缺 CRLF 与文末无换行、缺混合写法 → 全部补上 |
| 变更卫生 | pass |

第二轮：block 0，review 2。按规则修完后只跑 ruff 与测试，不审第三轮：

- 代码块里的 `@AGENTS.md` 示例仍被报为重复导入，叫用户删自己的示例 → 抽出 `unfenced`，替换与报告都只看代码块以外的行；规格场景写明不报。
- `~~~` 代码块没有测试，且 ``` 开头的代码块遇到 `~~~` 会被误判结束 → 代码块以开头同一种字符结束，新增 `~~~` 内含 ``` 的用例。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：504 passed（本 change 之前 493；新增与改写的用例都在 `tests/test_init.py`、`tests/test_update.py`）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案（命令行提示文字由测试锁定）。

## 6. 额外步骤

未改 `rules/` 或 `lint/`，额外步骤不适用。

## 行数

没有 design，不做估计对照。实际：`src/rulemason/init.py` +37 / −3，`tests/test_init.py` +54 / −3，`tests/test_update.py` +9。proposal Impact 原估「约 +25 行」，多出的是两轮审查补的代码块处理与换行保留。

## 偏差与发现

- **落点**：proposal 原写改 `plan_blocks`，精简后改在 `set_block`（只对没有标题的块，即 `CLAUDE.md` 的 claude 块生效），proposal 与 tasks 已同步。
- **顺带修正**：原来的重复导入判断按子串 `@AGENTS.md`，会漏报 `@./AGENTS.md`、误报代码块里的示例；现在两种都按代码块外的导入判断。提示文字由「块外已有 @AGENTS.md」改为「块外已导入 AGENTS.md」。
- **未处理**：`check.py` 与 `remove.py` 仍按子串判断是否导入了 `AGENTS.md`，口径与 init 不同；目前没有因此出错的场景，留待需要时统一。
