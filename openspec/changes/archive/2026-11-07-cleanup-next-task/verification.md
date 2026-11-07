# 完成汇报

1. **写代码前的判断**：`rulemason judge --change cleanup-next-task`，pass 3 / review 0 / block 0。没有 block，继续。
2. **自动精简**：无代码改动，跳过精简。skill 是文档；测试只在既有断言循环里加子串。
3. **独立审查**：两轮，审查者只看材料、不读仓库。
   - 第一轮 review 2、无 block。补上「也不是用户确认」，测试加上「不写入文件」「具体改哪些等进入该模块后的计划」「这两种都不写这次要做的事」。
   - 第二轮 review 2、无 block。收尾的那句改成「哪一类软指标不算这次要清的内容」。没有下一个模块时只写「这次没有要做的模块」，不写「具体改哪些」。按两轮上限，没有开第三轮。
4. **ruff**：`uv run ruff check .` 通过。
5. **测试**：`uv run pytest`，641 passed。判断回归：没有改判断规则或 `JEV_MODEL`，跳过。改了既有测试 `test_skill_legacy_cleanup_section`：只加等价子串断言，没有删、没有放宽。新增子串包括「这次要做的事」「不算这次要清的内容」「同一次诊断」「不写入文件」「也不是用户确认」「具体改哪些等进入该模块后的计划」「这两种都不写这次要做的事」「哪一类软指标不算这次要清的内容」「不写具体改哪些」。
6. **前端 lint / 文案检查**：无前端、无界面文案，跳过。
7. **额外步骤**（改了 skill，在接入项目验证）：四个目录跑了开发版 `rulemason update --dry-run`，前后工作区改动数不变，未提交也未推送。
   - 两个项目只列出所选工具的 skill 副本和 `.rulemason.yaml`。
   - 一个项目还列出 `.rulemason/rules/code-style.md`。这是尚未吃进已发布的规矩文件，不是本 change 改的。本 change 只改 skill。
   - 一个旧名克隆退出码 1，提示它直接引用 `rules/`，不需要 `rulemason update`。

## 估计行数

| 文件 | 估计 | 实际 |
|---|---|---|
| `skills/rulemason/SKILL.md` | +6 / −2 | +2 / −2 |
| `tests/test_templates.py` | +6 / −0 | +4 / −0 |

新句子写进原有段落，第 7 节仍是 26 行，上限 70。没有超出一倍。
