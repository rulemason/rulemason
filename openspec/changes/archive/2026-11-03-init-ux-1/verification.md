# init-ux-1 完成汇报

## 1. 写代码前的判断

`rulemason judge --change init-ux-1`：pass 3 / review 0 / block 0。

## 2. 自动精简（/simplify，4 路并行）

- 采纳：删掉被补丁重复套了一次的颜色常量与 `KEY_URL`（真问题，ruff 不报重复常量）；`shared.has_openspec` 替换 7 处 `(root / "openspec").is_dir()`；`split_writes` / `untouched_line` 供完整计划与摘要共用；`print_notes` 放进 init，update 共用；`check.judge_blockers` 供 `judge_label` 与 `guide_key` 共用；`frontend_dirs` 在识别表复用；编号退路复用已算好的标签与标注；Ctrl-C 在选择器里处理（cbreak 下 `\x03` 映射永远不会触发，删掉）；`.gitignore` 链条与选择器重画简化；ESLint 提示复用 import 字面量；`banner.show` 用 `color_enabled`。
- 跳过：`generated_files` 去掉默认参数（测试仍有调用方）；`block_body` 抽模板表（只有一个变体）；专门的「检查点」层（没有收益）；全部性能类建议（缓存 `react_dirs` / `has_git`、`report` 不跑整份 check 等）。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件。

**第 1 轮**：block 0。三条真缺陷与若干 review，全部处理：

1. `.gitignore` 只按文件规则（如 `*.md`、`SKILL.md`）忽略时，只放行目录没有用：改为逐级链条后以 `!目录/**` 收尾，并覆盖 `.rulemason/`；目录是符号链接或在项目外时跳过，交给写入前校验。
2. 单独按下 ESC 会阻塞到下一键：读后续字节前先用 `selectors` 等 50 毫秒。
3. `readme_intro` 把「Node.js」「v1.0」里的点当句号：句末只认中文标点，或后面是空格 / 行尾的英文标点。
4. 画第一帧之前先确认能逐键读取，stdout 被管道接走时不会把转义写进日志。
5. 规格与 design 补上三处偏离（见第 7 节）；`select.render` 改用 `shared.DIM` / `YELLOW`；`YES` 常量共用；`.rulemason/README.md` 归「规则副本」。
6. 测试补：`read_key` 转义解析、裸 ESC 不阻塞、异常时恢复终端、EOF 取消、画帧前探能力；`.gitignore` 四种起点；旧全量副本 `update` 后删掉 `react.md`；结论行紧接改动清单；「Node.js」句子。

**第 2 轮**：block 0，review 若干，修完后跑完 ruff 与测试，按规则不再审第三轮：

1. `readme_intro` 的 `if not sentences` 是死分支，删掉。
2. 忽略来自子目录自己的 `.gitignore` 时，根文件的放行规则没用，每次 init 都会重复追加：放行规则已写过就不再追加，补测试。
3. `ensure_supported` 用 `# noqa` 违反 python.md「不逐行 noqa」：改为 `importlib.util.find_spec("termios")`。
4. `plan_gitignore` 的推导式变量遮蔽外层 `rel`，改名 `path`。
5. 测试：`.gitignore` 整体忽略 `.rulemason/` 的起点补一例；`*.md` 断言直接写；假键盘的管道由 fixture 关闭；抛异常改用小函数。

## 4. ruff 与测试

- `uv run ruff check .`：通过。
- `uv run pytest`：408 passed（改前 360，新增 48）。
- 判断回归：没有改判断规则与 `JEV_MODEL`，跳过。
- 前端 lint、文案检查：本仓库没有，跳过。

## 5. 手工试跑（任务 5.2）

- 伪终端（Python `pty` 驱动，按键分步喂入）交互 init：下移、空格、回车选中 Claude Code；摘要「新增 8 个文件：规则副本 2、配置 2、skill 1、入口 3」；`d` 展开完整清单后再问一次；`y` 写入；README 第一段预填两句；`.gitignore` 为 `.claude/` 时写入 5 行链条并 `!…/**` 收尾，git 不再忽略；`*.md` 起点同样放行 `.rulemason/` 与 skill 副本；重跑时预勾 claude、无改动时只打印提示。
- Go 项目 `--yes` 无 openspec：不跑 `openspec init`，只生成 `code-style`、`workflow-gates`、README 与 skill 副本；AGENTS 检查点块写明未启用；`check` 退出 0，识别表 openspec 一行说明未启用。
- 三个接入项目临时 worktree `update --dry-run`：只多出 README / skill 副本刷新；项目丙多出删掉 `react.md` 与 `eslint-base.mjs`（它没有 React 也没有 ESLint 配置）；`check` 退出码不变；主工作区不变。
- 交互 init 结尾的 key 提问在本机看不到（本机已有 key），由测试覆盖三种条件。

## 6. 额外步骤

没有改 `rules/` 与 `lint/` 的正文，不需要在接入项目验证规则；第 5 节已覆盖接入项目的 `update` 与 `check`。

## 7. 实施中对方案的修正

- ESLint 基础配置在「有 React 目录或已有 ESLint 配置」时复制：项目乙的前端不是 React 却继承了 eslint-base，只随 React 会把它弄坏。design 决策 5 与 delta 已改。
- 没有 `openspec/` 的项目 `check` 要退出 0，于是把 init-ux-2 里「检查点未启用」那一项的最小版提前做了：不算「接入 产物写法」层，识别表的 openspec 一行写明未启用。design 决策 4 与 delta 已改。
- `.gitignore` 放行不是一行 `!目录/`，而是从被忽略的那一级起的链条加 `!目录/**`：git 不允许在父目录被排除时再包含子项，文件级规则也要覆盖。design 决策 8 与 delta 已改。

## 8. 版本

0.8.4（发版前已核对 `git tag` 最新为 v0.8.3，PyPI 最新 0.8.3）。

## 9. 行数对照

| 文件 | 估计 | 实际 |
|---|---|---|
| `src/rulemason/select.py` | +70 | +100 / −0 |
| `src/rulemason/init.py` | +120 / −40 | +222 / −50 |
| `src/rulemason/shared.py` | +30 / −5 | +32 / −4 |
| `src/rulemason/check.py` | +6 | +44 / −9 |
| `src/rulemason/update.py` | +4 / −2 | +5 / −11 |
| `src/rulemason/banner.py` | +3 / −12 | +14 / −24 |
| `templates/` | +15 / −3 | +7 / −4 |
| `skills/rulemason/SKILL.md` | ~4 | +3 / −3 |
| `README.md` | ~10 | +6 / −4 |
| `tests/test_select.py` | +60 | +130 / −0 |
| 其他测试 | +140 / −30 | +264 / −19 |

`init.py` 与测试超出估计一倍以上：审查后补的 `.gitignore` 链条、README 句子切分、选择器探测与 48 个新测试，估计时没有算进去。
