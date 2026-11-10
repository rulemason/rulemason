# 功能前后对比（de-ai-flavor-fusion）

## 之前（main）

| 能力 | 状态 |
|---|---|
| 文案卫生确定性检查 | 无 |
| 编码四原则共享规矩 | 无 |
| `result-check --preset` | 无（仅 `--requirements`） |
| init/update 种预设 | 无 |
| 推荐短名默认行为 | — |

## 之后（本分支）

| 能力 | 状态 |
|---|---|
| `prose_hygiene` | 有；短名显式；非作者判别 |
| `rules/prose-hygiene.md` + `agent-coding-caution.md` | init/update **必复制** |
| 默认 severity | `hint`：命中「提示」，单独 **exit 0** |
| 严格模式 | `severity: strict` 或 `--preset strict` → 命中 **exit 1** |
| `em_dash` | 高级可选，预设默认 **关闭** |
| 种子 | `.rulemason/result-check/prose-hygiene.{hint,strict}.json` 仅首次写入 |
| 旧行为 | 未声明 prose 的 requirements / cjk 失败码不变；非法配置仍 2 |

## 何时会跑

仅当调用方执行：

```bash
rulemason result-check --record <记录.json> --requirements <要求.json>
# 或
rulemason result-check --record <记录.json> --preset hint|strict
```

且 requirements / 预设里含 `type: prose_hygiene`。  
`rulemason check` / `init` / `update` **不会**扫仓或因文风命中改 CI 退出码。
