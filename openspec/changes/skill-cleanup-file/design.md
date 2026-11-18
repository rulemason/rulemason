## Context

动机见 proposal.md「Why」。与做法相关的现状：

- skill 副本由 `src/rulemason/shared.py:46` 的 `SKILL_FILES = ("SKILL.md",)` 决定，`generated_files` 按这个元组逐个复制到各工具的 skill 发现路径（`shared.py:193-195`）。清单、`check` 的比对、`update` 的补齐都基于 `generated_files` 的结果，不单独认文件名。
- 打包已收整个目录：`pyproject.toml` 的 `force-include` 写的是 `"skills/rulemason" = "rulemason/_shared/skills/rulemason"`。
- 本仓库自己的 `.claude/skills/rulemason` 与 `.agents/skills/rulemason` 是指向 `skills/rulemason` 的符号链接（`ls -la .claude/skills .agents/skills`），新文件不需要另外分发。
- `update` 会删除「清单记录过、当前版本不再生成、且没被手改」的副本（`src/rulemason/init.py:338` 的 `plan_stale_copies`）。
- `SKILL.md` 共 168 行，第 7 节「存量清理」在第 139–164 行，约 7600 字节（`sed -n 139,164p skills/rulemason/SKILL.md | wc -c`）。第 1 节第 35 行写了清理时的入口闸门与展示方式；第 7 节里有三处指回别的节：「按第 1 节停下」「展示按第 1 节」「汇报按第 8 节写」。
- 代码里没有解析清理提交的地方（`grep -rn cleanup src/rulemason/*.py` 无结果），完成标记只是 skill 的约定。
- 测试：`tests/test_templates.py` 的 `test_skill_is_one_file_and_templates_ship_with_engine` 断言 skill 目录只有 `SKILL.md`；`test_skill_legacy_cleanup_section` 从 `SKILL.md` 切出第 7 节，断言不超过 70 行并含约 60 个原文短语。`tests/test_check.py:326`、`tests/test_init.py:208,442` 按 `shared.SKILL_FILES` 计数，会自动跟着变。

## Goals / Non-Goals

**Goals:**

- 清理正文搬家后逐字不变，只在开头加一句章节引用的说明，并改完成标记与收尾两处。
- 日常用 `/rulemason` 的路径（补项目信息、巡检、启用判断）不再读到清理正文。

**Non-Goals:**

- 不给 `cleanup.md` 单独的清单条目或巡检项，它和 `SKILL.md` 一样按生成副本处理。

## Decisions

1. **新文件放在 skill 目录根下，叫 `cleanup.md`**。否决：放进 `references/` 子目录。多一层目录，对复制逻辑没有好处；skill 目录只有两个文件，平放足够清楚。
2. **`SKILL.md` 保留「## 7. 存量清理（可选，用户提出时才做）」标题，正文换成一段入口**。否决：删掉第 7 节、后面重新编号。第 1 节第 35 行与测试都按「第 7 节」引用，重新编号会牵动一串无关改动。入口写明：读本 skill 目录下的 `cleanup.md` 并照做，没读到就不开始清理。
3. **第 1 节第 35 行的入口闸门与展示规则留在 `SKILL.md`**。否决：一起搬进 `cleanup.md`。这一行决定的是「要不要进入清理」，必须在读 `cleanup.md` 之前生效。`cleanup.md` 正文里的「第 1 节」「第 8 节」不逐处改写（其中两处被测试按原文断言），改为在开头加一句：文中的章节指同目录 `SKILL.md` 的章节。
4. **阶段提交用 `refactor(cleanup-step): <模块> 第 N 步`**。否决：最后一次提交加尾注 `Cleanup-Complete: <模块>`，诊断改认尾注。已完成的模块都是按 `refactor(cleanup): <模块>` 记的，改认尾注要么认不出它们，要么得两种都认。也否决「同一个前缀后面加『阶段 N』」：`refactor(cleanup): <模块> 阶段 1` 仍以 `refactor(cleanup): <模块>` 开头，诊断照样会误判。
5. **`rulekit-cli` 规格里的场景名「skill 副本只有一个文件」保留不改，只改 THEN**。否决：改名为「只有正文文件」。OpenSpec 不允许 MODIFIED 里丢掉已有场景（`openspec validate --strict` 报错），只能保留原名；名字与内容不完全贴合，在这里记下。
6. **测试按「改既有测试时」处理**：切片来源从 `SKILL.md` 第 7 节改为 `cleanup.md` 全文，短语一个不少；70 行上限照旧作用于 `cleanup.md` 的正文。另加断言：`SKILL.md` 第 7 节只剩入口且点名 `cleanup.md`，`cleanup.md` 写明阶段提交前缀。

## Risks / Trade-offs

- [其他工具的代理读了 SKILL.md 却没去读 cleanup.md] → 入口一段写明文件位置，并写明没读到就停下说明，不凭记忆清理。
- [用户分阶段提交时仍用旧前缀] → skill 不提交，强制不了；`cleanup.md` 在完成标记一段与收尾两处都写明前缀；收尾按计划里是否还有步骤没做完，分成两个互斥的分支，分别给出阶段提交或最终提交的完整说明。
- [接入项目升级后 check 先报副本与本机版本应生成的不一致] → 预期行为，`next.code` 为 `update`；发版说明写明运行 `rulemason update`。
- [70 行上限原来量的是 SKILL.md 第 7 节，搬家后量的是 cleanup.md 全文，多出标题与说明行] → 搬家后实测行数，超出时只把上限改到实测值加说明，不删正文。

## Migration Plan

1. 本仓库合并本 change，发补丁版本。
2. 接入项目升级本机 rulemason 后运行 `rulemason update`，补上 `cleanup.md`。
3. 按 AGENTS.md「额外步骤」，在一个接入项目用开发版只读运行 `rulemason update --dry-run` 与 `rulemason check`，确认只多出 `cleanup.md` 与 `SKILL.md` 的变化。

回滚：还原本 change 的提交并发补丁版本；接入项目再运行 `rulemason update`，`plan_stale_copies` 会删掉未手改的 `cleanup.md`，`SKILL.md` 恢复原文。

## 新增与修改的文件

| 文件 | 估计改动行数 |
|---|---|
| `skills/rulemason/cleanup.md`（新增） | 约 30 行 |
| `skills/rulemason/SKILL.md` | 约 26 行删除、3 行新增 |
| `src/rulemason/shared.py` | 1 行 |
| `tests/test_templates.py` | 约 15 行 |
| `tests/test_check.py` | 约 14 行 |
