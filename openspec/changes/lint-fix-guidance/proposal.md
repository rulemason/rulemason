## Why

在 macOS 上给一个 monorepo 接入时，`init` 停在「ruff.toml 已继承其他 ruff 配置：未修改，请改为继承 .rulemason/lint/ruff-base.toml」，用户不知道该改哪个文件、改成什么。实际原因是 `ruff.toml` 继承的 `lint/ruff-base.toml` 是基础配置放在旧位置的副本，内容与 `.rulemason/lint/ruff-base.toml` 完全相同。`rulemason remove` 正是把基础配置移到 `lint/`，所以卸载后再接入就会卡在这里。同一项目的 ESLint 配置同时引入旧位置和 `.rulemason/` 两份基础规则，check 却认为已接上，没有报出来。

ruff 的 `extend` 只能写一个路径，所以 rulemason 现在对指向项目内其他文件的 `extend` 一律不改、只给一句提示。可是旧位置副本只需改指向；被继承的若是项目自己的配置，把基础配置接到继承链的末端也不丢原有设置。这两种情况都不需要人来决定，rulemason 可以自己做。

真正需要用户决定的情况（写了 `select`、继承了项目外的配置、ESLint 配置格式认不出），现在的提示没写文件行号和原文，零基础用户照着做不下去。

## What Changes

- 识别旧位置的基础配置副本：ruff 的 `extend` 或 ESLint 的引入指向项目内另一份同名基础配置（`ruff-base.toml`、`eslint-base.mjs`，不在 `.rulemason/` 下）时，内容与 `.rulemason/lint/` 副本相同，`init` 与 `update` 就把路径改到 `.rulemason/lint/`，并提示旧文件已无人引用、可以删除（不代为删除）；内容不同时不改，写明对比差异、保留改动、改指向的步骤。这一判断先于沿继承链处理。
- ESLint 配置已引入 `.rulemason/` 的基础规则、又引入旧位置的同名基础规则时，check 报「重复引入」，说明写明要删的引入行与配置项所在行号；不自动删除。
- ruff 配置已经 `extend` 了别的配置时，沿继承链找到末端那份配置。末端在项目内、可读，链上没有 `select`、没有循环时，`init` 与 `update` 在末端配置里补一行继承 `.rulemason/lint/ruff-base.toml`，作为一条「修改」列进计划，与其他改动一起确认。原来的 `extend` 保持不动。
- `check` 判断 ruff 是否接上基础配置时沿继承链查：链上任一配置继承了项目内的 ruff-base 副本，就算接上。这样补齐之后不会再报「没有继承」，`update` 也不会重复改。
- 改不了的 lint 项，「需要你处理」与 `check` 第一行要写清四件事：文件与行号、要删改或加入的原文、可选做法、改完运行的命令。覆盖三种情况：
  - 链上某份配置写了 `select`：给出「改为 `extend-select`」与「删去该行」两种做法；
  - 继承链走到项目外：给出把 `extend` 改为项目内副本要写的那一行，并提醒把需要的设置复制进项目；
  - ESLint 配置格式认不出：写明在哪个文件哪一行之后粘贴哪两段。
- `remove` 把基础配置移到项目 `lint/` 时，改写的是继承链里实际引用副本的那份配置，lint 结果保持不变。
- 不做：自动改写 `select`（会改变项目实际启用的规则，必须由人决定）；删除旧位置的基础配置文件或删除 ESLint 的重复引入（删引入要连带删用法）；修改项目外的文件；改写 `.eslintrc*` 老格式；给出用 `sed` 等命令直接改文件的一行命令（macOS 与 Linux 写法不同，TOML 引号与注释容易改坏）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：init、update 识别旧位置的基础配置副本并改指向；check 报 ESLint 重复引入；init、update 的 ruff 继承补齐改为沿继承链接到末端；check 判断「已接上」改为沿继承链；「init 可重复运行，冲突只报告」与「check 第一行给结论与下一步」中，手动项的说明要写出文件行号、原文、可选做法与下一步命令；「remove 保持 lint 可用」覆盖继承链。

## Impact

- 代码：`src/rulemason/check.py`（`ruff_refs`、`_ruff_fix`、`_eslint_fix`、`manual_lint` 的继承链与说明）、`src/rulemason/init.py` 与 `src/rulemason/update.py`（计划里的修改项）、`src/rulemason/remove.py`（继承链里的引用改写）。
- 测试：`tests/test_check.py`、`tests/test_init.py`、`tests/test_update.py`、`tests/test_remove.py`，补旧位置副本（内容相同、内容不同、remove 后再 init）、ESLint 重复引入与继承链（两层、三层、项目外、循环、链上 select）用例。
- 接入项目：已经直接继承 ruff-base 的项目不受影响。原来卡在「已继承其他 ruff 配置」的项目，升级后运行一次 `rulemason update` 即可自动接上。ESLint 重复引入了基础规则的项目，升级后 check 会新报一项（非 0 退出），按说明删去旧引入即可。
