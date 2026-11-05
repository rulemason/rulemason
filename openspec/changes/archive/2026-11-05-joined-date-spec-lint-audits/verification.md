# Verification

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前判断 `rulemason judge --change joined-date-spec-lint-audits` | pass 3 / review 0 / block 0 |
| 1. 自动精简（`/simplify`，复用、简化、效率、层级四个方向并行） | **采纳**：`audit` 只算一次「接入之后的归档」，传给 `gate_records`，巡检项名只写一处；`spec_writing` 改用扫描得到的文件列表，会遵守扫描的跳过规则，并用 `_read` 读取；用已有的 `_section` 判断有没有 `## Requirements`；七类问题改成具名常量；嵌套的正则拆成两步；识别表「接入日期」改成 if/else；`joined_text` 去掉一个永远成立的判断；`manifest_text` 一次组装；测试去重（日期替身类合成一个；「推算」测试改为自己造一条已知日期的提交，不再照抄实现里的 git 命令；重复的参数行合并；`set_joined` 移到 conftest，test_update 也用它；去掉多余空行）。**不采纳**：效率类 4 条（按 CLAUDE.md 不采纳性能优化；其中「check 不推算」还会改变规格行为）；「`check_manifest_fields` 只有一个调用方」——抽出来是为了把 `read_manifest` 的 C901 压回上限；「`joined_date` 改成返回元组」——只有两个来源，改了反而要动三处调用 |
| 1. 独立审查第 1 轮 | block 0，review 7，全部修复：①新接入（没有清单）不看 git 历史，直接取当天，以前删过清单的项目重新接入不会拿到旧日期（规格「init 记接入当天」）；②不加引号的非法日期 PyYAML 解析时抛 `ValueError`，`read_manifest` 原来接不住，`check` 会崩，现已转成清单无效；③lint 占位的正则把 `echo a` 换行接 `eslint .` 和 `echo $(…)` 误判为占位，改为 echo 后只允许接空格或制表符，并排除换行、反引号与 `$`；④只有不带日期前缀的归档目录时误写「接入后尚未归档」，改为只看带日期的归档；⑤一行做两件事的拆开，看不出原因的分支补「走到这里说明…」，`identify` 的 docstring 补上接入日期；⑥补测试：日期写坏了、没有 joined 也没有 git、不加引号的非法日期，`_` 改成具名变量；⑦材料缺口——非 UTF-8 的 spec.md 会让 `check` 崩，改为转成带文件名的 `ConfigError`，与 `package.json` 的处理一致。没装 git 的情况是原有的 `has_git` 就会遇到的，不是本次引入，不改 |
| 1. 独立审查第 2 轮 | block 0，review 2：①非 UTF-8 的 spec.md 中断整个 check，和「巡检不影响退出码」有出入——保持 `ConfigError`（读不出文件是配置问题，与 `package.json` 一致），补了测试；②`except` 里的 `UnicodeError` 已被 `ValueError` 覆盖、`identify` 里有一个必然成立的判断，两处都删了。第 2 轮只剩 review，修完跑 ruff 与测试，不再审第 3 轮 |
| 2. `uv run ruff check .` | All checks passed。修过两处本次引入的问题：`read_manifest` 加校验后 C901 超限（抽出 `check_manifest_fields`），以及 import 排序 I001 |
| 3. `uv run pytest` | 607 passed |
| 3. 判断回归 | 命令表没有这一行，跳过；本次也没改判断规则文件或 `JEV_MODEL` |
| 4. 前端 lint | 无前端，跳过 |
| 5. 文案检查 | 无界面文案，跳过 |
| 6. 额外步骤 | 没有改 `rules/` 或 `lint/`；接入项目验证见下文 3.2 |

## 3.2 接入项目验证

在一个已接入项目里，用 `git worktree add --detach` 把已提交的 HEAD 检出到临时目录，只读；用本仓库源码运行：

- 清单第一次提交的日期是 2026-11-02（从旧名迁移过来的那次提交）。
- `update` 前，识别表显示「接入日期：2026-11-02（推算）」；「最近归档的检查点记录」一致；「lint 脚本为占位」一致。
- `rulemason update --yes` 后，清单第 3 行写入 `joined: '2026-11-02'`；识别表不再显示「推算」；`check` 第一行「日常巡检：一切一致」，退出码 0。
- 「主规格写法」报出两类问题：Purpose 是占位，共 16 份（列出前 10 个和总数）；requirement 正文超过 500 字，4 份。与在同一目录运行 `openspec validate --specs --strict --json` 的结果对照：占位同为 16 份，超长同为这 4 个能力，没有其他类型的问题，**完全一致**。
- 收尾时用 `git worktree remove` 删除临时目录，再 `git worktree prune`。原检出的 HEAD 和原有未提交改动都没变。没有提交，没有推送。

## 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/shared.py` | +25 / −2 | +36 / −7 | 一倍以内：为压 C901 抽出了 `check_manifest_fields` |
| `src/rulemason/init.py` | +4 / −1 | +6 / −1 | 一致 |
| `src/rulemason/check.py` | +80 / −8 | +105 / −14 | 一倍以内：七类问题改为具名常量；审查补了非 UTF-8 转换与注释 |
| `skills/rulemason/SKILL.md` | +3 / −1 | +3 / −1 | 一致 |
| `tests/test_shared.py` | +30 | +31 / −4 | 一致 |
| `tests/test_init.py`、`tests/test_update.py` | +40 | +57 | 一倍以内：审查补了「以前删掉过的清单」用例 |
| `tests/test_check.py` | +100 / −3 | +129 / −3 | 一倍以内：审查补了 6 个用例 |
| `tests/conftest.py` | — | +9 | 未估计：精简时把 `set_joined` 移到这里，两个测试文件共用 |

## 偏离与说明

- design 写的是 `joined_date` 在 `init` 和 `update` 共用；实际实现中，新接入（没有清单）时不看 git，直接取当天，以符合规格「init 记接入当天」（审查第 1 轮发现）。老清单补日期仍按 git 推算。
- 函数签名的调整：`gate_records` 的参数从 `(root)` 改成了 `(dated)`，`spec_writing` 多了 `files` 参数，都是精简时的调整，对外行为不变；`joined_date(root, manifest)` 与 tasks 1.1 一致。
