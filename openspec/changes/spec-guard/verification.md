# spec-guard 验证记录

## 1. 方案与写代码前的判断

- 方案写完：`rulemason judge --change spec-guard` pass 3 / review 0 / block 0。
- 写代码前：pass 3 / block 0。
- apply 中按审查意见修订了规格增量与 design 的划线说法，修订后重跑判断仍是 pass 3 / block 0；`openspec validate spec-guard --strict` 通过。

## 2. 自动精简

本次只改共享正文、入口块模板、本仓库 AGENTS.md / README 与测试，没有代码逻辑：无代码改动，跳过精简。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件，不读仓库、不运行命令。材料包括 change 产物、改后的 `rules/workflow-gates.md` 全文与完整 diff。

第 1 轮：block 1，review 8。安全与测试为 pass。
- block-1（已修）：「改契约」与「冲突」分不开：用户明确要改规格写着的行为时，两条都套得上。
  - 重新划线：「改契约」是用户要的就是改变主规格已写的某条；「冲突」是用户要的是别的事，做法却会顺带破坏主规格已写的某条。
  - 冲突时用户选改规格，就按「改契约」走。
  - 规格增量的冲突场景改为「一键导出全部会跳过确认」；design D2 同步改写。
- review 1–7（已修）：
  - 适用范围改为「本次改动不属于任何进行中的 change」。
  - 没有 openspec 的项目接上第 4 步。
  - apply 第 7 步写明：没有 design 的最小 change 跳过行数对照。
  - 归档失败分两种情况说明：`openspec archive` 失败时什么都未移动；归档成功、校验失败时，主规格已合并。
  - key 提示写明申请地址。
  - MODIFIED requirement 去掉「三个」，无 openspec 入口块补「改代码前读取」。
  - 「没有判断层的项目」一节写明最小 change 同样不执行判断。
- review 8：提交时排除不属于本 change 的 `previews/`。

第 2 轮：第 1 轮处理全部确认到位，没有 block，有 2 条 review，已修复，按规定不再审第 3 轮：
- 「冲突」里用户选换做法后怎么走，补「按新做法重新判路」；第 4 步的触发改为「不起 change 的直接改动」。
- 无 openspec 入口块补「改代码前读取该文件」的断言。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`：432 passed，不联网。
- 判断回归：本次没有改判断规则文件或 `JEV_MODEL`，跳过。
- 前端 lint、文案检查：本仓库没有前端与界面文案，跳过。
- 本仓库 `rulemason check`：「日常巡检：一切一致」。

## 5. 接入项目验证（额外步骤）

在项目甲、乙、丙的临时 detached worktree 里，用本次代码运行 `rulemason update` 再 `check`：

- 三个项目退出码都是 0，第一行都是「日常巡检：一切一致」。
- AGENTS.md 入口块都已刷新为「开始 OpenSpec 方案与实现、归档，以及不走 OpenSpec 改代码之前」。
- `.rulemason/rules/workflow-gates.md` 副本都含「不走 OpenSpec 改代码时」一节。
- 三个项目的主工作区都没有改动。

**Claude Code 实测**：在项目乙的 worktree 里先运行 update，再用 `claude -p` 非交互跑三个不走 OpenSpec 的小改动，三题都是解读后的评价入口。只放行了读写文件、`openspec`、`git status/diff`、`ls`。实测用的正文是第 1 轮修订后的版本，第 2 轮只补了两句措辞。

| 题目 | 期望 | 结果 |
|---|---|---|
| 默认选中 👍、直接提交 | 冲突 | 读了 `feedback` 主规格，判为冲突，指出会破坏「MUST NOT 预选」及相关场景。没改代码，给出换做法、改规格、放弃三个选项 |
| 问句改成「这一卦，准不准？」 | 改契约 | 判为改契约，起了最小 change（proposal、规格增量、tasks，不写 design），`validate --strict` 通过，停下等确认，并追问按钮文字是否跟着改。判断命令因实测未放行而没跑，它如实写明了 |
| 两个按钮间距加大 | 未覆盖 | 读了 `feedback` 与 `visual-design-tokens`，判为未覆盖，只改一行 CSS，汇报写明依据。ruff、测试、前端 lint 因实测未放行而没跑，它如实列出、请用户放行 |

三题都先读了主规格，都判对了路，汇报里也都写明了判断依据。三个 worktree 用完即删，项目乙的主工作区没有改动。

## 6. 与 design 的偏差

- 实测中的冲突题换了一道。原题「把 👎 做小、突出 👍」是用户明确要改规格写着的行为，按新划线属于改契约，所以换成「默认选中 👍 以便快捷提交」：用户要的是快捷提交，做法却会顺带破坏「无预选」，这才是冲突。

## 7. 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 |
|---|---|---|
| `rules/workflow-gates.md` | +40 / −2 | +27 / −4 |
| `src/rulemason/templates/workflow-gates.block.md` | ±1 | ±1 |
| `src/rulemason/templates/workflow-gates-no-openspec.block.md` | ±1 | ±1 |
| `AGENTS.md` | ±1 | ±1 |
| `README.md` | +3 / −1 | ±1 |
| `tests/test_templates.py` | +25 | +34 |
| `tests/test_init.py` | ±2 | ±1 |

都没有超出估计的一倍。
