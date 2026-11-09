## MODIFIED Requirements

### Requirement: init 生成项目内只读副本

`init` SHALL 把项目用得上的共享规则正文与 lint 基础配置复制到 `.rulemason/`：`code-style.md`、`workflow-gates.md`、`cjk-typography.md` 与 `result-check-contracts.md` 必复制；`python.md` 与 `ruff-base.toml` 只在识别到 Python 时；`react.md` 只在识别到 React 目录时；`eslint-base.mjs` 在有 React 目录或已有 ESLint 配置时；`copy-voice.md` 只在有前端目录或判断已启用时。`rulemason` skill 的 `SKILL.md` SHALL 复制到每个已选工具的 skill 发现路径，`.rulemason.yaml` 记录每个生成文件的校验值，副本的有无以清单为准；项目后来出现新语言时由 `update` 补齐。判断层模板 MUST NOT 复制进项目。副本 SHALL 作为项目文件提交，MUST NOT 被手工修改。

#### Scenario: 同事克隆项目
- **WHEN** 同事克隆一个已接入并提交的项目，本机没有装 rulemason
- **THEN** 所选工具能读取 `.rulemason/` 中的规则正文并发现 `/rulemason` skill

#### Scenario: 项目不在 rulekit 的同级目录
- **WHEN** 项目位于任意目录，附近没有 rulemason 仓库
- **THEN** 接入与 ruff 继承照常生效，不出现读取项目外文件的确认

#### Scenario: skill 副本只有一个文件
- **WHEN** 选了 Claude Code 的项目运行 `rulemason init`
- **THEN** `.claude/skills/rulemason/` 下只有 `SKILL.md`，没有 `templates/`

#### Scenario: Go 项目只拿到通用规则
- **WHEN** 只有 `go.mod` 与 `.go` 文件的项目运行 `rulemason init --tools claude --yes`
- **THEN** `.rulemason/` 下只有 `rules/code-style.md`、`rules/workflow-gates.md`、`rules/cjk-typography.md`、`rules/result-check-contracts.md` 与 `README.md`，没有 `python.md`、`react.md`、`copy-voice.md` 与 `lint/`；`check` 不报缺少副本

#### Scenario: 后来加了 Python
- **WHEN** 上述项目新增 `pyproject.toml` 后运行 `rulemason update`
- **THEN** 补上 `rules/python.md` 与 `lint/ruff-base.toml`，清单记录它们，入口块加上 python.md 的引用

## ADDED Requirements

### Requirement: 中文排版与 result-check 契约规则必复制并被入口引用
`init` 与 `update` SHALL 把 `rules/cjk-typography.md` 与 `rules/result-check-contracts.md` 复制进项目 `.rulemason/rules/`（所有接入项目，与 code-style 同级必复制），清单记录校验值。AGENTS / Claude / OpenCode 等入口中的 code-style 类标记块 SHALL 引用这两份副本（可注明阅读场合）。`check` MUST 在副本缺失或被手改时非 0 退出。既有检查项与无新规则时的项目行为 MUST 在 `update` 补齐后恢复一致。

#### Scenario: 无前端项目也拿到两份规则
- **WHEN** 仅有 Python、无前端的项目运行 `rulemason update`
- **THEN** `.rulemason/rules/` 含 `cjk-typography.md` 与 `result-check-contracts.md`，入口块出现对二者的引用

#### Scenario: 手改排版规则副本被查出
- **WHEN** 项目手改 `.rulemason/rules/cjk-typography.md` 后运行 `rulemason check`
- **THEN** 以非 0 退出并报告该副本不一致

#### Scenario: 升级补齐不破坏旧命令表
- **WHEN** 已接入项目从无这两份规则的版本升级并 `rulemason update --yes`
- **THEN** 补上两份副本与入口引用，项目命令表与红线正文不被改写
