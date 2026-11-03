# init-ux-2 验证记录

## 1. 方案与写代码前的判断

- 方案写完：`rulemason judge --change init-ux-2` 第一次 block 1 条（`lint/design`：D8 缺否决理由），属起草失误，补上后 pass 3 / review 0 / block 0。
- 写代码前：pass 3 / block 0。apply 中按用户决定改了前端目录口径（见第 5 节），改后重跑仍是 pass 3 / block 0；`openspec validate init-ux-2 --strict` 通过。

## 2. 自动精简（/simplify，四路并行）

采纳（行为不变）：
- 「记录的版本比本机新 / 旧」原来散在三处，各自判空，收成 `version_order(sel)`。
- `next_stage` 原来靠在巡检文字里搜「只有版本号落后」来判断，改为直接用 `behind` 和版本比较的结果。
- `init.plan_stale_copies` 改用 `check.managed_prefixes`。
- 副本校验值的记录抽成 `shared.copy_record`，`plan_copies` 与 `copies_behind` 共用。
- `_ruff_fix` / `_eslint_fix` 开头算引用的重复代码收成 `_refs()`，每份配置只解析一次引用。
- `broken_refs` 改成循环，`check_lint` 改用海象赋值。
- `scan` 每进一个目录都重新合并一次排除集合，改为在循环前合并好。
- `manual_lint` 里 ruff 配置原来读两遍，改为只读一遍。
- `is_source_repo` 的判断移进 `copies_behind`。

跳过：
- 每个 `package.json` 一次 check 会解析多遍：纯性能问题，按规则不做。
- `check_lint` 整体改由 `lint_fix` 生成：两者的输出各有用处，`check_lint` 描述问题，`lint_fix` 给出改法；合并会改报告文字。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件，内含 diff、change 产物、九条与 `check.py` 全文；不读仓库、不运行命令。

第 1 轮：安全与变更卫生 pass，其余各项均为 review，没有 block。
- 已修：
  - #3：措辞改为「副本与本机版本应生成的不一致」，因为语言变化或启用判断也会触发这一条。规格补了「启用判断后副本要补文案语气」场景。
  - #4：清单没有副本记录时，不再声称「副本内容相同」（新增 `version_only`）。
  - #5：标记块模板跨版本的变化不在比较范围内，已写进 design 的风险。
  - #6：改了过时的注释与 `exit_code` 的 docstring；`_inherit_problem` 改用 `_refs`。
  - #8：补测试，覆盖三种情况：只有 ESLint 坏引用、`tseslint.config()` 空参数、没有副本记录时版本落后。
- 驳回：
  - #1：ruff 的 `extend` 只能写一个路径，正确引用和坏引用不会同时出现。
  - #2：`generated_files` 只生成副本目录里的路径。
  - #7：`Template` 原本就已导入；update 的补齐计划也走 `plan_lint`，已有测试覆盖。

第 2 轮：第 1 轮的处理全部确认到位；没有 block，有 4 条 review，已全部修复，按规定不再审第 3 轮。
- 补了「启用判断后副本要补文案语气」的直接测试。
- 「有 Python 代码却没有 ruff 配置」在三处重复，抽成 `needs_ruff_config`。
- `frontend_dirs` 的 return 拆成两步。
- 手动提示里的「配置数组第一项」改为「配置数组（或 config( 调用）的第一项」。
- 审查者提出 update 在 `--json` 模式下可能多输出一行。核对后不会：`--json` 只配合 `--dry-run` 使用，而 dry-run 分支在打印这一行之前就已经返回。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`：429 passed，用时约 86 秒，未联网。判断回归：本次没有改判断规则文件，也没有改 `JEV_MODEL`，所以跳过。
- 前端 lint、文案检查：本仓库没有前端和界面文案，跳过。

## 5. 接入项目试跑（额外步骤）

每个项目都在临时 detached worktree 里运行，主工作区前后对比 `git status`，结果一致：

| 项目 | 0.8.4 check | 本次代码 check | update 后 |
|---|---|---|---|
| 项目甲 | 0，「日常巡检：运行 rulemason update 升级副本」 | 1，「接入：运行 rulemason update」，3 个副本与本机应生成的不一致 | 未单独跑（dry-run 计划与项目乙相同） |
| 项目乙 | 同上 | 1，同上（3 个文件） | 0，「日常巡检：一切一致」 |
| 项目丙 | 同上 | 1，同上（4 个文件，会删掉用不到的 `react.md`、`eslint-base.mjs`） | 0，「日常巡检：一切一致」 |
| 公司项目（未接入） | `init --plan`：client-web 的 `defineConfig([` 配置被报「无法自动识别」 | `init --plan`：该文件进入「修改」，不再列在「已跳过」里 | — |

- 试跑中发现：项目乙的 `frontend/` 是不用框架的 vite 前端，按原定口径会从前端目录里漏掉。用户确认改为「框架或 `index.html`」；改后项目乙的前端目录与 0.8.4 相同。
- 在临时项目里验证：Python 只在 `apps/api/` 时生成 `apps/api/ruff.toml`；在项目根运行 `ruff check .` 能读到继承的基础规则（`print` 被 T201 报出）。

## 6. 与 design 的偏差

- tasks 2.1 写的函数名是 `broken_lint_refs`，实际叫 `broken_refs`：它只按文件名比较，ruff 与 ESLint 共用一个函数，所以不带 lint 前缀。
- 前端目录口径加了「同目录有 `index.html`」（用户确认），proposal、design、规格与测试都已同步。
- 动作代码 `upgrade_copies` 已删除。原因：副本内容落后时走 `update`，只差版本号时走 `none` 并在动作后附一句。SKILL.md 的动作表同步删掉了它，新增 `manual_lint`。
- 顺带修了一个旧问题：项目根的 ESLint 配置生成的引入路径原来是 `.rulemason/lint/eslint-base.mjs`，Node 会把它当成包名；改为 `./.rulemason/…`，并加了测试。

## 7. 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/check.py` | +110 / −20 | +264 / −55 | 超出一倍。原因有三：`_insert_ruff_extend`、`config_ref` 从 init 整体搬入（约 25 行）；精简与审查新增了 `version_order`、`version_only`、`_Refs`、`needs_ruff_config`、`managed_prefixes`；`next_stage` 拆成两层。 |
| `src/rulemason/init.py` | +20 / −25 | +20 / −57 | 删除比估计多，因为 lint 判断整体移去了 check |
| `src/rulemason/shared.py` | +5 | +10 / −2 | 加了 `copy_record` 与 `CHECKPOINTS_OFF` |
| `src/rulemason/update.py` | +3 | +4 | |
| `src/rulemason/remove.py` | — | +1 / −5 | 改用 `check.repoint`，design 未列这个文件 |
| `ruff.toml.tmpl` | 1 | 1 | |
| `tests/test_check.py` | +130 | +103 / −5 | |
| `tests/test_init.py` | +80 | +54 | |
| `tests/test_update.py` | +30 | +22 / −1 | |
| `tests/test_shared.py`、`tests/test_templates.py` | — | +15、±2 | 扫描跳过的测试；模板占位与动作代码表 |
| `README.md`、`skills/rulemason/SKILL.md` | — | ±3、±5 | 退出码口径、动作表 |
