# 完成汇报：banner-rider-smaller

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐步记录。

## 0. 写代码前的判断

`rulemason judge --change banner-rider-smaller`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简**：跳过。本次 diff 只换 `ICON` 的像素数据、两处注释里的行数和测试常量，没有改代码逻辑；CLAUDE.md 规定 `/simplify` 只在 diff 改了代码逻辑时调用。

**独立审查**：审查者只读一份材料文件，不读仓库、不跑命令。

- 第一轮：block 0 / review 3。
  1. 产物写的兔子尺寸与起点和网格对不上（写 8×11 @ (7, 0)，实际 7×11 @ (8, 0)），「耳尖与马耳齐平」不成立，实际高 2 像素（旧版高 4）→ proposal、design 改准。用户选的是并排预览里的实际图样，构图不动。
  2. tasks 1.1「后 5 行逐字相同」的前提「马独占」不成立：第 1 行含兔脚，无色渲染逐字相同、彩色下颜色不同 → 措辞改准。
  3. 工作区里有另一会话建的 `openspec/changes/drop-rulekit-migration/`，与本次无关 → 不随本次提交。
- 第二轮：block 0 / review 0。审查者按半格规则逐列推了前 5 行，与渲染逐字相同；确认 delta 完整覆盖原 Requirement。

## 2. ruff

`uv run ruff check .`：All checks passed。

## 3. 测试

`uv run pytest`：380 passed。`tests/test_banner.py` 26 passed。没有改判断规则或 `JEV_MODEL`，命令表没有「判断回归」，跳过。

## 4. 前端 lint

无前端，跳过。

## 5. 文案检查

界面文字没有改动，跳过。

## 6. 额外步骤

没有改 `rules/` 或 `lint/`，不需要在接入项目验证。

## 7. 任务 3.1 的核对

- `len(ICON) == 20`，每行 26 列，`_icon_lines(False)` 10 行；无色渲染的后 5 行与改动前的后 5 行逐字相同。
- 伪终端运行 `uv run rulemason`：第 1 到 10 行是图标，第 11 行空，第 12 行起是 RULEMASON 字标。

## 行数对照

| 文件 | design 估计 | 实际（git diff --numstat） |
|---|---|---|
| `src/rulemason/banner.py` | +22 / −24 | +11 / −13 |
| `tests/test_banner.py` | +3 / −3 | +3 / −3 |

`banner.py` 实际比估计少：估计按整块替换 `ICON` 算，git 只计变了的行（网格后 9 行与旧版相同）。没有超出。

## 追加：鼻子居中（归档前）

用户指出鼻子没在两眼正中：眼在第 9、12 列，鼻在第 11 列，偏右半格。眼距改为偶数列差 4（第 9、13 列），鼻子第 11 列正好居中；只动网格第 5 行一个像素（`whwwhww` → `whwwwhw`），design 附录同步。ruff 通过，`tests/test_banner.py` 26 passed，全量 `uv run pytest` 380 passed。
