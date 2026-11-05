# Tasks

## 1. 文件夹提示

- [x] 1.1 `shared.py` 新增共享的语言判断与 `folder_hint(scanned)`，`check.identify` 的语言判断改用共享函数；验证：`tests/test_shared.py` 覆盖「无语言 + 另一个仓库」「无语言 + 另一个 rulemason 项目」出提示，「有 Python + 子仓库」「无语言 + 只有第三方目录」不出，`uv run pytest tests/test_shared.py tests/test_check.py` 通过
- [x] 1.2 `init.build_plan` 改用 `scan`，有提示时追加到 `plan.tips`；验证：`tests/test_init.py` 新增文件夹布局下 `init --plan` 的「提示」含子项目名，且要写的文件与去掉子仓库后的布局相同，`uv run pytest tests/test_init.py tests/test_update.py` 通过
- [x] 1.3 `check` 识别表在「跳过」之后加「提示」；验证：`tests/test_check.py` 覆盖文件夹布局出现提示、退出码与第一行不变、`--json` 的 `facts` 带「提示」，有代码的项目带子模块时不出现，`uv run pytest tests/test_check.py` 通过

## 2. 共享正文与文档

- [x] 2.1 `rules/workflow-gates.md` 第 5 行那一段末尾加「本项目」的定义与跨项目时各跑一遍的一句；验证：`git diff rules/workflow-gates.md` 只有这一处，`uv run pytest tests/test_templates.py` 通过
- [x] 2.2 `README.md`「第一次接入」之后加「多个项目放在同一文件夹」一小节（各项目分别接入、`--add-dir`、`CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`）；验证：通读一遍，没有本机路径与私人项目名，pre-commit 钩子通过

## 3. 验证

- [x] 3.1 在 scratchpad 搭 `A/`（非 git）下 `b/ c/` 两个 git 仓库的布局，跑 `init --plan` 与 `check` 看提示；在已接入的 `A/` 用 Claude Code 改 `b/` 的文件，看 AI 是否按 `b/` 的命令表跑 ruff；验证：输出与观察写进 `verification.md`
- [x] 3.2 在一个已接入项目运行 `rulemason update`（不提交、不推送）；验证：副本只多这一句，`rulemason check` 一致，结果写进 `verification.md`
- [x] 3.3 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
