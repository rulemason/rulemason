## Why

存量改造建议的第二批（D2、D1、A4），都是 `check` 与 `init` 的小改动：

1. **D2**：巡检「最近归档的检查点记录」只看日期最新那一天的归档。接入后还没归档过新 change 时，最新那天是接入前，于是永远报缺 `verification.md`；skill 又写着「不要补写过去的汇报」，用户只能一直看着这条偏离，或违反 skill 去补写。
2. **D1**：一个接入项目 40 份主规格里只有 12 份通过 `openspec validate --specs --strict`，`rulemason check` 却报「一切一致」；其中 2 份把标题写成了增量格式的 `## ADDED Requirements`，OpenSpec 读出的 requirement 是 0 条，检查点「读主规格判路」时等于看不见。
3. **A4**：一个前端包的 lint 脚本是 `echo "…placeholder"`，CI 一直是绿的，实际什么都没查；`check` 只报了缺 ESLint 配置，没点明脚本是假的。

## What Changes

- **接入日期**：`init` 在 `.rulemason.yaml` 记 `joined`（接入当天，`YYYY-MM-DD`）；已接入、没有这个键的项目，`update` 用 git 里第一次加入 `.rulemason.yaml` 的提交日期补上，没有 git 记录时用当天。已有的值不改。
- **检查点记录只看接入之后**：巡检「最近归档的检查点记录」只看日期晚于接入日期的归档，取其中最新一天；接入后还没有归档时写「接入后尚未归档，无记录可查」。清单没有 `joined` 时 `check` 按同样的 git 办法推算，推算不出来时保持现在的行为。识别表加一行「接入日期」。
- **主规格写法巡检**：`check` 用文本规则逐份检查 `openspec/specs/` 下的主规格，按问题类型分组列出能力名：缺 Purpose、Purpose 是占位（以 TBD 或 TODO 开头）、Purpose 不足 50 字、用了增量格式标题、没有 `## Requirements` 一节、requirement 正文超过 500 字、requirement 没有场景。不调用 `openspec`。
- **lint 脚本占位巡检**：`package.json` 的 `scripts.lint` 是空、只有 `echo …`、`true`、`:` 或 `exit 0` 时，列出文件与原文。
- 两项新巡检和现有巡检一样不影响退出码与下一步。skill 日常巡检一节补两条解读。
- 不做：调用 `openspec validate`；归档检查点里补 Purpose 的步骤；`check` 跑任何 lint；判断 lint 脚本是否「真的有用」（只认上面几种占位写法）；改 `check --json` 的顶层键。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：修改「巡检核对最近归档的检查点记录」（只看接入日期之后）；新增「清单记录接入日期」「巡检主规格写法」「巡检 lint 脚本占位」。

## Impact

- 代码：`src/rulemason/shared.py`（接入日期的读、校验与推算）、`init.py`（清单写入 `joined`）、`check.py`（识别表一行、检查点记录按接入日期筛、两项新巡检）；`skills/rulemason/SKILL.md` 巡检解读两条；对应测试。
- 接入项目：下次 `rulemason update` 时 `.rulemason.yaml` 多一行 `joined`，随升级一起提交；之后巡检不再报接入前的归档。
- 已有的巡检项只会多报（主规格、lint 占位），不会让 `check` 非 0。
