# gates-evidence 验证记录

## 1. 方案与写代码前的判断

- 方案写完时，`rulemason judge --change gates-evidence` 结果为 pass 3、review 0、block 0。
- 写代码前再跑一次，pass 3、block 0。

## 2. 自动精简（/simplify，四路并行）

- **效率**：pass。归档目录被 `archived()` 和 `gate_records` 各扫一遍，每次多花约 1 毫秒，check 每次运行只调用一次，不必为此把两个函数绑在一起。
- **层次**：pass。新巡检项和已有巡检项是同一种写法，不进入「接入」层，也不影响退出码与下一步。
- **复用与简化**，采纳：
  - 抽出 `archive_dirs(root)`，`archived()` 与 `gate_records` 共用，去掉重复的路径与目录判断（九条第 7 条）；
  - 带条件的海象推导式拆成循环（一行一事）；
  - 同日过滤改为 `sorted(p for day, p in dated if day == latest)`；
  - 测试里的 change 名提成常量 `LATEST`，参数名 `report` 改为 `text`，免得和 `report_` 撞名。
- **复用与简化**，不采纳：
  - 改用 `_read(root, …)` 读文件：要先把路径转成相对路径，读起来反而更绕。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件，不读仓库、不运行命令。

- **第 1 轮**：没有 block，有 1 条 review（正确性），对应补 1 条测试。
  - 问题：Python 正则默认按 Unicode 判断词边界，汉字也算单词字符，所以「独立review」「单元test」这种英文紧贴汉字的写法会被误报为没写到。
  - 修法：两个正则加上 `re.I | re.A`；测试那一项改为 `\btest`，`testing` 也能认出。
  - 新增两个应当通过的用例：「独立review 两轮；单元test 12 项通过」和「Reviewed twice; testing done.」；`preview`、`latest` 的反例保留。
- **第 2 轮**：确认修复到位，六项全部 pass，没有 block，也没有 review。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`：442 passed，未联网。
- 本次没有改判断规则，也没有改 `JEV_MODEL`，跳过判断回归。
- 本仓库没有前端，也没有界面文案，前端 lint 与文案检查跳过。

## 5. 接入项目试跑（额外步骤）

在临时 detached worktree 里用本次代码依次运行 update 和 check。三个项目跑完后，主工作区都没有变化。

| 项目 | check 第一行与退出码 | 最近归档的检查点记录 |
|---|---|---|
| 项目甲 | 日常巡检：一切一致，0 | 2026-11-01 的两个迁移 change 都没有 `verification.md` |
| 项目乙 | 日常巡检：一切一致，0 | 同上，也是 2026-11-01 的两个 change |
| 项目丙 | 日常巡检：一切一致，0 | 一致（最近一天的 3 个都有，其中一份是纯表格写法，也判为合格） |
| 本仓库 | 日常巡检：一切一致，0 | 一致 |

结果与 proposal 的预期一致：只报告，不改变退出码和下一步。

## 6. 与 design 的偏差

- 英文关键词的匹配方式和 design D2 写的不同。D2 写的是按子串匹配 `review` 和 `test`，实现中改为 ASCII 词边界，并单独认 `pytest`。原因是按子串匹配时，`latest` 会被当成 test，`preview` 会被当成 review，造成误判；第 1 轮审查又补上了英文紧贴汉字的情况。

## 7. 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 |
|---|---|---|
| `src/rulemason/check.py` | +25 | +37 / −2，超出不到一倍；多出的行是共用的 `archive_dirs` 和两条正则的说明 |
| `skills/rulemason/SKILL.md` | +1 | +1 |
| `tests/test_check.py` | +45 | +40 |
