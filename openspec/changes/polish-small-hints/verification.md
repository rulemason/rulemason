# 验证记录：polish-small-hints

日期：2026-11-05

## 1. 方案后与写代码前的判断

- 方案写完：`rulemason judge --change polish-small-hints` pass 3（proposal-states-non-goals、lint/design、design-no-speculative-extension）/ review 0 / block 0；`openspec validate --strict` valid。
- 写代码前重跑：pass 3 / block 0。
- 第一轮审查后按用户确认改了规格增量（R3、R4，见第 3 节），重跑判断：pass 3 / block 0。

## 2. 自动精简（/simplify）

四个角度（复用、简化、效率、层级）各一个子代理审查。

**采纳 3 条：**

- 报错标记从 `fail_mark()` 改为 `shared.fail(消息)`：返回整句，judge 17 处、key 2 处统一调用，不再各自拼标记。
- OpenCode 那一行由 `shared.skill_hint_lines(tools)` 给出：init 收尾与 check 报告共用，不再在两处各写一遍判断。
- key 与 judge 的旧控制台用例改为直接替换 `shared.legacy_console`。旧控制台的判定条件只在 `test_shared` 测一次。

**未采纳：**

- 把附注挂在 `Next` 上：`--json` 的 `next` 是 `asdict(nxt)`，会多出字段，违反「next 不变」。
- banner 旧用例改写：不在本次 diff 范围。
- 参数化 `inited` fixture：收益小。
- `detect_commands` 改嵌套分支：可选，层级审查认为现状合适。
- 效率角度：无发现。

精简后 design 与 tasks 里的函数名同步改为 `fail()`。

## 3. 独立审查

审查方式：子代理只读一份材料文件，不读其他文件、不运行命令。

### 第一轮：无 block，review 10 条

- **R1**：核对过，只有 `fill_project_info` 一个下一步提到 `/rulemason`，不需改。
- **R2**：design 决策 2 与文件表改为 `untouched_lines` 返回列表的写法。
- **R3**（需改规格，停下问用户后采纳）：上层目录已有 `pyproject.toml` 的目录跳过，避免 uv workspace 成员与示例项目重复出现 `uvx ruff` 行。规格增量、proposal、design 同步，补两条测试。
- **R4**（需改规格，停下问用户后采纳）：有无锁 Python 目录时，测试一行并列「待确认」，混合仓库里 Python 测试不再被悄悄略过。规格增量同步，补混合仓库测试。
- **R5**：`Report.next_notes` 保留。
- **R6**：OpenCode 用例改为断言紧跟在 `NEXT_STEP` 之后；补 `untouched_lines` 单元测试，覆盖摘要与完整清单共用的那一行。
- **R7**：已有用例断言了「其余 2 个」。
- **R8**：`grep -rn "✗" src` 只剩 `shared.fail()` 与注释。
- **R9**：judge-engine 两条 MODIFIED 由脚本从主规格整块截取，只替换一句。
- **R10**：`check --json` 逐个写出键，并有键集合的断言。

### 第二轮：无 block，review 与 nit 若干，均已修

- `fail(f"{exc}")` 改为 `fail(str(exc))`。
- 一行两件事的断言拆开。
- 嵌套用例补 docstring，并断言测试一行为「待确认」。
- 新增平级两个无锁目录的用例：「待确认」只出现一次。
- OpenCode 提示断言恰好出现一次。
- 规格场景里的命令表值用「」包起来。
- design 去掉一个多余空格。

### 第二轮里说明、未改的两处

- **审查材料里「只跑正则」场景出现两次**：截取脚本打印范围时重复打印了最后一个场景。主规格里只有一次（`grep -c` 为 1），增量正确。
- **在 Windows 上跑测试时，断言「✗ …」的用例会因为旧控制台判断而失败**：CI 只在 ubuntu-latest 上跑（`.github/workflows/ci.yml`），本次不加全局替身。将来要在 Windows 上跑测试，需要在 conftest 里固定 `legacy_console`。

两轮后不审第三轮。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`（第二轮修复后全量）：561 passed。
- 没有改判断规则文件与 `JEV_MODEL`，不跑判断回归。

## 5. 前端 lint、文案检查、额外步骤

本仓库没有前端与界面文案 `I18N`，也没有额外步骤，均跳过。

## 6. 端到端

在一个只有 `pyproject.toml` 与 `tests/`、没有 `uv.lock` 的临时项目里运行 `rulemason init --tools opencode,claude --yes`：

- `AGENTS.md` 命令表的 ruff 为 `` `uvx ruff check .` ``，测试为「待确认：填项目跑测试的命令」。
- `check` 第一行为「补项目信息：在 AI 工具中运行 /rulemason」。

报错开头的「×」只在 macOS 上用替身验证过，发版后请在 Windows 旧控制台看一次，例如在非仓库目录运行 `rulemason judge`。

## 7. 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/shared.py` | +12 | +18 | 精简时加了 `skill_hint_lines()` |
| `src/rulemason/banner.py` | +1 / −1 | +12 / −5 | **超出一倍**：改用 `legacy_console` 后 import 行超长，ruff 把它展开成多行（+8）；删去不再用的 `import os` |
| `src/rulemason/judge/judge.py` | ±17 | +18 / −17 | |
| `src/rulemason/key.py` | ±2 | +3 / −2 | |
| `src/rulemason/init.py` | +18 / −4 | +26 / −9 | R3、R4 的跳过与并列 |
| `src/rulemason/check.py` | +4 | +7 / −2 | |
| `tests/test_shared.py` | +20 | +22 | |
| `tests/test_init.py` | +45 | +73 | R3、R4 与第二轮补的用例 |
| `tests/test_check.py` | +25 | +16 | |
| `tests/test_key.py`、`tests/judge/test_engine.py` | +15 | +21 / −3 | |
