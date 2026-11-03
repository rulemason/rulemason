## Context

见 proposal.md 的 Why。现状：

- `check.archived(root)` 只统计 `openspec/changes/archive/` 下的目录数。归档目录名一律是 `YYYY-MM-DD-<change>`（`openspec archive` 生成）。
- `check.audit` 按顺序往 `report.findings` 里追加巡检项，空列表显示为「一致」。巡检项不参与 `exit_code` 与 `next_stage`。
- 现有 `verification.md` 写法不一：编号小节、自由小标题、整张表格都有，所以只能按关键词判断。

## Goals / Non-Goals

**Goals:**
- 每次归档后运行一次 check（本地或 CI），就能看出这次归档有没有留下审查与测试的记录。

**Non-Goals:**
- 不判断汇报内容是否属实，也不要求固定格式。

## Decisions

### D1 只看「最新日期」那一天的全部归档

把归档目录按名字排序，取日期前缀最大的那一天，那一天下的 change 全部检查。
否决：只取名字排序最后一个。同一天归档多个时，按名字排序得到的是字母序最后一个，不一定是最后归档的，会漏掉同日的其他 change。否决：按目录修改时间。克隆、检出都会改变修改时间，不可靠。否决：检查全部归档。历史归档大多没有这个文件，补写等于造假，有用的那一条还会被淹没。

### D2 关键词判定，中英都认

文件内容（不分大小写）同时包含「审查」或 `review`，以及「测试」或 `test`，就算合格。缺哪一样就报哪一样；文件不存在则报「没有 verification.md」。
否决：要求「## 审查」「## 测试」这样的固定标题。项目丙那种整张表格的汇报会被误判；要改格式，得先改共享检查点并让所有项目适应，代价远大于收益。

### D3 只报告

新巡检项追加在 `audit` 末尾，结果只进 `report.findings`，不进 `report.layers`。
否决：放进「接入」层让 check 非 0。能修的只有补写过去的汇报，这会逼人造假；一个历史 change 也会让 CI 一直变红。

## Risks / Trade-offs

- [只写了「测试：未运行」也会被判合格] → 本项只核对「有没有记录」，不核对记录写了什么；内容是否属实由用户看汇报判断。
- [目录名不符合 `YYYY-MM-DD-` 格式（手工移动的归档）] → 这类目录不参与「最新日期」的比较，直接忽略。
- [项目甲、乙升级后多出一条提示] → 这是想要的结果：提示的正是最近一次没有留记录的归档。下次按检查点归档后，这条提示就会消失。

## Migration Plan

1. 实现并通过 ruff 与测试。在项目甲、乙、丙的 worktree 里运行 check，记录这一项的结果。
2. 发版 0.8.7，接入项目升级即可，不需要 update。
3. 回滚：`uv tool install rulemason==0.8.6`。这次不涉及副本与清单。

## 文件与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/check.py` | `gate_records(root)` 与巡检项 | +25 |
| `skills/rulemason/SKILL.md` | 日常巡检说明一句 | +1 |
| `tests/test_check.py` | 五个场景 | +45 |
