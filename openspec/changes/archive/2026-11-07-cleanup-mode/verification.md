# Verification：cleanup-mode

## 写代码前

- `rulemason judge --change cleanup-mode`：pass 3 / review 0 / block 0。

## 改了什么

- `skills/rulemason/SKILL.md` 第 1 节加一句：用户要做存量清理时，`next.code` 只作第 7 节的入口闸门。
- 第 7 节：入口四停四续；不带模块名只诊断、不改文件；三层诊断；查重钉 `jscpd@5.4.2` 与 `pylint@4.1.3`，跑不起来就空出该列；jscpd 输出放仓库外并删掉；ruff 用 `--output-format json` 再按模块计数；只读代理最多 5 个，改文件最多 3 个；进度不写入 `.rulemason/`；六步保留；提交说明 `refactor(cleanup): <模块>` 由用户写。第 7 节 24 行，上限 70。
- `tests/test_templates.py`：原有短语都还在，补了新措辞，行数上限从 30 改为 70。

## 收尾检查点

1. **自动精简**：skill 是文档。测试只加断言，手工看过，都在原有的循环里，没有再抽的重复。没有会改变断言含义的精简。
2. **独立审查**（只读一份材料文件的子代理，两轮）：
   - 第一轮 block 0 / review 6，均已修：两处自然语言统一成「说要做存量清理」；查重在没有工具、离线、下载失败或命令失败时都空出该列；ruff 改为带路径的 JSON 再按模块计数；jscpd 输出放仓库外并删掉；测试改为断言停下与继续的完整名单，并断言「不带模块名时只输出诊断」。
   - 第二轮 block 0 / review 2，按规则修复后不审第三轮：`--statistics` 没有路径，改成 `--output-format json`；写明提交由用户做；测试补上「说要做存量清理」「离线」「下载失败」「由用户提交」。
3. **ruff**：`uv run ruff check .` 通过。
4. **测试**：`uv run pytest` 641 passed。
5. 前端 lint、文案检查：本仓库无前端、无界面文案，跳过。判断回归：命令表没有这一行，跳过。
6. **额外步骤**（改了 skill，在接入项目验证）：三个已接入项目跑了开发版 `rulemason update --dry-run`，前后工作区改动数不变，未提交也未推送。
   - 只用一个工具、没有前端的项目：`.rulemason/rules/code-style.md`、`.claude/skills/rulemason/SKILL.md`、`.rulemason.yaml`。
   - 两个有前端、两个工具都接入的项目：另有 `.rulemason/rules/react.md` 和 `.agents/skills/rulemason/SKILL.md`。
   - 另一个目录是本仓库旧名的 clone，命令提示它直接引用 `rules/`，不需要 update。
   - 计划里的 `rules/` 文件不是本 change 改的。这些项目还没更新到 0.8.25，开发版对照的是已发布的规则正文。本 change 只改 skill。

## 改既有测试的断言

- `test_skill_legacy_cleanup_section`：行数上限 `<= 30` 改为 `<= 70`。第 7 节从约 11 行写成 24 行，原上限装不下。原有短语（六步标题、共用模块、worktree、不提交等）仍在同一条断言里，没有删、没有放宽。

## 与 design 估计行数对照

| 文件 | 估计 | 实际 |
|---|---|---|
| `skills/rulemason/SKILL.md` | +45 / −10 | +19 / −3 |
| `tests/test_templates.py` | +16 / −2 | +11 / −2 |

两处都低于估计。第 7 节写成 24 行，没有用到 70 行上限。
