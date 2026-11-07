## ADDED Requirements

### Requirement: 巡检列出做完却未归档的 change

`rulemason check` 的「最近归档的检查点记录」SHALL 同时列出 `openspec/changes/` 下带 `.openspec.yaml` 的直接子目录里，任务已全部勾完且尚未归档的 change。任务以该目录 `tasks.md` 的勾选框计：至少有一个勾选框，且每个框内去掉空白后是 `x` 或 `X`，才算全部完成。没有 `tasks.md`、没有勾选框，或仍有未完成的框，MUST NOT 列出。没有 `verification.md` 时 SHALL 列出「<名>：没有 verification.md」；有该文件时 SHALL 列出「<名>：尚未归档」。这一项 MUST NOT 因此改变退出码或下一步。接入日之后没有归档时，只要列出了这种 change，这一项就 MUST NOT 只写「接入后尚未归档，无记录可查」。

#### Scenario: 勾完了但没有汇报
- **WHEN** 接入日之后没有归档，`openspec/changes/done-without-report/` 的 `tasks.md` 每个勾选框都是 `x`，且没有 `verification.md`
- **THEN** 这一项列出「done-without-report：没有 verification.md」，退出码为 0，下一步仍是「日常巡检：一切一致」，文字里不只是「接入后尚未归档，无记录可查」

#### Scenario: 有汇报但还没归档
- **WHEN** `openspec/changes/done-with-report/` 的任务已全部勾完，且目录里有 `verification.md`
- **THEN** 这一项列出「done-with-report：尚未归档」，退出码与下一步不变

#### Scenario: 还有任务没勾
- **WHEN** 接入日之后没有归档，某个 change 的 `tasks.md` 里还有未勾的框
- **THEN** 不列出这个 change；这一项仍写「接入后尚未归档，无记录可查」

#### Scenario: 没有勾选框
- **WHEN** 某个 change 的 `tasks.md` 只有普通列表，没有勾选框
- **THEN** 不列出这个 change

#### Scenario: 归档缺汇报和未归档的 change 一起列出
- **WHEN** 最近一天的归档里有一个 change 没有 `verification.md`，同时 `openspec/changes/` 里另有一个任务已全部勾完的 change
- **THEN** 这一项同时列出两者
