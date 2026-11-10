# 配置说明、CLI 样例、限制与迁移

## CLI 真实样例

```bash
# 文案卫生（旧短名，语义不变）
rulemason result-check --record out.json --preset hint
rulemason result-check --record out.json --preset strict

# 产物结构（无歧义 id）
rulemason result-check --record prd.json --preset product-artifact.hint
rulemason result-check --record prd.json --preset product-artifact.strict

# 自定义 requirements（可混用 field / pattern / prose_hygiene）
rulemason result-check --record prd.json --requirements my-reqs.json
```

## 默认 / 严格 / 关闭 / 自定义

| 模式 | 做法 |
|---|---|
| 默认（结构） | `--preset product-artifact.hint` 或种子里 severity=hint |
| 严格门禁 | 显式 `--preset product-artifact.strict` |
| 关闭 | 不调用该预设、requirements 不含对应项 |
| 自定义 | 改 `.rulemason/result-check/product-artifact.*.json` 或自写 requirements；update **不覆盖**已有种子 |

## 默认小节同义标题（最小中英）

- 非目标：`非目标` / `不在范围内` / `Out of Scope` / `Non-goal(s)`
- 成功或验收：`成功标准` / `验收` / `验收标准`（正则 `验收(?:标准)?`）/ `Success Criteria` / `Acceptance`
- 匹配：Markdown AT题行 `^#{1,6}`（大小写不敏感）

## 限制（如实）

- 结构存在 ≠ 实质质量 / 商业成功 / 指标已达成。
- 不剥代码围栏：围栏内假标题可误报通过（测试锁定）。
- 正文里出现「非目标」字样但无标题行 → 不匹配（预期）。
- `field` / `cjk` / `must_not_contain` 本轮无 severity。
- 不自动扫仓；init/update **不**检查文档。
- 不进默认判断红线；无 LLM/REA 运行时依赖。
- REA 仅规划阶段只读分析；不能替代读 PM 技能正文。
- CC BY-NC-SA 来源**未**再分发正文/模板。

## 迁移

- 未选用 `product-artifact.*` 的项目：无感。
- 未写 `severity` 的 `must_contain`/`pattern`：仍失败（与 0.8.34 前一致）。
- `--preset hint|strict`：仍为 prose-hygiene。
- 回滚：删规矩与种子即可。
