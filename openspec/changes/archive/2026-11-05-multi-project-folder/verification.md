# Verification

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前判断 `rulemason judge --change multi-project-folder` | pass 3 / review 0 / block 0 |
| 1. 自动精简（`/simplify`，四个方向） | 采纳：三处重复的「放项目的文件夹」测试布置抽成 `tests/conftest.py` 的 `project_folder`；参数化测试去掉 if 分支，改成参数化数据；删掉与共享单测重复的 init 用例；`"第三方目录"` 抽成常量 `THIRD_PARTY`，与另外两种原因一致；修正一处空行；恢复误改了对齐的 `PLAN_DIR` 一行。撤回 / 不采纳：效率审查的 3 条与简化审查的「names 集合建两次」1 条，都是性能类修改（按 CLAUDE.md 不采纳）；altitude 审查无发现 |
| 1. 独立审查第 1 轮 | block 0，review 3：①`folder_hint` 签名与 design 不一致 → 保留 `folder_hint(scanned)`（不加没有调用方的参数），design 与 tasks 文字已改一致；②提示里子项目名不截断 → 已修，抽出 `shared.shown_list`，识别表「跳过」一行与提示共用（多于 10 个写「等共 N 个」），加测试；③init `--plan --json` 不带提示 → 不改：现有 JSON 本来就不含任何 tips（仓库根提示也不在），加进去要改 JSON 结构，超出本 change。材料缺口「`build_plan` 还有没有别的调用方」：grep 确认只有 `init.run` 一处 |
| 1. 独立审查第 2 轮 | block 0，review 3：①tasks.md 签名文字 → 已改；②`--json` 里「提示」是否与「没有 git」同键 → 核实不同键：「没有 git」由 `check.render` 单独追加，不在 `facts`，无需改；③截断时文案「等共 12 个 是独立项目」多一个空格 → 句式改为「这里有独立项目 …；如果这里只是放项目的文件夹……」。第 2 轮只剩 review，修完跑 ruff 与测试，不再审第 3 轮 |
| 2. `uv run ruff check .` | All checks passed（修过一次本次引入的 I001：`tests/test_init.py` 的 conftest 导入超长后需换行） |
| 3. `uv run pytest` | 568 passed |
| 3. 判断回归 | 命令表没有这一行，跳过；本次也没改判断规则文件或 `JEV_MODEL` |
| 4. 前端 lint | 无前端，跳过 |
| 5. 文案检查 | 无界面文案，跳过 |
| 6. 额外步骤（改了 `rules/`，在接入项目验证） | 见下文 3.2；不提交、不推送 |

## 3.1 文件夹布局实测（scratchpad）

布局：`A/` 不是 git，下面 `b/`、`c/` 各是 git 仓库，有 `pyproject.toml` 与 `src/m.py`、没有 `uv.lock`。

- 在 `A/` 运行 `rulemason init --tools claude --plan`（b、c 尚未接入）：计划的「提示」里有一行写明 b、c，建议到各项目里分别接入；要写的文件仍是 7 个（规则副本、skill、入口与清单）。
- b、c、A 都接入后，在 `A/` 运行 `rulemason check`：第一行仍是「补项目信息：在 AI 工具中运行 /rulemason」，退出码 0；识别表在「跳过：b（另一个仓库）、c（另一个仓库）」后多一行「提示：这里有独立项目 b、c；如果这里只是放项目的文件夹，建议到各项目里分别运行 rulemason init；同时改几个项目时，在主要改的项目里打开 AI 工具，再挂上相关项目（如 --add-dir）」；`--json` 的 `facts` 带「提示」。
- 在 `A/` 用 Claude Code 非交互运行（`claude -p`，只放行读写文件、`uvx ruff check` 与只读 git 命令），任务是「在 b/src/m.py 加 add 函数，按项目规矩做完，汇报跑了哪些检查、用的哪个项目的命令表」。AI 引用新加的那句「本项目指被改文件往上最近的 `.rulemason.yaml` 所在目录」，取 `b/AGENTS.md` 的命令表（明确说没有用 A 的「无，跳过」），在 `b/` 根目录改动前后各跑一次 `uvx ruff check .`（都通过）；测试一行因 b 的命令表写「待确认」而跳过并说明。只跑了一次、没有对照组（不加这句时的行为），属于单次观察。这次实测用的是改句式之前的提示文字，提示文字不影响这个观察。

## 3.2 已接入项目运行 update

在一个工作区干净的已接入项目（0.8.17）用本仓库源码运行 `rulemason update --dry-run`，再运行 `rulemason update --yes`：

- 计划与结果都只有 `.rulemason/rules/workflow-gates.md`、`.rulemason.yaml` 两个文件；diff 为副本里那一句，以及清单中这份副本的校验值。
- `rulemason check` 第一行「日常巡检：一切一致」，退出码 0；巡检里「React 目录缺少 ESLint」一条是该项目原有的，与本次无关。
- 验证后用 `git checkout --` 还原这两个文件，项目回到干净状态；没有提交、没有推送。

## 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/shared.py` | +18 | +36 / −4 | 正好是估计的两倍：独立审查第 1 轮要求截断，多了 `shown_list` 与 `SHOWN_DIRS`；精简时多了 `THIRD_PARTY` 等三个常量 |
| `src/rulemason/check.py` | +4 / −2 | +10 / −12 | 新增超出一倍：三个导入各占一行；`has_python` 移走（−4）、`skipped_label` 改用 `shown_list`、`SHOWN_SKIPPED` 移到 shared。净减 2 行 |
| `src/rulemason/init.py` | +4 / −1 | +7 / −2 | 在范围内 |
| `rules/workflow-gates.md` | +1 / −1 | +1 / −1 | 一致 |
| `README.md` | +12 | +11 | 一致 |
| `tests/test_shared.py` | +30 | +29 / −1 | 一致 |
| `tests/test_init.py` | +25 | +28 / −1 | 一致（导入换行占了几行） |
| `tests/test_check.py` | +30 | +18 | 少于估计：布置抽到 conftest |
| `tests/conftest.py` | — | +8 | 未估计：精简时抽出的 `project_folder` |

## 偏离与说明

- `folder_hint` 签名为 `folder_hint(scanned)`，不带 `root`（实现用不到）；design 与 tasks 的文字已同步。
- design 决策 4 给的提示文字示例按第 2 轮审查改了句式，design 已同步。
- README 只改了中文版；英文简版 `README.en.md` 只有一行 monorepo 说明，没有展开接入细节，本次不加。
