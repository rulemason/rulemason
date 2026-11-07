# Verification：code-style-redundancy

## 写代码前

- `rulemason judge --change code-style-redundancy`：pass 3 / review 0 / block 0（本仓库无项目规则，只跑通用规则）。

## 改了什么

- `rules/code-style.md` 第 8 条末尾补：不为上游已保证的条件再加判断或包 `try`，是否保证以调用链里看得到的校验或类型声明为准，看不出时不删检查、按第 3 条写注释。
- `rules/code-style.md` 第 9 条：不加、不留没有调用方的函数和文件；只有一个调用方、自身不带逻辑的抽象层直接内联；带自己逻辑的辅助函数不算。九条仍是 9 条。
- `rules/react.md` 第 9 条补：只有一处使用、只转发 props 的包装组件直接内联。
- `tests/test_templates.py`：补三处措辞断言，抽出 `_line(text, prefix)`。

## 收尾检查点

1. **自动精简**：规则正文只改文档，不精简。测试代码的改动手工精简：新增断言会让「按前缀取一行」的表达式出现第三次，按第 7 条抽成 `_line`，原有两处一并换用；其余无可精简。
2. **独立审查**（只读一份材料文件的子代理，两轮）：
   - 第一轮 block 0 / review 6，均已修：第 8 条补「以调用链里看得到的校验或类型声明为准」与「看不出保证时不删检查」；第 9 条「不加」改为「不加、不留」，覆盖重构遗留的函数；React 第 9 条补「只有一处使用」；抽出 `_line`；补第 8 条保护条款的断言；`cleanup-mode` 空脚手架不随本 change 提交。
   - 第二轮 block 0 / review 5，按规则修复后不审第三轮：第 8 条「再加检查」改为「再加判断或包 `try`」并加断言；proposal、tasks、规格增量的措辞同步到最终正文；tasks 2.1 不再写「只改文档、跳过精简」，改为测试代码手工精简；提交时只加本 change 的文件。
3. **ruff**：`uv run ruff check .` 通过。
4. **测试**：`uv run pytest` 641 passed。
5. 前端 lint、文案检查：本仓库无前端、无界面文案，跳过。判断回归：命令表没有这一行，跳过。
6. **额外步骤**（改了 `rules/`，在接入项目验证）：在三个已接入项目运行开发版 `rulemason update --dry-run`，前后各项目工作区的改动数不变，未提交也未推送。
   - 不含前端的项目：计划只列 `.rulemason/rules/code-style.md`、`.rulemason.yaml`。
   - 两个含前端的项目：计划只列 `.rulemason/rules/code-style.md`、`.rulemason/rules/react.md`、`.rulemason.yaml`。
   - 另一个目录是本仓库旧名的 clone，命令提示它直接引用 `rules/`，不需要 update。

## 改既有测试的断言

- `test_code_style_external_operations_and_secrets`：`eighth = next(... startswith("8. "))` 改为 `_line(code_style, "8. ")`，等价。断言 `"静默改走另一条路径" in eighth` 保留在新的循环里，并加上新措辞的三个短语，只收紧、不放宽。
- `test_rules_wording_key_sections`：`front = next(... startswith("4. 改了前端时"))` 改为 `_line(gates, "4. 改了前端时")`，等价；后面的断言不变。

## 与 design 估计行数对照

| 文件 | 估计 | 实际 |
|---|---|---|
| `rules/code-style.md` | +2 / −2 | +2 / −2 |
| `rules/react.md` | +1 / −1 | +1 / −1 |
| `tests/test_templates.py` | +8 | +13 / −3 |

测试文件超出估计，但没到一倍：多出的是审查要求补的断言和抽出的 `_line`。
