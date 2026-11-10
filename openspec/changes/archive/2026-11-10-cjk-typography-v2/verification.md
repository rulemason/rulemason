# 验证：cjk-typography-v2

版本：**0.8.33**。Yaomancy 同步本轮未做。

## 样例跑（README.md + rules/**/*.md，全部已知短名）

| 阶段 | 命中 |
|---|---|
| 实现前（规划试跑） | 0 |
| 实现后 | **0** |

无需文档修复；CI allowlist 仍空。

## 门禁

| 项 | 结果 |
|---|---|
| `uv run ruff check .` | 通过 |
| `uv run pytest` | **700 passed** |
| `openspec validate --all --strict` | 通过（含本 change） |
| `rulemason check` | exit 0 |
| Jev `judge --change cjk-typography-v2` | **pass 3 / review 0 / block 0** |

## 干净室

`src/rulemason` 与 `rules/` 无 外部中文排版调研对象 源码/正则/词表拷贝；README 不写外部工具名。

## 跳过

- 未跑其他付费模型 / eval（仅一次 Jev）。
- 未归档、未推送、未发版。
