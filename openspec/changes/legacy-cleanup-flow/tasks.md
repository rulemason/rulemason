# Tasks

## 1. skill 与检查点

- [x] 1.1 `skills/rulemason/SKILL.md` 新增第 7 节「存量清理（可选，用户提出时才做）」六步（规划含先规划共用模块与不得要求「不新建文件」、先存证据含临时 worktree 与不经 stdin 的原因、代理指令要点、恢复、主会话复核、收尾），原「汇报」改为第 8 节；frontmatter description 与开头一句补「存量清理」；验证：第 7 节不超过 30 行，`grep -n "^## " skills/rulemason/SKILL.md` 顺序为 1–8，没有项目专属词
- [x] 1.2 `rules/workflow-gates.md`「自动精简」一段加「新增函数先按名检索，已有同名或同用途的实现就复用」；验证：`git diff rules/workflow-gates.md` 只有这一处
- [x] 1.3 `tests/test_templates.py`：章节顺序改为 8 节、基线两节的切分边界随之改；新增第 7 节关键措辞断言（worktree、stdin、共用模块、`git diff` 恢复）与查重一句断言；验证：`uv run pytest tests/test_templates.py` 通过

## 2. 验证

- [x] 2.1 在一个接入项目运行 `rulemason update`（临时 worktree，只读）：副本只多第 7 节与查重一句，`rulemason check` 一致；验证：结果写进 `verification.md`，临时目录删除
- [x] 2.2 按 workflow gates 完成：无代码逻辑改动跳过精简，独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
