# Design

## Context

动机见 proposal.md「Why」。现状：

- `check._ruff_fix` 只看一份配置自己的 `extend`：没有就插入，指向不存在或项目外的同名基础配置就改指向，指向别的存在的配置就只给一句 note。`init.plan_lint` 与 `update` 都用它决定改不改；`check.check_lint` 用 `_inherit_problem` 只看这一份配置的引用；`remove.plan_lint_move` 只改 `ruff_configs` 里那几份配置。
- 「旧路径」的判断只认目标不存在或在项目外（`broken_refs`）。`rulemason remove` 会把基础配置移到项目根 `lint/` 并改好引用，这些文件存在且在项目内，所以卸载后再接入时，ruff 落进「已继承其他 ruff 配置」，ESLint 则被当成普通的其他引入。`_eslint_fix` 只要有一条引用指向项目内副本就返回「已接上」，同时引入的旧位置副本不会被发现。
- `ruff_configs` 只收文件名为 `ruff.toml` 或含 `[tool.ruff` 的 `pyproject.toml`。继承链上的文件可以叫任何名字（如 `config/ruff-shared.toml`），不在这个列表里。
- ruff 的 `extend` 只接受一个路径，相对路径按所在配置文件的目录解析，支持 `~`；被继承的配置可以再 `extend`。现有 `_target` 已按这个规则解析。
- 改不了的项以字符串进 `plan.notes`，由 `print_notes` 逐条打印成 `  - …`；`check` 第一行在只剩手动 lint 项时把整条 note 拼进去。

## Goals / Non-Goals

**Goals:**
- init / update / check / remove 对继承链的看法一致：check 认为接上的，update 不再改；update 改完的，check 不再报。
- 手动项的说明零基础可照做：文件、行号、原文、做法、下一条命令。

**Non-Goals:**
- 不调用 ruff 本身解析配置。
- 不改 JSON 输出结构（`check --json`、`init --plan --json`、`update --dry-run --json` 的字段不变，说明仍在 note 字符串与 `text` 里）。

## Decisions

1. **先认旧位置副本，再走继承链。** 引用指向项目内同名基础配置（不在 `.rulemason/lint/` 下）时先按副本处理，不当作项目自己的配置。否决「一律走继承链」：基础配置本身写着 `select`，旧副本若被当成链的末端，会被判成「链上有 select」，报出一条让人看不懂的提示，而真正要做的只是改一个路径。
2. **按内容是否相同决定改不改。** 与项目内 `.rulemason/lint/` 副本比较；副本还没生成（同一次 init 才写）时，与本机版本将写入的内容比较。相同就改指向；不同说明有人改过基础配置，改指向会丢掉这些改动，所以只报告并给出 `diff` 与改法。否决「同名即改指向」：会悄悄丢掉项目对基础规则的改动；否决「顺手删掉旧文件」：它不在 `.rulemason.yaml` 的清单里，不归 rulemason 管。
3. **ESLint 重复引入只报告，不自动删。** 删一条引入要连带删掉配置数组里用它的那一项，变量名与写法各项目不同，与现有「删引入要连带删用法，不自动做」的取舍一致。否决「把旧引入改指向 `.rulemason/`」：同一份规则会被加载两次，重复问题仍在。
4. **基础配置接在继承链末端。** 末端配置加一行 `extend`，链上其余文件不动；末端在链的最底层，基础规则最先生效、其余配置照常覆盖。否决「把 `ruff.toml` 的 `extend` 换成 ruff-base」：会丢掉原继承配置里的设置；否决「把原继承配置的内容抄进 `ruff.toml` 再换 extend」：同一份设置出现两处，以后两边会改岔。
5. **自己沿 `extend` 走链，不调用 ruff。** 新增一个走链函数，复用 `_target` 解析路径，记录走过的文件以发现循环，最多走 10 层。否决用 `ruff check --show-settings` 解析：init 运行环境不一定装了 ruff，而且它只给最终设置，看不出该改哪份文件。
6. **链上任一配置写了 `select` 就整条不改。** 末端补继承后，上层的 `select` 仍会覆盖基础规则，改了也接不上。否决「自动把 `select` 改成 `extend-select`」：两者含义不同（前者限定、后者追加），会改变项目实际启用的规则，必须由人决定。
7. **check 判断「已接上」和「有没有 select」都走整条链。** 否决只看首份配置：update 在末端补完后，首份配置的引用仍指向中间文件，check 会一直报「没有继承」，update 又重复改，形成循环。
8. **说明仍是一条字符串：第一行摘要，后面缩进写步骤。** `print_notes` 原样打印多行；check 第一行只取摘要行，完整步骤在报告「接入 lint 继承」下。否决给 `LintFix` 与 JSON 加结构化的 `steps` 字段：现在没有调用方需要它，`/rulemason` 读的是 `text`。
9. **不给改文件的 shell 命令，只给行号与原文。** 否决生成 `sed` 一行命令：macOS 与 Linux 的 `sed -i` 写法不同，TOML 引号与行尾注释容易被改坏。唯一给出的命令是改完运行的 `rulemason update`，以及 `.eslintrc` 迁移用的官方工具 `npx @eslint/migrate-config`。
10. **`.eslintrc` 只给迁移指引，不代为运行迁移工具。** 否决在 init 里自动运行 `npx @eslint/migrate-config`：要联网、要求本机有 Node，还会写出计划以外的文件。
11. **remove 沿链找真正引用副本的文件。** 从每份 ruff 配置出发走链，凡是引用了 `.rulemason/lint/ruff-base.toml` 的文件都改指向 `lint/`，同一文件只改一次。否决只改 `ruff_configs` 列表里的文件：末端文件不在列表里，卸载后 ruff 会找不到基础配置。

## Risks / Trade-offs

- [末端是 `pyproject.toml` 但没有 `[tool.ruff]` 表] → 不新建表，按「无法安全写入 extend」报告，给出要加的两行原文。
- [末端文件被项目外的工具或别的仓库共用] → 只改项目根内的文件；末端在项目外时只报告。
- [多份配置共用同一末端，计划里重复出现] → 计划按文件路径去重，同一文件只写一次。
- [报告里的行号在用户编辑后过时] → 行号在每次 init / update / check 时重新计算，说明末尾都写「改完运行 rulemason update」重新核对。
- [继承链很深或指向大文件] → 最多走 10 层，超过按「继承链过深」报告。
- [旧副本内容只差注释或空行，或来自旧版本 rulemason，被当成「改过」] → 除换行统一为 LF 外不做归一化，说明写「被改过或来自旧版本」，宁可多报一次让人看 `diff`，也不悄悄丢改动。
- [ESLint 重复引入新报出来，已接入项目升级后 check 变成非 0] → 说明给出行号与原文，删两行即恢复；发布说明写明这一变化。
- [同一份 ESLint 配置里既有失效引用又有旧位置副本引用，update 只改失效那条，下次 check 报成重复引入] → 说明照常给出删哪一行，多走一轮但不会改坏；情况罕见，不为它加分支。
- [一份 ruff 配置原来同时报「没有继承」与「写了 select」两条，现在只报 select 那一条说明] → select 不去掉就接不上，先报它是对的；发布说明写明。

## Migration Plan

1. 在本仓库实现并通过测试，版本号升到 0.8.11，README 与 README.en 的 CI 示例钉到 `rulemason==0.8.11`。
2. 推送 `v0.8.11` tag，CI 发布到 PyPI 并自动建 Release。
3. 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`：原来卡在「已继承其他 ruff 配置」的项目会在计划里看到末端配置的修改，确认后跑一遍 ruff 再提交。

回滚：update 写入的只是末端配置里一行 `extend`，在项目里用 `git checkout -- <文件>` 撤回即可；工具本身回到 `uv tool install rulemason==0.8.10`。CI 钉版本的项目不受本机升级影响。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/check.py` | 旧位置副本识别（ruff 与 ESLint 共用）；ESLint 重复引入；走链函数；`_ruff_fix` 改为先认旧副本、再沿链补末端；`check_lint` 沿链判断接上与 `select`；各种手动项的分行说明；第一行只取摘要 | +150 |
| `src/rulemason/init.py` | `plan_lint` 写入末端文件（不在 `ruff_configs` 列表里时也写） | +10 |
| `src/rulemason/remove.py` | `lint_configs` 沿链收集引用副本的文件 | +15 |
| `src/rulemason/__init__.py` | 版本 0.8.11 | 1 |
| `README.md`、`README.en.md` | 「出了问题怎么办」补手动 lint 项一行；CI 示例版本 | +4 |
| `tests/test_check.py` | 旧副本的口径、ESLint 重复引入、链上接上、链上 select、链中断、第一行摘要 | +85 |
| `tests/test_init.py` | 卸载后再接入、旧副本被改过、ESLint 引入旧副本、两层、三层、共用末端、循环、项目外、select 行号说明、ESLint 与 `.eslintrc` 说明；改写原「已继承其他 ruff 配置」用例 | +140 |
| `tests/test_update.py` | update 沿链补齐、再跑无改动 | +30 |
| `tests/test_remove.py` | 末端引用副本时卸载 | +25 |
