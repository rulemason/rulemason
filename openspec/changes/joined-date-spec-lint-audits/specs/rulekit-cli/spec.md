## MODIFIED Requirements

### Requirement: 巡检核对最近归档的检查点记录

`rulemason check` 的巡检 SHALL 有一项「最近归档的检查点记录」：在 `openspec/changes/archive/` 里取日期前缀晚于接入日期的归档，再取其中日期最新的那一天归档的全部 change，逐个检查目录里有没有 `verification.md`，以及文件里是否同时写到审查（「审查」或 review）与测试（「测试」或 test）。缺文件或缺其中一项时 SHALL 列出 change 名与缺什么。接入日期之后还没有归档时 SHALL 写「接入后尚未归档，无记录可查」；接入日期推算不出来时 SHALL 不按日期筛。这一项 MUST NOT 影响退出码与下一步；没有已归档 change 时写「一致」。更早的归档 MUST NOT 被检查。

#### Scenario: 最近一次归档带完整汇报
- **WHEN** 最新归档的 change 有 `verification.md`，其中写了独立审查两轮的结果与 pytest 的结果
- **THEN** 这一项写「一致」

#### Scenario: 最近一次归档没有汇报
- **WHEN** 最新归档的是 `2026-11-01-migrate-x`，目录里没有 `verification.md`
- **THEN** 这一项列出「2026-11-01-migrate-x：没有 verification.md」，退出码与下一步不变

#### Scenario: 汇报缺审查
- **WHEN** 最新归档的 change 有 `verification.md`，只写了测试结果，没有提到审查
- **THEN** 这一项列出该 change 缺审查记录

#### Scenario: 同一天归档了两个
- **WHEN** 最新的日期下归档了两个 change，其中一个没有 `verification.md`
- **THEN** 只列出缺的那一个；更早日期的归档即使没有汇报也不列出

#### Scenario: 表格写法的汇报
- **WHEN** `verification.md` 没有小节标题，只有一张写着「独立审查第一轮」「测试：44 项通过」的表格
- **THEN** 这一项写「一致」

#### Scenario: 接入后还没归档
- **WHEN** 清单记录接入日期 `2026-11-04`，已归档的 change 都在 `2026-11-03` 及以前，其中最新的没有 `verification.md`
- **THEN** 这一项写「接入后尚未归档，无记录可查」，不列出接入前的归档，退出码与下一步不变

#### Scenario: 接入当天归档的不算
- **WHEN** 清单记录接入日期 `2026-11-04`，有一个 `2026-11-04-x` 的归档没有 `verification.md`，另有一个 `2026-11-06-y` 的归档带完整汇报
- **THEN** 只检查 `2026-11-06-y`，这一项写「一致」

## ADDED Requirements

### Requirement: 清单记录接入日期

`rulemason init` 写入的 `.rulemason.yaml` SHALL 有键 `joined`，值为接入当天的 `YYYY-MM-DD`。已有 `joined` 时 `init` 与 `update` MUST NOT 改它；清单没有 `joined` 时，`update` SHALL 补上：取 git 里第一次加入 `.rulemason.yaml` 的提交日期，没有 git 或没有这条提交时取当天。`joined` 不是 `YYYY-MM-DD` 时 SHALL 按清单无效报出。`check` 的识别表 SHALL 有一行「接入日期」；清单没有 `joined` 时按同样的 git 办法推算并注明「推算」，推算不出来时写「—」。

#### Scenario: 新接入
- **WHEN** 在 2026-11-05 对一个项目运行 `rulemason init --tools claude --yes`
- **THEN** `.rulemason.yaml` 有 `joined: '2026-11-05'`，识别表写「接入日期：2026-11-05」

#### Scenario: 老项目升级时补上
- **WHEN** 项目在 2026-11-02 的提交里加入了 `.rulemason.yaml`、清单没有 `joined`，在 2026-11-06 运行 `rulemason update --yes`
- **THEN** 清单补上 `joined: '2026-11-02'`，不是 `2026-11-06`

#### Scenario: 已有日期不改
- **WHEN** 清单已有 `joined: '2026-10-30'`，再运行 `rulemason init` 或 `rulemason update`
- **THEN** `joined` 仍是 `2026-10-30`

#### Scenario: 日期写坏了
- **WHEN** 用户把清单里的 `joined` 改成 `上周`
- **THEN** `check` 按清单无效报出，写明 `joined` 格式无效

### Requirement: 巡检主规格写法

`rulemason check` 的巡检 SHALL 有一项「主规格写法」：用文本规则检查 `openspec/specs/` 下每份 `spec.md`，按问题类型分组列出能力路径：缺 Purpose 或 Purpose 为空、Purpose 是占位（以 TBD 或 TODO 开头）、Purpose 不足 50 字、用了增量格式标题（`## ADDED|MODIFIED|REMOVED|RENAMED Requirements`）、没有 `## Requirements` 一节、requirement 正文超过 500 字、requirement 没有场景。MUST NOT 调用 `openspec` 命令。这一项 MUST NOT 影响退出码与下一步；没有 `openspec/specs/` 或全部符合时写「一致」。

#### Scenario: 增量格式标题
- **WHEN** `openspec/specs/order-refund/spec.md` 的标题写成 `## ADDED Requirements`
- **THEN** 这一项列出「用了增量格式标题：order-refund」，退出码与下一步不变

#### Scenario: 归档留下的占位
- **WHEN** 两份主规格的 Purpose 是归档时生成的「TBD - created by archiving change …」
- **THEN** 这一项在「Purpose 是占位」后列出这两个能力路径

#### Scenario: 全部符合
- **WHEN** 每份主规格都有 50 字以上的 Purpose、`## Requirements` 一节，每条 requirement 不超过 500 字且至少一个场景
- **THEN** 这一项写「一致」

### Requirement: 巡检 lint 脚本占位

`rulemason check` 的巡检 SHALL 有一项「lint 脚本为占位」：项目文件里每个 `package.json` 的 `scripts.lint` 是空串、`true`、`:`、`exit 0`，或只有一条 `echo` 命令时，SHALL 列出该 `package.json` 的路径与脚本原文。没有 `lint` 脚本的 `package.json` MUST NOT 报出。这一项 MUST NOT 影响退出码与下一步。

#### Scenario: echo 占位
- **WHEN** `packages/ui/package.json` 的 `scripts.lint` 是 `echo "lint placeholder"`
- **THEN** 这一项列出 `packages/ui/package.json` 与原文，退出码与下一步不变

#### Scenario: 真的 lint
- **WHEN** `scripts.lint` 是 `eslint .` 或 `turbo run lint`
- **THEN** 不报出
