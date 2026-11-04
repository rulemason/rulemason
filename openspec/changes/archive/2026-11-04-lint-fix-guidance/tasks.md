# Tasks

## 1. 旧位置的基础配置副本

- [x] 1.1 `check.py` 新增旧位置副本识别（ruff 与 ESLint 共用）：引用指向项目内同名基础配置、不在 `.rulemason/lint/` 下时，与项目内副本比较内容（副本未生成时与本机版本将写入的内容比较），分出「内容相同」「内容不同」；验证：`tests/test_check.py` 新增两个用例，分别断言两种结果
- [x] 1.2 `_ruff_fix` 与 `_eslint_fix` 先走旧副本判断：内容相同改指向 `.rulemason/lint/`，并在汇报提示旧文件已无人引用、可以删除；内容不同返回说明（`diff` 命令、保留设置、改哪一行、`rulemason update`）；验证：`tests/test_init.py` 的「卸载后再接入」用例通过（`rulemason remove --yes` 后再 `init --yes`，`ruff.toml` 改为继承 `.rulemason/lint/ruff-base.toml`，`lint/ruff-base.toml` 仍在，「需要你处理」没有 ruff 项），「旧副本被改过」「ESLint 引入旧位置副本」两个用例通过
- [x] 1.3 `check_lint` 对旧副本报「继承的是旧位置的基础配置副本」，内容相同时第一行下一步为 `rulemason update`；验证：`tests/test_check.py` 的「check 的口径」用例通过
- [x] 1.4 ESLint 重复引入：同一配置既引入 `.rulemason/lint/eslint-base.mjs` 又引入其他位置的同名基础规则时，check 报「重复引入基础规则」并非 0 退出，说明写明旧引入与其使用项的行号和原文；init 与 update 不改该文件；验证：`tests/test_check.py` 与 `tests/test_init.py` 的「同时引入两份」用例通过

## 2. 走继承链

- [x] 2.1 `check.py` 新增走链函数：从一份 ruff 配置沿 `extend` 解析到末端（复用 `_target`），返回链上每份文件与内容，并给出停下的原因（末端、项目外、读不出、循环、超过 10 层）；旧位置副本按第 1 组处理，不作为链的末端；验证：`tests/test_check.py` 新增两层、三层、项目外、循环、超过 10 层五个用例通过
- [x] 2.2 `check_lint` 改为沿链判断「已接上」与 `select`，链中断时写明哪份配置的哪个引用；验证：「末端接上即为接上」「链上的 select」两个场景的用例通过，`test_broken_ruff_ref_is_reported_separately` 仍通过

## 3. init / update 在末端补继承

- [x] 3.1 `_ruff_fix` 在旧副本判断之后沿链处理：链上已接上不改；末端在项目内、无 `select`、无循环时返回末端文件的改写；其余情况返回说明；`plan_lint` 能写入不在 `ruff_configs` 列表里的末端文件，同一文件只写一次；验证：`tests/test_init.py` 的两层、三层、共用末端、循环用例通过，原 `test_other_ruff_extend_and_legacy_eslint_are_reported` 改为断言末端被补齐、`ruff.toml` 逐字不变
- [x] 3.2 update 走同一判断；验证：`tests/test_update.py` 新增「update 沿链补齐」「update 改正旧位置副本」与「补齐后再跑 `update --yes` 计划为空」三个用例通过

## 4. 改不了的项写明怎么改

- [x] 4.1 ruff 的 `select`、继承链走到项目外、继承链循环、超过 10 层、末端 `pyproject.toml` 没有 `[tool.ruff]` 五种说明：第一行摘要，后面写文件与行号、原文、可选做法（改后的原文）、「改完运行：rulemason update」；验证：`tests/test_init.py` 断言 `ruff.toml` 第 3 行 `select` 的说明含行号、原文、`extend-select` 与「删去这一行」两种做法，项目外的说明含改后的 `extend` 原文与复制设置的提醒，全部说明不含 `sed`
- [x] 4.2 ESLint 格式认不出时写明在第一条 `import` 之前加的引入原文与数组第一项；`.eslintrc*` 写明先运行 `npx @eslint/migrate-config <文件>` 再 `rulemason update`；验证：对应两个用例通过
- [x] 4.3 check 第一行在只剩手动 lint 项时只取说明的摘要行，完整步骤列在报告「接入 lint 继承」下；能沿链补齐或改正旧副本时下一步仍是 `rulemason update`；验证：`tests/test_check.py` 的「只剩手动 lint 项」用例改为断言第一行只有一行且不含「运行 rulemason update」，新增「能沿继承链补齐时不算手动项」用例通过；`check --json` 的字段集合不变
- [x] 4.4 README 与 README.en 的「出了问题怎么办」补「接入：手动修改 …」一行，说明报告里写了行号与做法；「卸载」一节补一句：卸载后再接入会把 `lint/` 下未改过的基础配置改回引用 `.rulemason/`；验证：中英命令表同步测试通过，README 出现这两处；README.en 是简版、没有这两节，只在 check 说明后补一句改不了的项会写明文件与行号

## 5. remove 沿链改指向

- [x] 5.1 `remove.lint_configs` 从每份 ruff 配置走链，收集引用 `.rulemason/lint/ruff-base.toml` 的文件，同一文件只改一次；验证：`tests/test_remove.py` 新增「继承链末端引用副本」用例：卸载后末端改为指向 `../lint/ruff-base.toml`，`ruff.toml` 逐字不变，`lint/ruff-base.toml` 与原副本相同

## 6. 收尾

- [x] 6.1 用临时项目复现问题报告里的两种情况：一是根 `ruff.toml` 继承 `lint/ruff-base.toml`（与副本相同），`apps/admin-web/eslint.config.js` 同时引入 `lint/` 与 `.rulemason/` 两份基础规则；二是根 `ruff.toml` 继承项目内另一份配置。依次运行 `rulemason init --yes`、`rulemason check`、`ruff check .`；验证：第一种 ruff 改指向、ESLint 报重复引入并给出行号；第二种末端被补齐；两种都能用 `ruff check --show-settings` 看到 ruff-base 的规则
- [x] 6.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙的 worktree 跑 `rulemason check` 与 `rulemason update --dry-run`，记录与改动前是否一致；验证：结果与 design 行数对照写进 `verification.md`

## Workflow follow-up

- 发版 0.8.11：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README、README.en 的 CI 钉版本，推送、归档、打 tag；发布说明写明「ESLint 重复引入基础规则」是新增检查，会让这类项目的 check 变为非 0。
- 接入项目运行 `uv tool upgrade rulemason` 与 `rulemason update`。
- 在出问题的那台 Mac 上重新运行 `rulemason update` 与 `rulemason check`，确认 ruff 不再报，admin-web 报出重复引入并照说明删去旧引入。
