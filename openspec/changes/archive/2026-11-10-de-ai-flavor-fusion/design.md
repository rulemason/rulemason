# Design

## Context

用户已确认：规则自动分发；推荐三短名默认 hint、不阻断 CI；`em_dash` 默认关；自动分发≠自动跑；兼容旧退出码；update 种子幂等不覆盖用户文件。

## Goals / Non-Goals

- Goals：双轨落地；hint/strict；种子预设 + `--preset`；端到端测试。
- Non-Goals：改 check 巡检退出码；默认 CI 风格阻断；作者判别；付费依赖。

## Decisions

1. **`severity`: `hint`|`strict`，缺省 `hint`**  
   - 否决：用顶层全局开关——会悄悄改变多检查项语义。  
   - 否决：hint 时改 overall 语义吞掉 FAIL——明确禁止。
2. **新状态「提示」**：计入报告；`_summarize` 视其为非阻断（与「通过」一起允许 overall_pass）；FAIL/无法判断/输入错误仍阻断。
3. **种子文件不进校验覆盖清单**：只在路径不存在时写入；手改后 update 不覆盖、check 不因种子漂移失败。
4. **`--preset hint|strict`**：解析为 requirements；项目种子优先于包内模板；仍须 `--record`。
5. **`em_dash` 留在 KNOWN_RULES**，预设 `rules` 数组不含它。
6. **编码规矩必复制**，仅规则层。

## Risks / Trade-offs

- [用户把 hint 当成已严格门禁] → 对策：报告写明「提示」；文档/CLI 区分 hint/strict。
- [种子与包内模板漂移] → 对策：种子只首次写入；`--preset` 无种子时用包内当前模板。

## Migration Plan

- 前向：update 补规则副本 + 缺失时种子；已有自定义 requirements 不动。
- 回滚：去掉类型与种子文件即可；未声明 prose 的项目无感。

## Open Questions

无（用户已确认默认策略）。
