## Why

`rulemason remove` 卸载后，`CLAUDE.md` 只剩一行 `@AGENTS.md`，让 Claude Code 仍能读到项目指令（`src/rulemason/remove.py:154` 的 `keep_agents_import`）。之后重新 `rulemason init`，新写入的 `rulemason:claude` 块里也有 `@AGENTS.md`，init 于是报「CLAUDE.md 在 rulemason:claude 块外已有 @AGENTS.md，与块内重复导入：请删去块外那一行」（`src/rulemason/init.py:153`），要用户手动删 remove 自己留下的那一行。卸载再接入应当一条命令接好，不留手工活。

## What Changes

- `init` 与 `update` 补 `CLAUDE.md` 的 `rulemason:claude` 块时，若文件里还没有这个块，且 `@AGENTS.md` 在全文只出现一次、顶格独占一行、不在代码块里，就用新块替换这一行（块放在原来那一行的位置，块内第一行就是 `@AGENTS.md`），作为一条「修改」进计划；不再报重复导入。
- 块外的导入写成别的形式（如 `@./AGENTS.md`、缩进、与其他文字同一行）时，那些行不改，报重复导入，由用户处理；提示改为「块外已导入 AGENTS.md」，`@./AGENTS.md` 也能报出（原来按子串判断会漏报）。
- 不做：改 `remove` 的行为（卸载后留 `@AGENTS.md` 是对的）；处理 `CLAUDE.md` 里其他重复导入（如重复导入共享规则副本）；改 `check` 的判断。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：「init 可重复运行，冲突只报告」补一条例外：块外单独一行的 `@AGENTS.md` 由新块接替，不算冲突。

## Impact

- 代码：`src/rulemason/init.py` 的 `set_block`（没有标题的块先找独占一行的正文首行，就地替换）与 `plan_blocks` 的重复导入提示（约 +25 行）；`tests/test_init.py`、`tests/test_update.py` 补卸载再接入、换行保留、其他写法仍报告等用例。
- 接入项目：只影响运行过 `remove` 后再接入、或自己在 `CLAUDE.md` 写了单独一行 `@AGENTS.md` 的项目；结果是少一条「需要你处理」。
