# Verification

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前判断 `rulemason judge --change legacy-cleanup-flow` | pass 3 / review 0 / block 0 |
| 1. 精简 | 没有产品代码逻辑改动，只改了 skill、共享检查点和测试断言，按 CLAUDE.md 不调用 `/simplify`。`tests/test_templates.py` 新增的两个测试函数手工看过，没有可以消掉的重复 |
| 1. 独立审查第 1 轮 | block 0，review 5，全部修复：①design 写了「本机缓存离线安装」，正文没写，第 2 步已补；②导语原来是「每一步动手前都确认」，改为「动手前列出第 1、2 步的计划，用户确认后再做」，与规格一致；临时目录写明放在仓库外，证据文件放在 worktree 外；第 6 步改为 `git worktree remove --force` 再 `prune`，因为装过依赖的 worktree 用普通 remove 删不掉；第 2 步不再写命令表里没有的「lint 统计」，改为「命令表的 ruff 或前端 lint（加 JSON 输出）」；第 5 步改为「要盯的指标都不应变差」；③测试补上「用户确认后再做」和 `--force` 的断言，description 改为按 `description:` 开头查找，不再靠行号。材料缺口「不可违反」：那一节要求改文件前先列计划等确认、巡检只报告；存量清理是用户提出的，动手前确认一次，不属于巡检，两者不冲突 |
| 1. 独立审查第 2 轮 | block 1，**核实不成立**：审查员说「改既有测试时」一节不存在。实际在 `rules/workflow-gates.md:63`，0.8.19（PR #17）加入；「重构等价性」在 `rules/react.md:27`。第 2 轮的材料只给了 diff，没附这两节原文，第 1 轮附了原文，当时核对过引用。review 3，全部修复：第 5 步删掉与导语重复的「再跑命令表的 lint 与测试」；第 1 步补上清单里的文件有未提交改动时先剔除或请用户先提交，与 skill「工作区里用户已有的改动一律不碰」一致；补「本机缓存离线安装」的断言。第 2 轮只剩 review，修完跑 ruff 与测试，不再审第 3 轮 |
| 2. `uv run ruff check .` | All checks passed |
| 3. `uv run pytest` | 609 passed |
| 3. 判断回归 | 命令表没有这一行，跳过；本次没改判断规则文件或 `JEV_MODEL` |
| 4. 前端 lint | 无前端，跳过 |
| 5. 文案检查 | 无界面文案，跳过 |
| 6. 额外步骤（改了 `rules/`，在接入项目验证） | 见下文 2.1；不提交、不推送 |

## 2.1 接入项目验证

用一个已接入项目，通过 `git worktree add --detach` 把已提交的 HEAD 检出到临时目录，只读：

1. 先用已发布的 0.8.20 运行 `rulemason update --yes`，`check` 显示「日常巡检：一切一致」。把 `.rulemason/`、两份 skill 和清单存一份快照。
2. 再用本仓库源码运行 `rulemason update --yes`，更新了 `workflow-gates.md`、两份 skill 和 `.rulemason.yaml`。
3. 和快照比，差异只有两处：
   - 检查点「自动精简」的那一句；
   - skill 的 description、标题、新的第 7 节，以及「汇报」改为第 8 节（两份 skill 各 17 行变化）。

   `check` 仍是一致，退出码 0。
4. 用 `git worktree remove` 删掉临时目录，再 `git worktree prune`。原检出的 HEAD 和原有未提交改动都没变，没有提交、没有推送。

这次验证用的是第 1 轮审查修改前的正文；后面两轮只改了 skill 第 7 节的措辞，副本的差异范围不变。

## 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `skills/rulemason/SKILL.md` | +30 / −3 | +14 / −3 | 低于估计：六步每步写成一段，第 7 节共 12 行 |
| `rules/workflow-gates.md` | +1 / −1 | +1 / −1 | 一致 |
| `tests/test_templates.py` | +20 / −3 | +23 / −2 | 一致 |
