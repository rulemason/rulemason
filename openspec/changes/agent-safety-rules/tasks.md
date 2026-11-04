# Tasks

## 1. 共享规矩

- [x] 1.1 `rules/code-style.md` 在「## 九条之外」之后新增「## 外部操作与凭据」：三级（读，不含密钥值与个人数据 / 写，含发布、发送这类收不回的操作，逐次授权 / 删除或作废只给入口与核对点，说不清会不会销毁的也算），项目指令另有写明的从项目、「有写权限不等于可以写」、授权只管这一次；密钥不让用户贴进对话（写进本机环境文件时确认不会被提交）、不打印值、出现过按泄露处理、一个用途一把、最小权限、预发与生产分开；第一行说明补「与外部操作纪律」；整节不超过 15 行，不出现任何公司、平台账号或事件细节；验证：`tests/test_templates.py` 新增用例断言该节存在且含三级与密钥四点，`uv run pytest tests/test_templates.py` 通过
- [x] 1.2 九条第 8 条补半句：失败时静默改走另一条路径（换接口、退回缓存或旧数据）来掩盖失败也不行，要降级由最外层决定并让人知道；验证：同一用例断言第 8 条含「静默改走另一条路径」，九条仍是 9 条

## 2. skill：常见红线候选

- [x] 2.1 `skills/rulemason/SKILL.md` 补项目信息第 2 步加常见红线候选：有数据库访问（ORM、迁移目录、数据库连接配置）、有部署脚本或 CI 发布流程、有区分生产环境的配置时各提一条，出处写「rulemason 常见红线（触发文件）」，没有对应的东西不提，仍逐条由用户确认；「不可违反」一节的出处列表补上「rulemason 常见红线」；验证：`tests/test_templates.py` 断言 skill 含三类触发条件、三条候选原文与「rulemason 常见红线」

## 3. 产物写法基础版

- [x] 3.1 `openspec-base/artifact-rules.yaml` 的 design 新增「Context 里的关键事实注明出处（文件与行，或可复现的命令），没有核实的标「未核实」」；本仓库 `openspec/config.yaml` 的 `rules.design` 同步追加同一句；验证：`test_artifact_base_limits` 补断言新条目，对本仓库运行开发版 `rulemason check` 不报「产物写法与基础版的差异」
- [x] 3.2 对一个只有旧基础版 rules 的临时项目运行开发版 `rulemason update --dry-run` 与 `rulemason update --yes`；验证：补齐计划列出 `openspec/config.yaml`，`rulemason check` 报出缺少的 design 新条目，写入后该条在项目 design 列表末尾，其余文字逐字不变，再运行 `rulemason check` 不报差异

## 4. 文档与收尾

- [x] 4.1 README 与 README.en「规则」一句补碰外部平台与密钥时的纪律（三级与密钥不经过对话）；验证：两份 README 各补一处，中英命令表同步测试通过
- [x] 4.2 按 workflow gates 完成精简（无代码逻辑改动时跳过并写明）、独立审查、`uv run ruff check .`、`uv run pytest`；在项目甲、乙、丙运行开发版 `rulemason update --dry-run`；验证：三个项目只刷新规则与 skill 副本、`.rulemason.yaml`，并列出 design 新条目的补齐；结果与 design 行数对照写进 `verification.md`

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README CI 钉版本，推送、归档、打 tag；发布说明写明新增「外部操作与凭据」一节、第 8 条措辞、常见红线候选与 design 新条目，以及升级后 `rulemason update --yes` 追加 design 条目。
- 接入项目运行 `uv tool upgrade rulemason`、`rulemason update`、`rulemason update --yes`，提交方式同前。
