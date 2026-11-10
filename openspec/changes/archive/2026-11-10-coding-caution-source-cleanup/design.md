# Design

## Context

- 基线：`main` @ `1fd7ac66`（0.8.36）。出处：`git rev-parse HEAD` / `__version__`。
- 现行分发规矩曾含来源小节；主规格曾要求归因。出处：实现前 `rules/*.md`、`openspec/specs/*/spec.md`（现已改）。
- 编码审慎已有四条过程原则；本期再加四条。出处：`rules/agent-coding-caution.md`。
- 用户确认：同 PR 清来源 + 加原则；不合并、不打 tag、不发版；归档去专名并重命名含第三方名的目录。

## Goals / Non-Goals

**Goals:**
- 产品面（规矩、README、注释、主规格、测试）无第三方专名/URL/SHA。
- 编码审慎八条齐全；负向测试锁住「分发正文无第三方痕迹」。
- 归档历史可读但无专名；版本钉 0.8.37。

**Non-Goals:**
- 不 yank 旧 PyPI；不改写已推送 git 历史；不新增 result-check 预设；不跑付费判断。

## Decisions

1. **整段删除来源小节，不改成中性致谢句**  
   - 否决：保留「行为参考外部调研」中性句——仍暗示外部依赖，用户已选整删。

2. **测试用字面第三方名做负向断言**  
   - 否决：编码混淆 needle——可读性差，且方案明确要求负向断言专名。

3. **归档：删分析 artifacts + 改写正文 + 旧归档目录名 → `verification-walkthrough`**  
   - 否决：只删 artifacts 留 design URL——仍暴露来源；否决保留目录品牌名——用户已选重命名。

4. **主规格改为 MUST NOT 写第三方来源，并同步归档 delta**  
   - 否决：只改规矩不改规格——`openspec validate` 与契约会漂移。

## Risks / Trade-offs

- [归档改写后历史语义变淡] → 保留功能结论与任务勾选，只去专名/URL/SHA。
- [负向测试字面含专名] → 仅 `tests/` 允许；全仓 rg 时记为合理残留。
- [用户手改过的规矩副本] → 仍走既有 `update`/`check` 落后策略，不另开覆盖逻辑。

## Migration Plan

1. 合并本 PR 后发版（另轮）→ 用户 `rulemason update` 刷副本。
2. 回滚：还原本 PR；旧包行为不变。不 yank。

## 文件与估计行数

| 文件 | 估计 |
|---|---|
| `rules/agent-coding-caution.md` | +8～12 |
| `rules/prose-hygiene.md` / `product-artifact-caution.md` | −5～15 各 |
| `README.md` | −5～10 |
| `src/rulemason/prose_hygiene.py` | ~±3 |
| `openspec/specs/{agent,product,verification}-*/spec.md` | ±20～40 各 |
| `tests/test_product_artifact.py` / `test_agent_coding_caution.py` | ±20～40 |
| `src/rulemason/__init__.py` | 1 |
| 归档多文件 | 改写/删除/重命名 |

## Open Questions

无。
