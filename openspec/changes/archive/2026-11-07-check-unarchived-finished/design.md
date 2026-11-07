# Design

## Context

动机见 proposal.md「Why」。现状：

- `gate_records` 只检查接入日之后、日期最新的那一天归档（`src/rulemason/check.py:303`）。没有这种归档时，巡检用说明代替「一致」：「接入后尚未归档，无记录可查」（`src/rulemason/check.py:1135`）。说明只出现在文字版；`findings` 仍是空列表（`tests/test_check.py:818`）。
- 偏离列表为空时才用这句说明（`src/rulemason/check.py:1231`）。
- 退出码只看名称以「接入」开头的层（`src/rulemason/check.py:1195`）。没有别的缺口时，下一步是「日常巡检：一切一致」（`src/rulemason/check.py:1192`）。
- 主规格把「没有已归档 change 时写一致」和「接入后还没归档时写无记录可查」写在 `openspec/specs/rulekit-cli/spec.md:657`。

## Goals / Non-Goals

**Goals:**

- 任务全部勾完、还留在 `openspec/changes/` 的 change，出现在「最近归档的检查点记录」里。
- 退出码和下一步与现在相同。

**Non-Goals:**

- 不审未归档汇报的正文。
- 不把进行中的 change 列进去。

## Decisions

1. **写进现有的「最近归档的检查点记录」，不新开巡检项。** 缺汇报写「<目录名>：没有 verification.md」，有汇报写「<目录名>：尚未归档」。列表非空时，文字版不再只剩「接入后尚未归档，无记录可查」。否决单独加一行：那一行仍会显示无记录可查，读者还是以为没有记录。
2. **只认带 `.openspec.yaml` 的直接子目录，任务只读 `tasks.md`。** 至少有一个勾选框，且每个框内去掉空白后是 `x` 或 `X`，才算勾完。否决运行 `openspec list`：没装这个命令时检查会漏报。否决把 `tasks.md` 不在这个文件名里的 schema 也算进来：这次的接入项目用 spec-driven。
3. **未归档的汇报不查「审查」和「测试」。** 这两项仍只查最近一天的归档。否决对未归档汇报做同样的正文检查：归档前的汇报可以还在写，列名是为了让人看见它还没归档。
4. **不改变退出码和下一步。** 否决因此让 `check` 失败：归档与否是人的决定，CI 不该为此变红。

## Risks / Trade-offs

- [勾选框写法和归档计数不一致] → 完成只认框内去掉空白后的 `x` 或 `X`，其余标记算未完成。
- [进行中的 change 被点名] → 还有未完成的框，或没有勾选框，就不列出。
- [任务写在别的文件名里] → 没有 `tasks.md` 就不列出，汇报里说明这个范围。
- [无记录可查被列表盖住] → 列表里的句子写明缺汇报或尚未归档。

## Migration Plan

1. 本仓库改 `check.py` 与测试，按检查点收尾后发版。发布说明只写：巡检列出任务已勾完、尚未归档的 change。
2. 接入项目升级本机的 `rulemason` 即可，不必 `rulemason update`。本机被精确版本钉住时，用 `uv tool install rulemason@latest`。
3. 回滚：再安装上一版。不改项目文件，没有要迁移的数据。

## 文件与估计行数

| 文件 | 改什么 | 估计 |
|---|---|---|
| `src/rulemason/check.py` | 同一巡检项加上未归档且任务已勾完的 change | +35 / −2 |
| `tests/test_check.py` | 勾完缺汇报、有汇报、未勾完、无勾选框、与归档缺汇报并列 | +48 / −0 |
