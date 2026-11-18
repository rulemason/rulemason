## 1. 先写会失败的测试

- [x] 1.1 `tests/test_templates.py`：Claude 入口模板的导入列表去掉 4 份写作类规则；OpenCode 模板不含这 4 份；`code-style.block.md` 仍列出这 4 份，且不含 `--preset`、「只分发不扫仓」；字数上限改为 10100；归档一节断言「运行 `rulemason check`」「原样转述」「不代用户配置 key」，并且不再含「正好是 3」。验证：`uv run pytest tests/test_templates.py` 只有这些断言失败。
- [x] 1.2 `tests/test_check.py`：启用提示的四个场景（第 3 个归档且没有 key、接入后第 1 个且有 key、之后不再提示、已启用不提示），断言第二行文字、`next.code` 与退出码不变。验证：此时失败。
- [x] 1.3 `tests/test_update.py`（或 `test_init.py`）：OpenCode 配置里有这 4 项时，`update` 不改写配置文件，计划列出可手动删去的条目。验证：此时失败。

## 2. 入口与提示

- [x] 2.1 `claude.block.md`、`opencode.jsonc.tmpl` 去掉 4 份写作类规则；本仓库 `CLAUDE.md` 同步。验证：1.1 中模板相关断言通过，`test_claude_block_imports_rules_and_maps_simplify_step` 通过。
- [x] 2.2 `code-style.block.md` 与本仓库 `AGENTS.md` 的 Code style 列表：这几行只写阅读场合。验证：1.1 相关断言通过；`tests/test_product_artifact.py`、`tests/test_prose_hygiene.py` 照旧通过。
- [x] 2.3 `check.py`：在 `collect` 里按条件给 `report.next_notes` 加启用提示，文字见 design「措辞草稿」。验证：1.2 通过。
- [x] 2.4 `init.py` 的 `plan_opencode`：已有配置含这 4 项时加一条提示，不改文件。验证：1.3 通过。
- [x] 2.5 `rules/workflow-gates.md` 第 5 步换成一句转述，测试里的字数上限改为 10100。验证：1.1 归档断言与字数测试通过，记录实际字数。

## 3. 检查点与验证

- [x] 3.1 按 `rules/workflow-gates.md`「apply 最后一个任务做完」执行：自动精简、独立审查、`uv run ruff check .`、`uv run pytest`。验证：结果写进 `verification.md`；旧测试 `test_gates_archive_merges_without_asking_and_hints_key_once` 的断言搬到了哪里逐条列出。
- [x] 3.2 额外步骤：在一个接入项目用开发版只读运行 `rulemason update --dry-run` 与 `rulemason check`。验证：只有 `CLAUDE.md`、`AGENTS.md` 标记块与副本变化，项目 `git status` 前后不变；记录进 `verification.md`。
- [x] 3.3 `openspec validate writing-rules-on-demand --strict` 通过，并在 `verification.md` 写发版说明草稿（升级产出要随升级提交；OpenCode 项目可手删 4 项）。
