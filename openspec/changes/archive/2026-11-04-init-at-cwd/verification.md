# Verification：init-at-cwd

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。

## 写代码前检查点

`rulemason judge --change init-at-cwd`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简（`/simplify`，四路并行）**，只采纳行为保持的修改：

- 采纳：新增 `outer_repo`，check 与 `repo_root_hint` 共用「未接入且在仓库子目录里」的判断；`find_root` 用 `repo_root` 作边界、单一返回点；仓库根提示从 `build_plan` 挪到 `init.run`，只在项目根就是当前目录时加（在仓库根运行 `rulemason init app` 不再说「当前目录在 git 仓库……」）；update 一步写法；删一条重复断言；补「显式路径不提示」「未接入子目录运行 remove」两个用例。
- 跳过：测试里的提示原文改为由函数生成（有意锁定输出文字）；三个用例的准备代码抽 fixture（各 3 行，收益小）；check 里先判断清单再找仓库根（性能类，不采纳）。
- 修复深度方向：找项目根的决定只在 cli 与 judge 两处，二者故意不同，合适。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：block 1，review 12，全部处理：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | block：规格要求 check 也写「接入整个仓库的做法」，实现只写仓库根 → 按 design 改规格与 proposal：init 与 update 写做法，check 识别表写仓库根。review：规格丢了「check 与 update 写明判断出的项目根」→ 补回；提示条件没限定「找不到清单」→ 补上；judge-engine 主规格写「与 init 等相同的规则」→ 新增 judge-engine 增量只改措辞；工作区场景测试缺提示断言 → 补 |
| 正确性 | review：`init.run` 自己读 `Path.cwd()` → 改由 cli 传 `at_cwd`；提示出现在代跑 openspec 的提问之后 → 两者都在当前目录，写进 design Risks |
| 安全 | pass |
| 代码质量 | review：check 一行做两件事、`--json` 里「项目根」不再是纯路径 → 「项目根」保持纯路径，另起一行「所在 git 仓库根」；design 决策 3 改写 |
| 测试 | review：judge 缺用例 → 新增「没有清单时 judge 用仓库根」；remove 断言过宽 → 断言退出码 1；准备代码重复 → 未抽 fixture（理由同上） |
| 变更卫生 | review：README.en 少 `rulemason init <repo-root>`、弯引号 → 补上、改直引号；shared.py 行数超估计 → 见下表 |

第二轮：block 0，review 4。按规则修完后只跑 ruff 与测试，不审第三轮：

- design Risks 与新增的 judge-engine 增量矛盾、行数表漏三项、proposal Impact 漏 `cli.py` 与 `judge.py` → 同步。
- 规格没写「显式给出别的路径时不提示」→ 条件补「项目根就是当前目录（没有显式给出别的路径）」，「显式给出路径」场景补「不提示」。
- judge 用例的前提只在夹具里 → 用例里断言当前目录是 `api/`、没有清单。
- tasks 3.1 的描述与 README 实际改动不符 → 改写。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：523 passed（改动前 514）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案。

## 6. 额外步骤

未改 `rules/`、`lint/` 或 skill，额外步骤不适用；仍在项目甲、乙、丙的根目录与一个子目录各运行开发版与 0.8.14 的 `rulemason check`，输出完全相同（都已接入，找到清单的路径不变）。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/shared.py` | +12 / −4 | +26 / −7 | 超出一倍：精简与审查后新增 `outer_repo`、`repo_root_hint`，让「未接入且在仓库子目录里」的判断只写一处 |
| `src/rulemason/cli.py` | +3 / −2 | +5 / −3 | 多出 `at_cwd` 传参 |
| `src/rulemason/judge/judge.py` | +3 / −2 | +12 / −3 | 超出一倍：import 换行与 docstring 写明为何不同于 init |
| `src/rulemason/init.py` | +8 | +7 / −2 | |
| `src/rulemason/check.py` | +5 / −1 | +4 | |
| `src/rulemason/update.py` | +4 / −1 | +3 | |
| `README.md`、`README.en.md` | +2 / −2 | +4 / −2 | |
| `tests/test_shared.py` | +15 / −6 | +14 / −6 | |
| `tests/test_init.py` | +30 / −5 | +48 / −3 | 审查后补「显式路径不提示」「已接入不提示」与工作区提示断言 |
| `tests/test_check.py`、`tests/test_update.py` | +20 | +26 | |
| `tests/test_remove.py` | +8 | +9 | |
| `tests/judge/test_engine.py` | +6 | +7 / −1 | |

## 偏差与发现

- **judge-engine 规格也要改**：原以为只改 rulekit-cli，审查发现 judge-engine 主规格写着「与 init、update、check 相同的规则」，本 change 新增它的增量，只改措辞、行为不变。
- **check 的写法**：design 原写「在项目根一行里补仓库根」，审查后改为另起一行，`--json` 里「项目根」的值保持纯路径。
- **提示时机**：交互运行时代跑 openspec 的提问先于计划，用户先看到提问才看到仓库根提示；两者都写在当前目录，不会再写到别处，未改流程。
- **发布说明要写**：找不到 `.rulemason.yaml` 时在当前目录接入，与 openspec init 一致；monorepo 要接入整个仓库，到仓库根运行或 `rulemason init <仓库根>`。
