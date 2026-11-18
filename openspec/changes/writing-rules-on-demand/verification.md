# 验证记录：writing-rules-on-demand

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前的判断 | `rulemason judge --change writing-rules-on-demand`：pass 3 / review 0 / block 0 |
| 1. 自动精简 | 按 `CLAUDE.md` 用 `/simplify`，范围是 `src/rulemason/check.py`、`init.py`、模板与测试的改动（`rules/`、`AGENTS.md`、`CLAUDE.md` 是文档，不在范围内）。四个角度各一个子代理，处理见下 |
| 1. 独立审查 | 审查者只读一份材料文件。第一轮 block 0 / review 5；第二轮 block 0 / review 4，修完不再审 |
| 2. ruff | `uv run ruff check .`：All checks passed |
| 3. 测试 | `uv run pytest`：767 passed。没有改判断规则文件或 `JEV_MODEL`，不跑判断回归 |
| 4. 前端 lint | 本仓库无前端，跳过 |
| 5. 文案检查 | 本仓库无界面文案，跳过 |
| 6. 额外步骤 | 见下「接入项目验证」 |
| change 校验 | `openspec validate writing-rules-on-demand --strict`：valid |

## 字数

常驻五份：改前 10284，改后 10062，上限 10100。归档第 5 步从 304 字换成 82 字的一句。

## 自动精简的取舍

采纳（都不改行为）：

- `judge_onboarding_hint` 先查是否已启用、再比计数，最后才查 git 与 key，绝大多数 `check` 不再多起 git 进程。
- 「接入后归档 change」在 `collect` 里只算一次，同时传给 `identify` 与提示函数；识别表那一行的输出与原来一致（`since` 为空时仍是「—」）。
- 两句提示合成一个模板，只在没有 key 时多一段配置说明（顺带消掉了两句措辞不一致）；判断覆盖范围那句抽成 `JUDGE_SCOPE`，`init.guide_key` 共用，输出文字不变。
- `plan_opencode` 每份配置只解析一次 `instructions`。
- 测试：用 `check.run` 取报告文字与退出码，准备步骤收进 `_hint_project`；「不提示」的情形合成参数化测试；模板测试直接用 `init.ON_DEMAND_RULES`，并断言两份入口模板都不含它们。

不采纳：

- 抽 `judge_enabled(root)`、把 `copied_rules` 改成引用写作类名单：都要改既有代码，超出本次范围。
- 提示文字与识别表「判断」一行复用同一套片段：会改变既有输出。
- 测试里改用 `JUDGE_SCOPE` 常量：保留字面量，措辞被改时测试能发现。

## 独立审查的处理

第一轮：

1. 有 key 时的提示文字与 design 草稿不一致：实现是精简时合并成的同一模板，改 design 草稿与实现一致。
2. `rulekit-cli` 两个场景写「入口块」，可能被读成 Claude 入口块：改为点名 `AGENTS.md` 的 Code style 块。
3. 场景写「报告第二行」，补项目信息阶段会排在 skill 提示之后：改为「第一行之后」。
4. `openspec/judgments.yaml` 路径第三次出现：不改，单个路径判断，抽函数要改两处既有代码；第二轮审查认可这个取舍。
5. 测试缺边界：补上已归档 4 个且接入后 2 个、没有 git、接入后 1 个但总数只有 2 个；另加 OpenCode 多出或删去写作类规则时 `check` 不报错的测试。

第二轮：

1. design 决策 3 仍写「第二行」：已改为「第一行之后」。
2. 「已启用」用例是接入后 0 个，与规格场景（接入后 1 个）不一致：改为接入前 5 个、接入后 1 个。
3. OpenCode 那条测试可能是空测：加对照，配置里去掉 `code-style.md` 时必须报缺。
4. 其他主规格是否还写着旧条件：检索 `openspec/specs/`，只有 `workflow-gates` 的「归档后提示一次启用判断」命中，正是本次 MODIFIED 的那条。

另外，第一轮审查者核实不了的两点已查：仓库里（`skills/`、`rules/`、README、`src/`）没有别处复述旧第 5 步的条件；本仓库自己的 `.opencode/opencode.jsonc` 本来就没有这 4 项，不需要改（它也没有导入编码审慎规则，这是改动前就有的，不在本次范围）。

新增的「不提示」用例确实测到各自的条件：临时去掉提示函数里查 git 与归档数的一行，`no_git`、`too_few` 两条失败，其余三条照旧通过；恢复后全部通过。

## 改既有测试（逐条）

| 位置 | 改前 | 改后 | 说明 |
|---|---|---|---|
| `test_claude_block_imports_rules_and_maps_simplify_step` | 导入列表含 9 份规则 | 去掉 4 份写作类规则 | 规格改动 |
| `test_opencode_and_ruff_templates_point_to_copies` | `instructions` 含 9 份 | 去掉 4 份写作类规则 | 规格改动 |
| `test_resident_rules_stay_within_budget` | 不超过 10300 | 不超过 10100 | 收紧 |
| `test_gates_archive_merges_without_asking_and_hints_key_once` | 归档一节含「正好是 3」「接入后归档 change 正好是 1」「rulemason key」「已有 key 就提示在 AI 工具中运行 `/rulemason`」「判断审 OpenSpec 方案、界面文案与直接改动的说明」「不代用户配置 key」 | 含「运行 `rulemason check`」「原样转述一次」「不代用户配置 key」，且不含「正好是 3」 | 规格改动（design 决策 7）：条件搬进 `check`。原断言改由 `tests/test_check.py` 覆盖：正好 3 个 → `test_judge_onboarding_hint_at_third_archive_without_key`；接入后正好 1 个、已有 key 时运行 `/rulemason` → `..._at_first_archive_after_joined_with_key`；`rulemason key` 与申请地址、判断覆盖范围 → 两条都断言；其余情况不提示 → `test_judge_onboarding_hint_absent` 五种情形 |
| `test_blocks_reference_generated_copies` | 只断言九条、语言落法与检查点 | 另断言 4 份写作类规则在 Code style 块、不在两份入口模板，且块里没有 `--preset` 与「只分发不扫仓」 | 新增断言 |

新增：`tests/test_check.py` 的启用提示测试 3 条（其中一条参数化 5 种）与 `test_opencode_leftover_writing_rules_are_not_reported`；`tests/test_init.py::test_opencode_writing_rules_listed_for_manual_removal`。先写这些测试并看到需要提示的两条与 OpenCode 提示那条失败，再改实现。

## 接入项目验证

在一个已接入、工作区干净、选了 Claude Code 与 OpenCode 的项目里，用本仓库开发版只读运行：

- `rulemason update --dry-run`：将更新 `AGENTS.md`、`CLAUDE.md` 的标记块，以及规则副本、skill 副本与 `.rulemason.yaml`；未写文件。该项目的 OpenCode 配置是早期接入的，本来就没有这 4 项，所以没有「可手动删去」的提示，符合预期。
- `rulemason check`：「接入 生成副本」报副本与本机版本应生成的不一致，提示运行 `rulemason update`。
- 运行前后该项目 `git status` 均为空。

## 估计行数对照

| 文件 | 估计 | 实际（增 / 删） |
|---|---|---|
| `src/rulemason/templates/claude.block.md` | 删 4 | 0 / 4 |
| `src/rulemason/templates/opencode.jsonc.tmpl` | 删 4 | 0 / 4 |
| `src/rulemason/templates/code-style.block.md` | 约 3 | 3 / 3 |
| `src/rulemason/check.py` | 约 20 | 20 / 4 |
| `src/rulemason/init.py` | 约 6 | 10 / 2 |
| `rules/workflow-gates.md` | 1 | 1 / 1 |
| `CLAUDE.md`（本仓库） | 删 4 | 0 / 4 |
| `AGENTS.md`（本仓库） | 约 3 | 3 / 3 |
| `tests/test_templates.py` | 约 20 | 8 / 12 |
| `tests/test_check.py` | 约 40 | 55 / 0 |
| `tests/test_init.py` | 约 15 | 14 / 0 |

没有超出一倍的文件。

## 发版说明草稿

- 中文排版、result-check 契约、文案卫生、产品产物 4 份规则不再在每次会话开始时导入，改为在 `AGENTS.md` 的 Code style 块写明阅读场合、用到时再读。接入项目运行 `rulemason update` 后，`CLAUDE.md` 与 `AGENTS.md` 的 rulemason 标记块会变化，请随升级一起提交。
- 用 OpenCode 的项目：已有配置不会被改写；如果 `instructions` 里还有这 4 项，`update` 会列出来，可以手动删去。
- `rulemason check` 在启用判断的条件刚满足时（已归档正好 3 个，或接入后正好归档 1 个），在报告第一行之后给一条启用提示；检查点归档后转述这条提示即可。
- 常驻规则正文的字数上限降到 10100。
