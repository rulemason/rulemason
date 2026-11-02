# rulemason

给 AI 编码工具的共享规则与检查点。共享正文只在本仓库编辑；接入项目内是 `rulemason init` / `rulemason update` 生成的只读副本（`.rulemason/` 与 skill 副本），手改由 `rulemason check` 发现。

产品名、命令名、skill ID 与 PyPI 包名都是 `rulemason`，公开仓库为 `rulemason/rulemason`。本仓库的 `.rulemason.yaml` 是工具选择的唯一记录。

## 目录

- `rules/`：给 AI 与人读的规矩：`code-style.md`、`python.md`、`react.md`、`workflow-gates.md`、`copy-voice.md`。
- `lint/`：给工具读的基础配置：`ruff-base.toml`、`eslint-base.mjs`。
- `openspec-base/`：项目照写进 `openspec/config.yaml` 的产物规则基础版。
- `src/rulemason/`：`rulemason` 命令行（`init`、`update`、`check`、`judge`）、init 用的模板与从 rulekit 0.5 迁移的逻辑（根目录 `pyproject.toml`）。
- `src/rulemason/judge/`：共享判断引擎（`rulemason judge`，库 `rulemason.judge`），含通用判断规则与短标签词表。
- `skills/rulemason/`：`/rulemason` skill 正文与阶段三模板，由 `rulemason init` 复制进项目。
- `tests/`：命令行的测试；引擎测试在 `tests/judge/`。
- `openspec/`：本仓库自己的 change 与规格。

## 不可违反的约定

- 每条规矩只住一处：共享正文只放本仓库；项目专属的红线、context、项目判断规则与回归用例只放各项目。
- 共享文件不写项目专属路径、命令或领域词。
- 改共享文件会影响所有接入项目；实施前检查影响范围，之后在受影响项目验证。
- 仓库公开：不得提交密钥、本机绝对路径或私人项目名。每个 clone 从仓库根目录执行 `git config core.hooksPath .githooks` 启用 `.githooks/pre-commit`；私人项目名写进本机 `.git/info/private-words`（不入库），由它拦截。
- 只属于本机的项目指令（如阶段学习文档的落点）写在不入库的 `CLAUDE.local.md`。

## Code style

共享正文只住在以下文件；开始代码工作前读取适用文件，不要把正文复制到本文件或其他项目：

- `rules/code-style.md`：九条通用写法原则
- `rules/python.md`：Python 落法
- `rules/react.md`：React / TSX 落法（本仓库没有 React，入口不引用）

本仓库 Python 样板为 `src/rulemason/judge/judge.py` 与 `src/rulemason/check.py`。ruff 豁免见根目录 `pyproject.toml`。

## Workflow gates

检查点正文只住在 `rules/workflow-gates.md`。每个 change 的方案、实现前与实现后都读取并遵守该文件。

本仓库命令表（在仓库根目录执行）：

| 名称 | 命令 |
|---|---|
| 判断 | `rulemason judge --change <name>`（本仓库无项目规则，只跑通用规则） |
| ruff | `uv run ruff check .` |
| 测试 | `uv run pytest` |
| 前端 lint | 无前端，跳过 |
| 文案检查 | 无界面文案，跳过 |

红线规则：暂无（只有 `design-no-speculative-extension`）。

额外步骤：改了 `rules/` 或 `lint/` 时，在接入项目验证受影响的检查；记录结果，不提交或推送。
