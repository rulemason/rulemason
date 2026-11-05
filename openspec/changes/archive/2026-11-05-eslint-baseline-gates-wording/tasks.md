# Tasks

## 1. 共享正文

- [x] 1.1 `lint/eslint-base.mjs` 注释改口径（按文件各自上限、新文件 15、拆分目标下一档以内不卡线、递减时同时看超过 15 的个数）；`rules/react.md` 末段那句随之改；验证：两处文字不再出现「最复杂函数的值」，`grep -rn "最复杂函数" lint rules` 无结果，`uv run pytest tests/test_templates.py` 通过
- [x] 1.2 `rules/react.md` 新小节「重构等价性」六条；验证：`grep -in "antd\|ant design\|mui\|chakra" rules/react.md` 无结果，六条与规格增量一一对应
- [x] 1.3 `rules/workflow-gates.md`：第 1 步加检索句；新小节「改既有测试时」并在「apply 最后一个任务做完」第 3 步与「不走 OpenSpec」第 4 步各引用一句；「提交信息」扩成「提交与推送」；验证：`git diff rules/workflow-gates.md` 只落在这四处，正文里没有 `--only`、`--pathspec-from-file` 这类具体选项，`uv run pytest tests/test_templates.py` 通过
- [x] 1.4 `rules/workflow-gates.md`「apply 最后一个任务做完」第 4 步：前端 lint 只修本次改动引入的问题，既有问题列数量并建议建 ESLint 基线（独立审查第 2 轮发现，用户要求并入本 change）；验证：规格增量 MODIFIED「写完代码后按顺序检查并逐项汇报」带全部原场景与新场景「前端还没建立基线」，`openspec validate --strict` 通过，`uv run pytest tests/test_templates.py` 通过

## 2. skill

- [x] 2.1 `skills/rulemason/SKILL.md` 新增第 6 节「建立 ESLint 基线」（统计 → 计划 → 确认 → 照做，含「已按旧口径设全局上限」的迁移做法），原第 6 节「汇报」顺延为第 7；第 2 节第 6 步与第 3 节巡检里提到 ruff 基线的地方各补 ESLint；验证：第 5、6 两节结构对称（四个步骤名相同），`uv run pytest tests/test_templates.py tests/test_init.py` 通过

## 3. 文档与验证

- [x] 3.1 `README.md`「日常」里建立 ruff 基线那句补上 ESLint；验证：通读一遍，没有本机路径与私人项目名
- [x] 3.2 在一个有前端的接入项目上验证：用 `git worktree add` 在临时目录检出该项目远端最新的接入分支，运行 `rulemason update`，按新节对一个前端目录跑统计、生成按文件条目，并按「已按旧口径设了全局上限」的场景试一次迁移；前端 lint 通过，`rulemason check` 一致；验证：统计数字、写入的条目数与 lint 结果写进 `verification.md`（不写项目名与路径），之后删除临时目录并 `git worktree prune`，不提交、不推送
- [x] 3.3 按 workflow gates 完成：无代码改动跳过精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
