# Tasks

## 1. 命令行

- [x] 1.1 `check.identify` 识别表加「接入后归档 change」（用 `dated_archives` 与同一个接入日期；推算不出写「—」）；验证：`tests/test_check.py` 覆盖规格增量两个场景，`--json` 的 `facts` 带同名键，`uv run pytest tests/test_check.py` 通过
- [x] 1.2 `init.guide_key`：已有 key、条件满足、未启用时输出一行启用说明（含覆盖范围），不提问；已启用或条件未满足时行为不变；验证：`tests/test_init.py` 覆盖「已有 key、条件满足、未启用」与「已启用」，原有三个场景不变，`uv run pytest tests/test_init.py` 通过

## 2. 检查点、skill 与文档

- [x] 2.1 `rules/workflow-gates.md`「归档」第 5 步改为「判断条件满足且未启用，已归档正好 3 或接入后归档正好 1 时提示一次」，有无 key 分两种说法，都附覆盖范围；验证：`tests/test_templates.py` 断言新条件与两种说法，`uv run pytest tests/test_templates.py` 通过
- [x] 2.2 `skills/rulemason/SKILL.md` 第 2 节补完时问一次（附覆盖范围；接入后没起过 change 时照实说明）；第 3 节巡检「说明启用条件」一句补上覆盖范围；验证：`tests/test_templates.py` 断言关键措辞，通过
- [x] 2.3 `README.md`「判断（可选）」一节写明配 key 不等于启用、判断只审方案与文案；验证：通读，没有本机路径与私人项目名

## 3. 验证

- [x] 3.1 在一个已接入、有 key、未启用判断的项目上运行 `rulemason check`（只读），看识别表的「接入后归档 change」与「判断」两行；验证：结果写进 `verification.md`
- [x] 3.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
