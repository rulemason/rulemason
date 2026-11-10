# Tasks

## 1. 来源清除（产品面）

- [x] 1.1 删除 `rules/{agent-coding-caution,prose-hygiene,product-artifact-caution}.md` 来源小节
- [x] 1.2 删除 README 致谢段；改写 `prose_hygiene.py` 模块说明为自研表述
- [x] 1.3 主规格三份去掉须归因，改为 MUST NOT 写第三方来源；同步新增原则表述

## 2. 编码审慎四条

- [x] 2.1 `rules/agent-coding-caution.md` 增补可测先行、先根因再修、完成须有当次证据、审阅反馈先核实（无来源、无新预设）
- [x] 2.2 负向/正向测试：`test_agent_coding_caution.py`；`test_product_artifact.py` 改为不含第三方痕迹

## 3. 归档清理

- [x] 3.1 删除 PM 分析 artifacts 与 `full.patch`
- [x] 3.2 归档正文改写去专名；含第三方品牌的归档目录重命名为 `verification-walkthrough`

## 4. 版本与验证

- [x] 4.1 `__version__` 与 README 钉 → 0.8.37
- [x] 4.2 `uv run ruff check .`、`uv run pytest`、`openspec validate --strict`
- [x] 4.3 全仓 rg 复查第三方专名（测试负向 needle 记为合理残留）
