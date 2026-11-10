# Verification — pm-artifact-guidance-fusion

基线分支：`main` @ `71564ca`（0.8.34，`git fetch origin main` 核实）。实现分支：`cursor/pm-artifact-guidance-impl-aa93`。
本地实现提交：`5258e72`（其后另有 docs 提交附 `artifacts/full.patch`）。**未 push / 未开 PR / 未归档 / 未发版**。

## 已实现功能（真实）

- 自研 `rules/product-artifact-caution.md` 经 `init`/`update` 必复制；入口引用；不进默认判断红线。
- `must_contain`/`pattern` 可选 `severity`（缺省 `strict`）；`product-artifact.hint|strict` 预设；`--preset hint|strict` 仍为 prose-hygiene。
- 种子首次写入、幂等不覆盖；`remove` 删除；wheel/sdist 含规则与预设模板。

## 限制（如实）

- 结构标题存在 ≠ 实质质量 / 指标已达成。
- 不剥代码围栏（围栏内假标题可误报通过，测试锁定）。
- 无 LLM/REA 运行时；init/update 不扫仓、不检查文档。
- CC BY-NC-SA 来源未再分发正文。

## 测试结果（本次实测）

| 项 | 结果 |
|---|---|
| `uv run ruff check .` | 通过 |
| `uv run pytest` | **742 passed**（本次全量；不宣称「旧 725」） |
| `openspec validate --specs --strict` | 13 passed |
| `openspec validate --all --strict` | 14 passed（含本 change） |
| `openspec validate pm-artifact-guidance-fusion --strict` | valid |
| `uv build` | 见构建步骤；wheel/sdist 资源断言在 pytest 内 |
| 付费 Jev / 判断回归 | **未跑**（按要求注明） |

## 计划差异

- 规划示例曾写 `--preset hint` 做结构检查；实现改为无歧义 `product-artifact.*`，保留 hint/strict=prose。
- 验收同义词正则由错误的 `验收标准?` 改为 `验收(?:标准)?`。
- 未升版本号、未归档、未推送、未发版。

## 产物

- 前后对比：`artifacts/before-after.md`
- 配置/限制/CLI：`artifacts/configs-and-limits.md`
- 完整补丁：本地 git commit（不 push）
