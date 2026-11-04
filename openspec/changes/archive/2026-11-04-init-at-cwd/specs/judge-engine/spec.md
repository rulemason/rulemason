## MODIFIED Requirements

### Requirement: 命令在项目根目录运行

命令 `rulemason judge` SHALL 在任一接入项目内运行，这样确定项目根：与 `init`、`update`、`check` 一样从当前目录往上找最近的 `.rulemason.yaml`，不越过所在 git 仓库的根目录；找不到时以 git 仓库根为项目根（`init` 等命令找不到时用当前目录，judge 要在未接入 rulemason 的仓库子目录里也找到 `openspec/`）。引擎读取该项目根下的 `openspec/`。参数与原 `jev-judge` 一致：`--change <name>` 依次在 `openspec/changes/<name>`、`openspec/changes/archive/<name>`、`openspec/changes/archive/` 下唯一名为 `YYYY-MM-DD-<name>` 的目录中查找产物（只认日期前缀加完整名称；匹配到多个时列出并以非 0 退出），`--copy` 审相对主分支新增或修改的界面文案，`--lint-only` 只跑正则检查不联网，`--dry-run` 打印将要发送的请求而不发送。参数 SHALL 只在引擎里定义一处，`rulemason` 命令原样转交。

#### Scenario: 在子目录运行
- **WHEN** 在项目甲的 `api/` 目录下运行 `rulemason judge --change adopt-shared-rules`
- **THEN** 引擎以项目甲仓库根为项目根，审 `openspec/changes/adopt-shared-rules` 下的产物

#### Scenario: 仓库里的子项目
- **WHEN** 一个仓库的 `packages/web/` 自己有 `.rulemason.yaml` 与 `openspec/`，在 `packages/web/src/` 下运行 `rulemason judge --change x --lint-only`
- **THEN** 引擎以 `packages/web/` 为项目根，审它自己的 `openspec/changes/x`

#### Scenario: 不在 git 仓库里
- **WHEN** 在一个不属于任何 git 仓库的目录运行
- **THEN** 以非 0 退出码报错，说明需在接入项目内运行 `rulemason judge`

#### Scenario: 审已归档的 change
- **WHEN** 在项目内运行 `rulemason judge --change adopt-rulekit-cli --lint-only`，该 change 已归档为 `archive/2026-11-01-adopt-rulekit-cli`
- **THEN** 引擎审查该归档目录下的产物，不报 change 不存在

#### Scenario: 帮助里的命令名
- **WHEN** 运行 `rulemason judge --help`
- **THEN** 用法行写 `rulemason judge`，列出 `--change`、`--copy`、`--lint-only`、`--dry-run`
