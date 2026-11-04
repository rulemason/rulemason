# Verification：lint-fix-guidance

按 `rules/workflow-gates.md`「apply 最后一个任务做完」逐项执行。

## 写代码前检查点

`rulemason judge --change lint-fix-guidance`：pass 3 / review 0 / block 0。

## 1. 自动精简与独立审查

**自动精简（Claude Code 下用 `/simplify`，四路并行：复用、简化、效率、修复深度）**，只采纳行为保持的修改：

- 采纳：路径计算抽成 `_base_ref`（原 5 处）；ruff 与 ESLint 共用 `_ref_kind` 判断引用是接上、失效还是旧位置副本，`broken_refs` 改为它的过滤；`_is_base_copy` 改用已有的 `sha256_file`（换行归一规则只留一处）；`_target` 只算一次；`LintFix.target` 在 `lint_fix` 统一补齐，调用方不再写兜底；notes 与 tips 共用 `print_notes`（加可选颜色）和 `list_block`；`check_lint` 与 `manual_lint` 不再重复读 ruff 配置；常量 `RUFF_BASE`、`ESLINT_BASE` 在改动过的文件里统一使用。
- 跳过：`collect` 里 `check_lint` 与 `manual_lint` 各算一遍 `lint_fix`（缓存要改函数签名，且改动前就如此）；旧副本比对与共用末端重复读几个小文件（有上限、收益小）。
- 撤回：无。

**独立审查**（只读一份材料文件的子代理，两轮）：

第一轮：

| 项 | 结果与处理 |
|---|---|
| 需求符合 | review：README.en 少两处 → 英文版是简版、没有「出了问题怎么办」与「卸载」两节，只在 check 说明后补一句，见「偏差」；review→按 block 处理：tasks 写了接入项目的真名 → 两个 change 的 tasks 都改为「项目甲、乙、丙」，并用私人词表扫过改动文件，零命中 |
| 正确性 | review：重复引入时把「用到旧引入的那一行」整行列为删去，会删坏配置 → 只有那一行只写这一项时才写删去，否则写「去掉对它的使用」；继承链上读不出的文件会让 check / init / remove 崩 → 新增 `unreadable`，给说明；ESLint 把无关引用也算进「别处引入」→ 只取失效与旧位置副本；`select` 数组跨多行时「改为」原文只有半行 → 加注；失效与旧副本混在同一 ESLint 配置、ruff 由两条报告变一条 → 写进 design Risks |
| 安全 | pass |
| 代码质量 | review：`plan_lint` 每轮重建列表 → `add_once`；remove 里的文件名字面量 → 用常量；「只写豁免」措辞不清 → 改写；章节编号 2.1 / 2.2 → 是原有「2. 各层状态」下的小节，未改 |
| 测试 | review：补 pyproject 末端无 `[tool.ruff]`、链上引用不存在 / 过深 / 读不出、ESLint 旧副本被改过、卸载后再接入（ESLint）、`check --json` 字段集合不变 |
| 变更卫生 | pass |

第二轮：无 block，6 条 review。按规则修完后只跑 ruff 与测试，不审第三轮：

- 重复引入的旧副本若被改过，说明先给 `diff` 再删引入（新测试）。
- 「被改过」可能其实是旧版本留下的 → 措辞改为「被改过或来自旧版本」，design Risks 同步。
- 引入名解析不出（`import { x }`、`import * as x`）时笼统提醒删去使用处；同一变量多处使用时逐处列出（新测试）。
- tasks 4.4 的验证文字与 README.en 实际不符 → 改写；design Risks「不做归一化」与实现不符 → 改为「除换行统一为 LF 外」。
- 补测：继承链末端是失效引用时改写末端；init 路径下链上文件读不出。
- 未改：「`_old_copy_fix` 里 `target=file` 与 `lint_fix` 的兜底重复」——ruff 走到这里时 `file` 是继承链末端，可能不是起点文件，必须显式写，兜底只管起点。

## 2. ruff

`uv run ruff check .`：All checks passed!

## 3. 测试

`uv run pytest`：489 passed（改动前 460；新增 29 条，改写 5 条旧用例以匹配新说明）。未改判断规则文件或 `JEV_MODEL`，不跑判断回归。

## 4. 前端 lint

跳过：本仓库无前端。

## 5. 文案检查

跳过：本仓库无界面文案（命令行输出的说明文字已由测试锁定）。

## 6. 额外步骤

未改 `rules/` 或 `lint/`，额外步骤不适用；仍在项目甲、乙、丙用本分支开发版与已安装的 0.8.10 对比：`check` 第一行、`check --json` 的「接入 lint 继承」、`update --dry-run --json` 的补齐与待处理三项，三个项目结果完全相同（三者都因记录版本较旧而提示 update，与本次改动无关）。

## 7. 问题报告场景复现（任务 6.1）

临时项目，本分支开发版：

- 场景一：根 `ruff.toml` 继承 `lint/ruff-base.toml`（与副本相同），`apps/admin-web/eslint.config.js` 同时引入 `lint/` 与 `.rulemason/` 两份基础规则。`init --yes` 后 `ruff.toml` 改为继承 `.rulemason/lint/ruff-base.toml`；「提示」写明旧副本可删，不算待处理；「需要你处理」只有 ESLint 重复引入，写明删去第 2 行与第 8 行；照做后 `check` 退出码 0。`ruff check --show-settings` 能看到 BLE001、B905、T201。
- 场景二：根 `ruff.toml` 继承 `config/ruff-shared.toml`。`init --yes` 只修改末端文件，`ruff.toml` 逐字不变，原有 `line-length` 保留；`check` 第一行为「补项目信息」。

## 与 design 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/check.py` | +150 | +285 / −85 | 净增 200，未超出一倍；多出的是两轮审查补的读不出、重复引入的逐处使用与旧副本 diff 提示 |
| `src/rulemason/init.py` | +10 | +28 / −14 | 多出 `Plan.tips`、`add_once`、`list_block`（提示通道，见「偏差」） |
| `src/rulemason/remove.py` | +15 | +6 / −3 | |
| `src/rulemason/update.py` | 未列 | +6 / −2 | 打印提示 |
| `src/rulemason/__init__.py` | 1 | 0 | 版本号留到发版时改（tasks Workflow follow-up） |
| `README.md`、`README.en.md` | +4 | +4 / −3 | CI 钉版本留到发版时改 |
| `skills/rulemason/SKILL.md` | 未列 | +1 / −1 | 见「偏差」 |
| `tests/test_check.py` | +85 | +100 / −4 | |
| `tests/test_init.py` | +140 | +196 / −4 | 第二轮审查补测；+196 未超出估计一倍 |
| `tests/test_update.py` | +30 | +28 | |
| `tests/test_remove.py` | +25 | +10 | |

## 偏差与发现

- **提示通道**：规格要求「旧副本可删」不算「需要你处理」，为此给 `Plan` 加了 `tips`，在 init、update 的文字输出里单列「提示：」。`init --plan --json` 与 `update --dry-run --json` 的字段集合保持不变（design Non-Goals），提示只在文字输出里。
- **README.en**：英文简版没有「出了问题怎么办」与「卸载」两节，只补一句，tasks 4.4 验证文字已同步改写。
- **SKILL.md**：`manual_lint` 一行改为「`next.action` 只有文件与摘要，做法在 `layers`」，与新的 check 第一行一致；不在 tasks 内，属于同一行为的说明同步。
- **范围外发现，未处理**：`rulemason remove` 之后 `CLAUDE.md` 块外留着 `@AGENTS.md`，再 `init` 会报「块外重复导入」。属于 remove 的行为，另开 change 处理。
- **行为变化（发布说明要写）**：ESLint 重复引入基础规则现在会被 check 报出并非 0 退出；同一份 ruff 配置写了 `select` 时只报 select 一条说明（原来另报一条「没有继承」）。
