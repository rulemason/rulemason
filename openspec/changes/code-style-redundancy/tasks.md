# Tasks

## 1. 九条措辞

- [x] 1.1 `rules/code-style.md` 第 9 条重写：不加、不留当前没有调用方的参数、配置项、扩展点、函数和文件；只有一个调用方、自身不带逻辑的抽象层（只转发参数的包装函数、只有一个实现的基类或接口、只为一处调用建的工厂或策略类）直接内联，出现第二个调用方再抽；为降低复杂度拆出、带有自己逻辑的辅助函数不算。验证：`tests/test_templates.py` 新增断言第 9 条含「函数和文件」「直接内联」「带有自己逻辑的辅助函数不算」，`test_rules_wording_key_sections` 仍断言九条正好 9 条，`uv run pytest tests/test_templates.py` 通过。
- [x] 1.2 `rules/code-style.md` 第 8 条末尾补一句：不为上游已保证的条件再加判断或包 `try`（已校验的参数、类型已排除的空值、不会抛异常的调用），是否保证以调用链里看得到的校验或类型声明为准；看不出保证时不删检查，按第 3 条写明「走到这里说明什么」。原有半句不改顺序。验证：同一测试断言第 8 条同时含「静默改走另一条路径」和「上游已保证」，`uv run pytest tests/test_templates.py` 通过。
- [x] 1.3 `rules/react.md` 第 9 条补：只有一处使用、只转发 props 的包装组件直接内联。验证：`test_react_rules_are_shared_and_project_neutral` 补断言第 9 条含「包装组件」，项目中立断言仍通过。

## 2. 收尾与跨项目验证

- [x] 2.1 按检查点做收尾：规则正文只改文档，测试代码的改动（新增断言与抽出的取行函数）手工精简并写明结果；然后做独立审查、`uv run ruff check .`、`uv run pytest`。验证：三项结果和 design 的估计行数对照写进 `verification.md`。
- [x] 2.2 在已接入的项目里运行开发版 `rulemason update --dry-run`，不提交也不推送。验证：计划只列出 `.rulemason/rules/code-style.md`、`.rulemason/rules/react.md`（前端项目才有）和 `.rulemason.yaml`，结果记进 `verification.md`。

## Workflow follow-up

- 发版：先查 `git tag` 和 PyPI 上已有的版本，再 bump 版本号；发布说明写明第 8、9 条新措辞，并说明检查点只审本次 diff，存量清理另有入口（`cleanup-mode`）。
- 接入项目运行 `uv tool upgrade rulemason`、`rulemason update`，按项目惯例提交。
- 本 change 归档后，再对 `cleanup-mode` 运行 `/opsx-propose`。
