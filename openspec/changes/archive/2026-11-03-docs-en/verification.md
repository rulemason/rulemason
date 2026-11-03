# docs-en 验证记录

## 1. 方案与写代码前的判断

- 方案写完：`rulemason judge --change docs-en` 结果为 pass 3 / review 0 / block 0。
- 写代码前：结果为 pass 3 / block 0。

## 2. 自动精简

本次只改文档、包简介和测试，没有代码逻辑改动，跳过精简。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件，不读仓库、不运行命令。材料包括 change 产物、`README.en.md` 全文、中文 README 的相关段落和完整 diff。

### 第 1 轮：block 1，review 5

**block（测试）**：同步测试用裸子串判断，挡不住漂移。`/rulemason` 必定出现在英文版的 GitHub 网址里，`rulemason init` 等命令也会被正文命中，英文表格删掉这几行后测试照样通过。实施时我用的反例只删了 `remove`，没能暴露这个问题。修法如下：
- 两边都用 `readme_commands(text, 标题)` 取出各自命令表里反引号中的命令；
- 去掉占位参数（中文的「功能名」或 `<change-name>`）后，按命令表逐条比对。

**review，已修**：
- Judgment 一条补上「Without a key, the rules are checked by hand.」。
- Checkpoints 一条补上「只有动到主规格已写的承诺才起最小 change 并问一次，其余直接改再 lint 与测试」。
- design D1 的「三块」与正文列的四部分不一致，统一为四部分。

**review，未改**：
- 英文版「check 非 0 退出，可直接放进 CI」这句保留。中文 README 第 72 行就是这样写的，审查材料只截了前 60 行，审查者没看到。
- 简介里的全角括号保留。审查者建议改成破折号，但用户已确认用这一句原文作为 GitHub 简介。

**其他**：`previews/` 不属于本 change，提交时排除。

### 第 2 轮：没有 block，review 1

第 1 轮的处理全部确认到位。唯一的 review 已修：只查了一个方向，中文表删了某条命令、英文表忘了删时测不出来。现在补上反向检查，两边的命令表必须完全一致。按规定不再审第 3 轮。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`：444 passed，不联网。
- 防漂移实测：
  - 分别删掉英文命令表中 `rulemason remove`、`/rulemason`、`rulemason init`、`rulemason judge` 所在的行，测试都失败，并指出缺的是哪一条；恢复后通过。
  - 反向检查是第 2 轮审查后补上的，只在代码层面确认过，没有做删改实测。
- 判断回归、前端 lint、文案检查：不适用，已跳过。

## 5. 包元数据与对外修改

- `uv build` 生成的 wheel 中，METADATA 的 Summary 为：`Shared rules and checkpoints for AI coding tools（给 AI 编码工具的共享规则与检查点）：一处维护规则，项目内生成只读副本，方案与代码前后自动判断与审查`。PyPI 页面会在 0.8.8 发布后更新。
- GitHub 仓库简介：经用户确认，用有仓库权限的维护者账号运行 `gh repo edit` 修改，`gh repo view` 已核实新内容生效。
  - 改前：`给 AI 编码工具的共享规则与检查点：一处维护规则，项目内生成只读副本，方案与代码前后自动判断与审查`
  - 改后：`Shared rules and checkpoints for AI coding tools（给 AI 编码工具的共享规则与检查点）：一处维护规则，项目内生成只读副本，方案与代码前后自动判断与审查`
- 两份 README 里的互相链接用的都是 GitHub 完整网址。指向 `main` 分支上的 `README.en.md`，要等提交推送后才能打开；推送后需在 GitHub 与 PyPI 页面上各点一次确认。

## 6. 与 design 的偏差

- 测试的比对方式改了：design D2 原写「在 `README.en.md` 中出现」，现为「两张命令表逐条一致（双向）」。原因见第 3 节。
- `README.en.md` 顶部也加了一个回到中文版的链接，design 只写了中文版指向英文版。

## 7. 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 |
|---|---|---|
| `README.en.md` | +40 | +42 |
| `README.md` | +2 | +2 |
| `pyproject.toml` | ±1 | ±1 |
| `tests/test_templates.py` | +20 | +31 |

所有文件都没有超过估计的一倍。
