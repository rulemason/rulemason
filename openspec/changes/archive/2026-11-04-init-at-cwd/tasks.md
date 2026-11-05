# Tasks

## 1. 找项目根

- [x] 1.1 `shared.find_root`：往上找清单、不越过 git 仓库根，找不到返回 None；新增 `repo_root(start)` 返回所在 git 仓库根（`.git` 是目录或文件都算），不在 git 里返回 None；命令行没有清单时用当前目录；judge 的 `root()` 没有清单时用 `repo_root`（仍要求有 `openspec/`）；验证：`tests/test_shared.py` 改写 `test_find_root_stops_at_nested_repo`、`test_find_root_stops_at_git_file` 为返回 None，新增 `repo_root` 的三个用例（目录、`.git` 文件、不在 git 里），`uv run pytest tests/test_shared.py` 通过；judge 现有用例不改仍通过

## 2. 写明仓库根

- [x] 2.1 init：项目根与仓库根不同时，计划的「提示：」加一条「当前目录在 git 仓库 <仓库根> 里；要接入整个仓库，到仓库根运行，或运行 rulemason init <仓库根>」，交互摘要、`--plan` 与 `--yes` 结尾都有；`--plan --json` 字段集合不变；验证：`tests/test_init.py` 把 `test_init_in_subdirectory_uses_repo_root` 改写为在子目录接入、仓库根无新文件、输出含这条提示；新增「工作区仓库下的新目录」用例（替身 openspec 也写在新目录、工作区无新文件）；`--plan --json` 字段集合用例仍通过
- [x] 2.2 check 与 update：未接入且项目根与仓库根不同时，check 识别表在「项目根」后另起一行「所在 git 仓库根」，update 的「先运行 rulemason init」后补与 init 相同的说明；验证：`tests/test_check.py`、`tests/test_update.py` 各新增一个未接入子目录的用例；已接入项目在子目录运行 check 的结果与在根目录相同（`test_check_in_subdirectory_matches_root` 仍通过）

## 3. 文档与收尾

- [x] 3.1 README「第一次接入」一句改为「在要接入的目录运行」并补 monorepo 的说法，排障表「接入：运行 rulemason init」一行同步；README.en（简版，没有这两处）在命令表后补一段同样的说法；验证：README 改两处、README.en 补一段，中英命令表同步测试通过
- [x] 3.2 按 workflow gates 完成精简、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙的根目录与一个子目录运行开发版 `rulemason check`，确认结果与 0.8.14 相同；验证：结果与 design 行数对照写进 `verification.md`

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README CI 钉版本，推送、归档、打 tag；发布说明写明「找不到 .rulemason.yaml 时在当前目录接入，与 openspec init 一致」及 monorepo 用户的做法。
- Notion 统一入口第 3 节同步；第 71 篇记下工作区仓库的问题已由此解决。
