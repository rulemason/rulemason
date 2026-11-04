# Tasks

## 1. 检查点：只修本次引入的问题

- [x] 1.1 `rules/workflow-gates.md`：apply 后第 2 步与直接改动第 4 步改为「修掉本次改动引入的问题（落在本次改动行上的问题、新加而未使用的 import、因本次改动在未改的行上新出现的问题）；改动前就有的不修，汇报列出数量并建议运行 /rulemason 建立基线」；第 5 行「红线规则」改为「命令表之后列出、供判断使用的实质类规则」；验证：`grep -n "直到通过" rules/workflow-gates.md` 无结果，`uv run pytest tests/test_shared.py tests/test_templates.py` 通过

## 2. skill：建立 ruff 基线

- [x] 2.1 `skills/rulemason/SKILL.md` 新增「建立 ruff 基线」小节：按规则代码统计；四类做法（`I001`/`F401` 排除 `__init__.py` 给出 `--fix` 命令与数量、确认后才跑；`fastapi`/`typer` 声明 `extend-immutable-calls` 并列出函数清单；脚本与命令行入口目录 `T201` 进 `per-file-ignores`；其余按文件写「接入前遗留，改到该文件时清掉」）；列出要写入配置的原文，用户确认后照做，再跑 ruff 并写明前后问题数；不用 `# noqa`；验证：小节含四类做法、两份框架函数清单与「确认后」字样
- [x] 2.2 补项目信息第 6 步改为：ruff 报出问题时转到「建立 ruff 基线」；日常巡检一节写明唯一可写的例外是用户确认的基线计划；验证：`tests/test_templates.py` 中断言 skill「只读，不改文件」的用例按新措辞更新并通过，并新增断言 skill 含「建立 ruff 基线」

## 3. 模板与文档

- [x] 3.1 `src/rulemason/templates/AGENTS.md.tmpl` 命令表下方改为「判断用的红线规则：暂无（判断未启用；项目红线见上文「红线」一节）」；`tests/test_init.py:209` 的断言跟着改；验证：`uv run pytest tests/test_init.py` 通过，对临时项目运行 `rulemason init --yes` 后 AGENTS.md 出现新写法，`rulemason check` 第一行仍是「补项目信息」
- [x] 3.2 README 与 README.en「日常」一节补一句：已有大量代码的项目接入后，先在 AI 工具里运行 `/rulemason` 建立 ruff 基线；验证：中英命令表同步测试通过，两份 README 各出现这一句

## 4. 收尾

- [x] 4.1 照问题报告搭临时项目（FastAPI 后端，含 `Depends` / `Query`、`scripts/` 下的 `print`、未排序的 import、未用导入与几处其他问题），按新 skill 走一遍基线；验证：确认前不改任何文件，确认后 `ruff check .` 通过，`per-file-ignores` 只含「接入前遗留」与脚本目录两类条目，没有 `# noqa`，前后问题数写进 `verification.md`
- [x] 4.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙的 worktree 运行 `rulemason update --dry-run`，确认只刷新检查点与 skill 副本；验证：结果与 design 行数对照写进 `verification.md`

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本（lint-fix-guidance 可能先占用 0.8.11），bump 版本与 README、README.en 的 CI 钉版本，推送、归档、打 tag。
- 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`。
- 在问题报告里的 monorepo 运行一次 `/rulemason` 建立基线，确认 ruff 通过、后端测试结果不因自动修复而变化。
