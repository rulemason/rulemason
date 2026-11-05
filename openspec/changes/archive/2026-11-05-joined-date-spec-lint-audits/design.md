# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- `gate_records` 取 `openspec/changes/archive/` 里日期前缀最大的那一天，检查当天每个 change 的 `verification.md`（`src/rulemason/check.py:268`）；结果作为巡检「最近归档的检查点记录」加入 `report.findings`（`check.py:1032`）。巡检项不影响退出码（`check.py:1086` `exit_code` 只看「接入」开头的层）。
- `render` 把空的巡检项写成「一致」（`check.py` `render` 的「## 巡检」循环）；`--json` 的 `findings` 是 `巡检项 → 偏离列表`，`facts` 是识别表（`check.py` `to_json`），顶层键由测试钉住（`tests/test_check.py:906`）。
- 清单由 `shared.manifest_text` 生成，只管 `version`、`rulemason`、`tools`、`files` 四个键，其余键原样保留（`src/rulemason/shared.py:268`）；`init` 与 `update` 都经 `init.plan_manifest` 写清单（`src/rulemason/init.py` `plan_manifest`，`src/rulemason/update.py:48`）。`read_manifest` 对 `rulemason` 版本格式不对时抛 `ManifestError`（`shared.py:261`），`check` 把它报成 `fix_manifest`（`check.py:245`、`:1068`）。
- 测试照 init 的结果手写清单：`tests/test_check.py:45` `_install` 调 `manifest_text`；现有检查点记录的测试用 `2026-10-01`、`2026-11-0x` 这类过去的日期归档（`tests/test_check.py` `test_latest_archive_gate_records`）。
- OpenSpec 1.16.0 对主规格的严格校验：Purpose 少于 50 字（`MIN_PURPOSE_LENGTH`）、以 TBD 或 TODO 开头算占位、requirement 正文超过 500 字（`MAX_REQUIREMENT_TEXT_LENGTH`）、requirement 没有场景，都报出（`@fission-ai/openspec/dist/core/validation/constants.js:6`、`:9`，`validator.js:723-758`）。归档生成新能力时 Purpose 占位以「TBD - created by archiving change」开头（`specs-apply.js` `buildSpecSkeleton`）。
- 前端目录识别读 `package.json` 用 `json.loads`，读不出时抛 `ConfigError`（`check.py:213` `package_dirs`）。
- 建议页的数字（40 份主规格 12 份通过、2 份增量标题；lint 脚本是 `echo` 占位）来自一个接入项目，本机未复现。

## Goals / Non-Goals

**Goals:**
- 接入前的归档不再让巡检永远报缺，又不鼓励补写过去的汇报。
- 读主规格判路时会「看不见」的写法能被 `check` 报出来。
- 假的 lint 脚本能被点名。

**Non-Goals:**
- 不让 `check` 运行 `openspec`、ESLint 或任何外部命令（git 只读查询除外，已有先例）。
- 不改 `check --json` 的顶层键，不改退出码规则。

## Decisions

1. **接入日期存在清单的 `joined` 键里，值是加引号的 `YYYY-MM-DD` 字符串；`init` 与 `update` 共用 `plan_manifest` 计算：已有就保留，没有就取 git 里第一次加入 `.rulemason.yaml` 的提交日期（`git log --diff-filter=A --format=%cs -- .rulemason.yaml` 的最后一行），再没有就取当天。** `manifest_text` 多一个 `joined` 参数。否决每次 `check` 都从 git 推算、不写清单：没有 git 或浅克隆的 CI 里推算不出来，且接入日期是事实，应该随项目提交。否决老项目升级时一律记当天：会把接入后、升级前那段时间的归档也排除掉。`read_manifest` 接受字符串或 YAML 解析出的日期（用户手改去掉引号时），统一成字符串后校验，格式不对抛 `ManifestError`，和 `rulemason` 版本格式无效同一处理。
2. **只看日期严格晚于接入日期的归档。** 接入当天的归档分不清是接入前还是接入后，按接入前处理：宁可漏查一天，也不再出现「永远报缺、又不让补写」。否决「当天及以后」：接入当天先归档、后接入的项目会重现原问题。否决按提交时间比较到秒：归档目录名只有日期。
3. **「接入后尚未归档」写在巡检那一行，替代「一致」，偏离列表仍为空；接入日期另进识别表。** `Report` 加一个 `notes`（巡检项 → 替代「一致」的说明），只有 `render` 用它；`--json` 的 `findings` 里这一项仍是空列表，日期从 `facts` 的「接入日期」读。否决把这句话放进偏离列表：skill 会把它当问题去处理。否决给 `--json` 加顶层键：要改 `schema` 版本与测试钉住的键集合。
4. **`check` 没读到 `joined` 时按决策 1 的 git 办法推算，识别表注明「推算」；推算不出来时不按日期筛，保持现在的行为。** 否决推算不出来就当成今天：会把所有归档都排除，等于关掉这项检查。
5. **主规格写法用逐行文本规则检查，按问题类型分组，每类一行列出能力路径。** 规则与 OpenSpec 严格校验一一对应（50 字、500 字、TBD/TODO、场景），再加两条 OpenSpec 解析层面的：增量格式标题、没有 `## Requirements`。requirement 正文取 `### Requirement:` 标题到第一个 `#### Scenario:` 之间的文字去掉首尾空白。否决调用 `openspec validate --specs --strict --json`：`check` 要求不依赖外部命令、CI 里不一定装了 OpenSpec。否决按文件逐条列：40 份规格时会刷屏，按类型分组更好读。
6. **lint 占位只认一条命令的几种写法：空、`true`、`:`、`exit 0`、只有 `echo …`；含 `&&`、`;`、`|` 的不算。** 否决判断「脚本里有没有 eslint」：`turbo run lint`、`next lint` 这类间接调用都是真的。`package.json` 读不出时沿用 `package_dirs` 的 `ConfigError`，抽出共用的读取函数。

## Risks / Trade-offs

- [`update` 让所有老项目的清单多一行，`check` 报副本或清单有改动] → 这是一次正常升级的产出，skill 已要求升级产出一起提交；发布说明写明。
- [git 推算出的日期是迁移日期而不是最早接入日期（从 rulekit 迁过来的项目）] → 迁移前的归档本来就按旧规矩写的，从迁移日算起正合适；用户可以手改 `joined`。
- [接入当天的归档被跳过] → 只差一天，下一次归档就会被检查；场景里写明。
- [主规格文本规则与 OpenSpec 将来的校验不一致] → 规则数字取自 OpenSpec 常量，Context 写明出处；对不上时以 `openspec validate` 为准，巡检只是提示。
- [测试里过去日期的归档被接入日期筛掉] → `_install` 写清单时给一个早于所有测试归档的 `joined`，单独测筛选逻辑。

## Migration Plan

1. 改 `shared.py`、`init.py`、`check.py`、`SKILL.md`，补测试，跑 ruff 与测试。
2. 在一个已接入项目运行 `rulemason update`，看 `joined` 取到的是 git 里第一次加入清单的日期；`rulemason check` 的识别表与巡检符合预期；不提交。
3. 发版，发布说明写明清单新增 `joined`、两项新巡检。

回滚：`uv tool install rulemason==<上一版>`；旧版本读到多出的 `joined` 键会原样保留（`manifest_text` 保留未知键），不会报错。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/shared.py` | `joined` 校验、`joined_date()` 推算、`manifest_text` 加参数 | +25 / −2 |
| `src/rulemason/init.py` | `plan_manifest` 计算 `joined` | +4 / −1 |
| `src/rulemason/check.py` | 识别表一行；`gate_records` 按日期筛并给说明；`spec_writing()`、`lint_placeholders()` 两项巡检；`Report.notes` 与 `render`；`package.json` 读取抽成函数 | +80 / −8 |
| `skills/rulemason/SKILL.md` | 日常巡检两条解读，检查点记录一条补半句 | +3 / −1 |
| `tests/test_shared.py` | `joined` 校验与推算 | +30 |
| `tests/test_init.py`、`tests/test_update.py` | 新接入写日期、老项目补日期、已有不改 | +40 |
| `tests/test_check.py` | 接入日期筛选与说明、识别表、主规格七类问题、lint 占位 | +100 / −3 |
