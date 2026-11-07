## Why

`rulemason check` 的「最近归档的检查点记录」只看接入日之后的归档。任务已经勾完、却还留在 `openspec/changes/` 的 change，巡检会写成无记录可查，下一步仍是一切一致。

## What Changes

- 同一巡检项列出 `openspec/changes/` 里任务已全部勾完、尚未归档的 change。没有 `verification.md` 的写明缺汇报；有汇报的写明尚未归档。
- 还有未勾完的任务，或没有勾选框的，不列出。
- 接入日之后没有归档时，只要列出了这种 change，这一项就不能只写「接入后尚未归档，无记录可查」。
- 退出码和下一步不变。最近一天归档缺汇报的检查保持原样。
- 不做：
  - 不因此让 `check` 失败，也不改下一步。
  - 不审未归档 change 的汇报里有没有写到审查和测试。
  - 不调用 `openspec` 命令。
  - 不改清理队列，不改判断规则，不改项目依赖里的版本钉。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：巡检在最近归档的检查点记录里，一并列出做完却未归档的 change。

## Impact

- `src/rulemason/check.py`：同一巡检项增加未归档 change。
- `tests/test_check.py`：补勾完、未勾完、有汇报三种情况。
