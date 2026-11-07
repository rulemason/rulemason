# 完成汇报

1. **写代码前的判断**：`rulemason judge --change check-unarchived-finished`，pass 3 / review 0 / block 0。没有 block，继续。
2. **自动精简**：看过新增的 `tasks_finished` 与 `unarchived_finished`。判断只在一处，没有可安全合并的重复，保持原样。
3. **独立审查**：两轮，审查者只看材料、不读仓库。
   - 第一轮 review 3、无 block。混合勾选已在 `test_unfinished_change_stays_unlisted`。补了没有 `tasks.md` 的目录，以及接入层已经失败时退出码仍为 1、下一步仍是 `update`。
   - 第二轮 pass，无 block、无 review。
4. **ruff**：`uv run ruff check .` 通过。
5. **测试**：`uv run pytest`，647 passed。判断回归：没有改判断规则或 `JEV_MODEL`，跳过。新增测试，没有改既有断言。
6. **前端 lint / 文案检查**：无前端、无界面文案，跳过。
7. **额外步骤**：没有改 `rules/` 或 `lint/`，跳过接入项目验证。这次改的是已安装命令里的检查，升级本机后生效。

## 估计行数

| 文件 | 估计 | 实际 |
|---|---|---|
| `src/rulemason/check.py` | +35 / −2 | +23 / −1 |
| `tests/test_check.py` | +48 / −0 | +66 / −0 |

测试比估计多 18 行，不到一倍。多出来的是审查要求补上的两种情况：没有 `tasks.md`，以及原有失败不被这次列表改掉。
