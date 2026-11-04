# Verification：legacy-lint-baseline

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。

## 写代码前检查点

`rulemason judge --change legacy-lint-baseline`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简**：跳过。本次只改共享正文、skill、模板、README 与测试，`src/rulemason/` 下没有代码逻辑改动（模板只改一行文字），无代码改动，跳过精简。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 0，review 12，全部修复：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：直接改动第 4 步对「遗留豁免可选清掉」只是间接覆盖 → 改为「判断方法与遗留豁免的处理同第 2 步」；「本次引入」在 spec、design、正文三种口径 → 统一为「落在新增或修改行上、新加未用的 import、因本次改动在未改行上新出现的问题」，design 决策 5 删去「对改动过的文件运行」；design Risks 说巡检可提旧写法，skill 没写 → skill 日常巡检补一条 |
| 正确性 | review：只看改动行会漏掉报在未改行上的 C901、I001、F821 → 检查点补这一类；按文件豁免会放过遗留文件里新写的同类问题 → design Risks 写明与可选缓解命令；确认前列不出遗留条目原文 → 写明确认时是预估、确认后以重跑为准；命令行点名文件时 `--extend-exclude` 不生效 → 加 `--force-exclude` |
| 安全 | review：`--fix` 可能改到用户未提交的文件 → 计划先用 `--diff` 列出会改的文件并与 `git status` 对照，重叠时请用户先提交或排除 |
| 代码质量 | review：交叉引用「第 5 步」与第 2 节自己的第 5 步重名 → 改为节名「5. 建立 ruff 基线」；巡检例外说了两遍、「基线完全写在配置里」不准确 → 只说一次，改为「豁免全部写在」 |
| 测试 | review：`--unsafe-fixes` 断言过宽、gates 新措辞与 §4.2 那一行无断言 → 收紧并新增 `test_workflow_gates_fix_only_problems_this_change_introduced` |
| 变更卫生 | review：测试文件空行 → 改正 |

材料缺口经自查：测试中没有「直到通过」的旧断言；`workflow-gates-spec.md.tmpl` 不含 ruff 或「红线」措辞；三条 MODIFIED requirement 与主规格逐条比对，原有 scenario 全部保留。

第二轮：block 0，review 5。按规则修完后只跑 ruff 与测试，不审第三轮：

- tasks 1.1 的描述缺第三类问题、验证写法与测试不符 → 补上，验证改为「grep 无结果」。
- design Goals「基线完全写在配置里」 → 改为「豁免全部写在项目的 ruff 配置里；自动修复只动用户确认的文件」。
- skill §4.2 第 4 步对已接入项目的旧写法找不到那一行 → 补「旧写法「红线规则：…」一行同理」。
- gates 测试放错节 → 移到「3. 共享 workflow-gates」下。
- design 行数表漏了 `tests/test_templates.py` → 见下方对照表。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：491 passed（改动前 489；新增 2 条，改写 3 条断言以匹配新措辞）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案。

## 6. 额外步骤

改了 `rules/`，在项目甲、乙、丙用本分支开发版运行 `rulemason update --dry-run`：三个项目都只列出 `.rulemason/rules/workflow-gates.md`、rulemason skill 副本与 `.rulemason.yaml`，不碰 AGENTS.md 与项目其他文件，符合任务 4.2 的预期。

## 7. 问题报告场景复现（任务 4.1）

照问题报告搭的临时项目：`backend/` 下 FastAPI 路由（`Depends` / `Query` / `Header`）、Typer 命令行入口、`scripts/` 下的 `print`、未排序的 import、未用导入、裸 `except`、可变默认值；`rulemason init` 后按新 skill 走一遍基线（ruff 0.17.3）。

- 统计（确认前，工作区无改动）：F401 4、T201 3、B008 2（均为 `Depends`）、I001 2、E722 1、B006 1，共 13。
- 自动修复 `--select I001,F401 --extend-exclude __init__.py --force-exclude`：`--diff` 列出 `app/api/routes.py`、`scripts/seed.py` 两个文件；`--fix` 修 5 处（F401 3、I001 2）。命令行点名 `app/__init__.py` 时也被排除。
- 写入 `extend-immutable-calls`（FastAPI 与 Typer 两组）与 `"scripts/**"`、`"app/cli.py"` 的 T201 豁免。
- 重跑后剩余按文件写为「接入前遗留」：`app/__init__.py` F401；`app/api/routes.py` B006、E722。
- 结果：13 → 0，`ruff check .` 通过；`per-file-ignores` 只有脚本与命令行入口、接入前遗留两类；没有 `# noqa`。init 留下的占位注释行也在这时发现，skill 已补「一并删去」。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `rules/workflow-gates.md` | ±8 | +3 / −3 | 改的是三行长句 |
| `skills/rulemason/SKILL.md` | +30 | +34 / −5 | |
| `src/rulemason/templates/AGENTS.md.tmpl` | ±1 | +1 / −1 | |
| `tests/test_init.py` | ±1 | +1 / −1 | |
| `tests/test_templates.py` | 未列 | +25 / −2 | design 漏列；新增 skill 基线一节与 gates 新措辞两条测试 |
| `README.md`、`README.en.md` | +2 | +4 | 每份一段，段前空行各一行 |

## 偏差与发现

- 实测 ruff 0.17.3 对 `Query`、`Header`、`typer.Option` 等不报 B008，只报 `Depends`；`extend-immutable-calls` 仍按 design 列全两组函数，计划里写明 B008 实际落在哪些函数上。
- init 写的项目 ruff 配置里有 `〈脚本目录〉` 占位注释，写入真实条目时 skill 要求一并删去（不在 tasks 内，属于同一步骤的细节）。
- 已接入项目命令表之后仍是旧写法「红线规则：暂无。」：检查点的新定义同时覆盖新旧写法，巡检时提一句、不强制；启用判断时旧写法那一行同样改为列出规则 id。
- 发布说明要写：检查点里 ruff 一步从「修到通过」改为「只修本次引入的问题」；老项目接入后先运行 `/rulemason` 建立基线。
