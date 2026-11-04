## MODIFIED Requirements

### Requirement: init 可重复运行，冲突只报告

对已接入且未改动的项目重复运行 `init` SHALL 不产生任何文件改动。遇到无法安全写入的情况（ruff 配置仍写 `select`、无法识别的 ESLint 配置格式、标记块不成对），`init` MUST 跳过该文件并在汇报中说明，不强行改写。`CLAUDE.md` 还没有 `rulemason:claude` 块、`@AGENTS.md` 在全文只出现一次且顶格独占一行（不在代码块里）时，`init` 与 `update` SHALL 用新块替换这一行，不算冲突；其他写法的块外导入（如 `@./AGENTS.md`、缩进或夹在文字里）MUST NOT 修改，照旧报重复导入。

#### Scenario: 第二次运行
- **WHEN** init 成功后立即再次运行 `rulemason init --yes`
- **THEN** 汇报「没有需要改动的文件」，工作区无变化

#### Scenario: ruff 配置写了 select
- **WHEN** 项目 `pyproject.toml` 的 `[tool.ruff.lint]` 写了 `select`
- **THEN** init 不改该文件，汇报写明 `select` 所在的行号与原文、会覆盖基础规则，并给出改为 `extend-select` 或删去该行两种做法，由用户处理

#### Scenario: 卸载后再接入的 CLAUDE.md
- **WHEN** 项目运行过 `rulemason remove`，`CLAUDE.md` 是「`@AGENTS.md`」一行加一段项目自己的说明，之后运行 `rulemason init --tools claude --yes`
- **THEN** 那一行被 `rulemason:claude` 块替换，块内第一行是 `@AGENTS.md`，全文只导入一次 `AGENTS.md`，项目自己的说明逐字不变，「需要你处理」里没有重复导入

#### Scenario: 块外导入写法不同
- **WHEN** `CLAUDE.md` 块外写的是 `@./AGENTS.md`，没有 `rulemason:claude` 块，运行 `rulemason init --tools claude --yes`
- **THEN** 新块照常写入，`@./AGENTS.md` 那一行不变，汇报报出块外重复导入，请用户删去块外那一行

#### Scenario: 代码块里的示例
- **WHEN** `CLAUDE.md` 只在 ``` 代码块里写了一行 `@AGENTS.md` 作为示例，运行 `rulemason init --tools claude --yes`
- **THEN** 代码块逐字不变，新块加在文末，不报重复导入（代码块里的导入不生效）
