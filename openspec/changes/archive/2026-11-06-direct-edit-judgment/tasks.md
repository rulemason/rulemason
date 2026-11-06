# Tasks

## 1. 判断引擎

- [x] 1.1 `judge.py`：产物类型加 `direct`；新增 `lint_direct`（四段标题缺任一段即 block）与 `run_direct`；`main` 加 `--direct <文件>`，与 `--lint-only`、`--dry-run` 搭配可用；验证：`tests/judge/test_engine.py` 覆盖缺段 block 且不调模型、四段齐全时只选 `target: direct` 的规则、`--lint-only` 不需要 key，`uv run pytest tests/judge` 通过
- [x] 1.2 `base/judgments.yaml` 新增 `direct-route-respects-specs`（`target: direct`，block 0，注释写明来由与收紧条件）；验证：通用规则相关测试更新为三条，`--change` 时仍只有原来两条参与，`uv run pytest tests/judge` 通过

## 2. 检查点、skill 与文档

- [x] 2.1 `rules/workflow-gates.md`「不走 OpenSpec 改代码时」：第 2 步加「先走 OpenSpec 的区域」一条；第 3 步加直接改动说明交判断（四段、不贴代码、仓库外临时文件、block 按冲突、review 列出、只在判断启用且改了代码逻辑时）；第 4 步编号不变；验证：`tests/test_templates.py` 断言关键措辞与编号，`uv run pytest tests/test_templates.py` 通过
- [x] 2.2 `skills/rulemason/SKILL.md`：第 2 节补「先走 OpenSpec 的区域」候选与写法；第 3 节巡检没有这一行时提一句；4.2 节逐条问红线规则是否也判直接改动并写 `target: direct` 规则；验证：`tests/test_templates.py` 断言关键措辞，通过
- [x] 2.3 `README.md`「判断（可选）」一节补直接改动说明的用法与「先只 review」；验证：通读，没有本机路径与私人项目名
- [x] 2.4 把「判断只审 OpenSpec 方案与界面文案」改为「判断审 OpenSpec 方案、界面文案与直接改动的说明」：`init.py` 的结尾提示、检查点「归档」第 5 步、skill 第 2 节与第 3 节；接入后没起过 change 的说明改为「方案与文案的判断暂时用不上，直接改动的判断仍会用到」；三份规格增量加 MODIFIED；验证：`grep -rn "只审 OpenSpec" src rules skills README.md tests` 无结果，`tests/test_init.py` 与 `tests/test_templates.py` 断言新说法，通过

## 3. 验证

- [x] 3.1 在本仓库用缺段与完整的两份样例说明跑 `rulemason judge --direct … --lint-only`；在一个已启用判断的接入项目里跑 `--dry-run`，看请求体只含说明文字、规则只有 `target: direct` 的（只读，不发送）；验证：结果写进 `verification.md`
- [x] 3.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
