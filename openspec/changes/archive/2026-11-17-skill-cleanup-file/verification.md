# 验证记录：skill-cleanup-file

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前的判断 | `rulemason judge --change skill-cleanup-file`：pass 3 / review 0 / block 0 |
| 1. 自动精简 | 按 `CLAUDE.md` 用 `/simplify`，范围是 `src/rulemason/shared.py` 与两个测试文件的改动（`skills/` 下的 markdown 是文档，不在范围内）。四个角度各一个子代理，处理见下 |
| 1. 独立审查 | 审查者只读一份材料文件。第一轮 block 0 / review 5；第二轮 block 1 / review 2，按规定停止实现并报告用户，用户同意修法后修复；修复后复审 block 0 / review 2，修完不再审。处理见下 |
| 2. ruff | `uv run ruff check .`：All checks passed |
| 3. 测试 | `uv run pytest`：758 passed。没有改判断规则文件或 `JEV_MODEL`，不跑判断回归 |
| 4. 前端 lint | 本仓库无前端，跳过 |
| 5. 文案检查 | 本仓库无界面文案，跳过 |
| 6. 额外步骤 | 见下「接入项目验证」 |
| 打包 | `uv build --out-dir <仓库外临时目录>`：wheel 含 `rulemason/_shared/skills/rulemason/cleanup.md`，源码包含 `skills/rulemason/cleanup.md` |
| change 校验 | `openspec validate skill-cleanup-file --strict`：valid |

## 自动精简的取舍

采纳：

- 旧项目升级的测试从 `tests/test_update.py` 挪到 `tests/test_check.py`，用现成的 `inited` 夹具，放在同样走「check 报落后 → update」流程的测试旁边。
- 去掉测试里的防御写法（`unlink(missing_ok=True)`、`pop(…, None)`）：`init` 刚生成过这个文件，留着防御写法会让 `init` 不再生成 `cleanup.md` 时测试照样通过。断言只查 `cleanup.md` 是否进了清单。
- 模板测试里 skill 文件名列表只写一次，改为连写比较。

不采纳：

- 把 `SKILL_FILES` 改成读目录内容：会把编辑器临时文件等带进接入项目，层级审查本身也建议保留显式元组。
- 把新测试并进已有测试以省一次 `init`：最多省几十毫秒，单独一条更能看清旧项目的情形。

## 独立审查的处理

第一轮：

1. design、proposal 仍是旧说法：已按实际做法改。
2. 收尾只修了一半：补了一句阶段情形（这一句后来在第二轮被判为 block，见下）。
3. `cleanup.md` 开头一句与正文重复触发条件：已压缩。
4. 测试没覆盖「提示运行 update」：补断言 `next.code == "update"` 且退出码为 1。
5. 入口段没检查先过第 1 节：补断言「第 1 节」出现在「`cleanup.md`」之前。

第二轮（block 1，已停下报告用户，用户同意修法）：

- block：收尾一段「例外一句 + 照旧后文」互相矛盾；条件「这一轮只做完其中一步」会把最后一步也当成阶段提交，模块永远完不成，也漏了一轮做完多步的情形。修法：收尾拆成两个互斥分支，前一支以「收尾到此为止」结束；规格 requirement 改条件，场景改名「计划还有步骤没做完」并新增「最后一步做完」。
- review：design 文件表与 proposal Impact 补上 `tests/test_check.py`；`cleanup.md` 开头「入口闸门已过完」改为「入口闸门见 `SKILL.md` 第 1 节与下文『入口』」，不再与下文要求再跑 `check` 冲突。

修复后复审（block 0 / review 2）：

- 「步骤」与本节 1–6 的流程编号同名，代理可能把「计划的步骤全部做完」读成走完了 1–6：列计划时写明分几步、每步含哪些组；收尾改为「计划分的几步（列计划时定的，不是这里 1–6 的流程编号）」，并补「一轮做完多步的每步各提交一次」。
- 材料里看不到 import 与 `SKILL.md` 其他节：测试已实跑通过；`SKILL.md` 其余提到清理的只有描述、标题、第 1 节入口闸门与展示、第 8 节汇报展示，没有清理步骤本身。

## 改既有测试（逐条）

| 位置 | 改前 | 改后 | 说明 |
|---|---|---|---|
| `test_skill_is_one_file_and_templates_ship_with_engine`（改名为 `test_skill_is_body_files_and_templates_ship_with_engine`） | skill 目录只有 `["SKILL.md"]` | 目录列表 == `sorted(shared.SKILL_FILES)` == `["SKILL.md", "cleanup.md"]` | 规格把副本改为两个文件；同时绑定 `SKILL_FILES`，更严 |
| `test_skill_legacy_cleanup_section` | 从 `SKILL.md` 切出第 7 节，断言约 60 个短语与不超过 70 行 | 切片来源改为 `cleanup.md` 全文，短语一个不少，70 行上限照旧；另断言 `SKILL.md` 第 7 节只剩入口 | 正文搬家，等价 |

新增：`tests/test_check.py::test_old_single_file_skill_gets_cleanup_body`；`test_skill_legacy_cleanup_section` 内新增入口与阶段提交的断言。先写这些测试并看到失败，再改实现。

## 偏离

- `cleanup.md` 正文里的「第 1 节」「第 8 节」没有逐处改写（其中两处被测试按原文断言），改为开头加一句说明章节指 `SKILL.md`。
- 规格场景原写 `check`「报出缺少 `cleanup.md`」，与现有报法不符，改为「副本与本机版本应生成的不一致」。
- 收尾的阶段分支、列计划时写明分几步，是审查后补的，已同步进规格增量、proposal 与 design。

## 接入项目验证

在一个已接入、工作区干净的项目里，用本仓库开发版只读运行：

- `rulemason update --dry-run`：将更新 3 份规则副本（上一版的改动，该项目还没升级）、两个工具目录各自的 `SKILL.md` 与新增的 `cleanup.md`，以及 `.rulemason.yaml`；未写文件。
- `rulemason check`：「接入 生成副本」报副本与本机版本应生成的不一致（7 个文件），提示运行 `rulemason update`，与规格场景一致。
- 运行前后该项目 `git status` 均为空。

## 估计行数对照

| 文件 | 估计 | 实际 |
|---|---|---|
| `skills/rulemason/cleanup.md`（新增） | 约 30 | 28 |
| `skills/rulemason/SKILL.md` | 删约 26、增 3 | 删 24、增 1 |
| `src/rulemason/shared.py` | 1 | 1 / 1 |
| `tests/test_templates.py` | 约 15 | 增 11、删 3 |
| `tests/test_check.py` | 约 14 | 14 |

没有超出一倍的文件。

## 发版说明草稿

- `/rulemason` skill 的「存量清理」正文移到同目录的 `cleanup.md`，只在做存量清理时读。接入项目升级本机 rulemason 后，`rulemason check` 会提示副本落后，运行 `rulemason update` 补上 `cleanup.md`。
- 分几步做的存量清理：每步提交写成 `refactor(cleanup-step): <模块> 第 N 步`，全部做完的最后一次才写 `refactor(cleanup): <模块>`。诊断只认后者，模块不会在第一个阶段提交后就被当成已完成。
