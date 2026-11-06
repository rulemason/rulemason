# Verification

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前判断 `rulemason judge --change direct-edit-judgment` | pass 3 / review 0 / block 0 |
| 1. 自动精简 | `run_direct` 与 `run_change` 里「问裁判、逐条判定、报告」是同一段，已抽成 `ask_and_report`，两处共用；其余新增代码没有可精简处，未调用 `/simplify` 的四路审查 |
| 1. 独立审查第 1 轮 | block 0，review 若干，全部处理：①block 阈值 0 时 p 恰好为 0 的行为——`verdict` 里是 `p < block`，补测试确认只给 review；②说明文件不是 UTF-8 时会崩（`ValueError` 没人接）——转成带路径的 `ConfigError`，文件不存在的 `OSError` 由命令行最外层接住；③只有标题没有正文的段落也算通过——改为每段必须非空；④通用规则注释里带了具体业务词（路由、审计、管理端）——改成抽象描述，并写明 `enforces` 选 `L0/Code style` 的原因；⑤补测试：文件不存在、非 UTF-8、空段落、`--direct --dry-run` 只发说明、`--direct` 搭配 `--change` 结果叠加 |
| 1. 独立审查第 2 轮 | block 0，pass；仅提示测试文件有几处多余空行，已整理。不需要第 3 轮 |
| 2. `uv run ruff check .` | All checks passed |
| 3. `uv run pytest` | 629 passed |
| 3. 判断回归 | 命令表没有这一行，跳过；本次没改 `JEV_MODEL`，但新增了一条通用判断规则，没有真实样本可回归，所以阈值取 0 只 review |
| 4. 前端 lint | 无前端，跳过 |
| 5. 文案检查 | 无界面文案，跳过 |
| 6. 额外步骤（改了 `rules/`） | 见下文 3.1；不提交、不推送 |

## 3.1 实测

- 本仓库，`rulemason judge --direct <说明> --lint-only`：缺段的说明报两条 `lint/direct` block、退出码 1；四段齐全的说明 pass、退出码 0，不需要 key。
- 在一个已启用判断的接入项目里 `--dry-run`（只读，不发送）：请求体里 `state` 是说明全文，`questions` 只有通用规则 `direct-route-respects-specs`（该项目没有 `target: direct` 的规则），没有任何源码或其他项目文件，结果为 review 待人工。
- 引擎四段标题与检查点正文里的四个二级标题一致（脚本核对，并有测试断言）。

## 一处设计问题与处理

新增的通用规则最初写 `enforces: L0/Workflow gates`，结果临时项目的指令文件里只有 `## Code style`，引擎的 `load_rules` 找不到这个标题就整个退出，19 个测试失败。这等于让所有没有这个标题的项目的判断都崩。改为 `L0/Code style`（另一条通用规则也用它，所有接入项目都有），并在规则注释里写明原因。

## 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/judge/judge.py` | +45 / −3 | +51 / −7 | 一致 |
| `src/rulemason/judge/base/judgments.yaml` | +10 | +11 | 一致 |
| `rules/workflow-gates.md` | +3 / −1 | +2 / −2 | 一致（把两条新说明写进已有的两条里，没有新增行） |
| `skills/rulemason/SKILL.md` | +12 / −1 | +4 / −1 | 少于估计：三处补充各写成一段 |
| `README.md` | +4 | +4 / −1 | 一致 |
| `tests/judge/test_engine.py`、`tests/test_templates.py` | +70 | +132 / −2 | 在一倍以内：审查后补了边界与错误处理的测试 |

## 覆盖范围的说法一并改掉（原留给用户决定，用户选择一起改）

前一个 change（judge-onboarding-hints）写进 `init` 提示、归档后提示、skill 补项目信息的问一次、日常巡检与 README 的那句「判断只审 OpenSpec 方案与界面文案」，在本 change 之后不再准确：判断现在还审直接改动说明。这几处的说法被主规格（`rulekit-cli`、`workflow-gates`、`rules-layer-setup`）锁定，改它们需要本 change 再加规格增量，超出了原来的范围，用户选择与本 change 一起改，已完成：新增三份 MODIFIED 规格增量（`rulekit-cli`「init 结尾引导配置 key」、`workflow-gates`「归档后提示一次启用判断」、`rules-layer-setup`「阶段一接入代码规矩与 gates」）；`init.py`、检查点第 5 步、skill 第 2 节与第 3 节、对应测试改为「判断审 OpenSpec 方案、界面文案与直接改动的说明」；接入后没起过 change 时的说明改为「方案与文案的判断暂时用不上，直接改动的判断仍会用到」；`grep -rn "只审 OpenSpec" src rules skills README.md tests` 无结果。
