# Tasks

## 1. 接入日期

- [x] 1.1 `shared.py`：`read_manifest` 校验 `joined`（字符串或 YAML 日期，统一成 `YYYY-MM-DD`，无效抛 `ManifestError`）；新增 `joined_date(root, manifest)`：清单有就用，没有就取 git 里第一次加入 `.rulemason.yaml` 的提交日期，再没有返回 None；`manifest_text` 加 `joined` 参数；验证：`tests/test_shared.py` 覆盖有值、去引号的日期、格式无效、git 推算、没有 git，`uv run pytest tests/test_shared.py` 通过
- [x] 1.2 `init.plan_manifest` 计算 `joined`（已有保留 → git 推算 → 当天），`init` 与 `update` 共用；验证：`tests/test_init.py` 新接入写当天、已有不改，`tests/test_update.py` 老清单补上 git 里的日期，`uv run pytest tests/test_init.py tests/test_update.py` 通过

## 2. check

- [x] 2.1 识别表加「接入日期」（推算时注明「推算」，推算不出写「—」）；`gate_records` 只看日期晚于接入日期的归档，接入后没有归档时经 `Report.notes` 写「接入后尚未归档，无记录可查」；测试里 `_install` 给一个早于测试归档的 `joined`；验证：`tests/test_check.py` 覆盖规格增量的两个新场景与原有五个场景，`--json` 顶层键不变，`uv run pytest tests/test_check.py` 通过
- [x] 2.2 新巡检「主规格写法」：七类问题按类型分组列能力路径；验证：`tests/test_check.py` 每类一个用例，全部符合时写「一致」，没有 `openspec/specs/` 时写「一致」，退出码不变；在本仓库运行 `uv run rulemason check` 这一项是「一致」
- [x] 2.3 新巡检「lint 脚本为占位」，`package.json` 读取抽成共用函数；验证：`tests/test_check.py` 覆盖 `echo`、空、`true`、`exit 0` 报出，`eslint .`、`turbo run lint`、`echo a && eslint .`、没有 lint 脚本不报，`uv run pytest tests/test_check.py` 通过

## 3. skill 与验证

- [x] 3.1 `skills/rulemason/SKILL.md` 日常巡检：检查点记录一条补「只看接入日期之后」；新增「主规格写法」「lint 脚本为占位」两条解读；验证：`uv run pytest tests/test_templates.py` 通过
- [x] 3.2 在一个已接入项目运行 `rulemason update`（不提交）：`joined` 是 git 里第一次加入清单的日期，`rulemason check` 识别表有接入日期、检查点记录与主规格写法两项符合预期；验证：结果写进 `verification.md`，改动还原
- [x] 3.3 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；验证：结果写进 `verification.md`，含与 design 估计行数的对照
