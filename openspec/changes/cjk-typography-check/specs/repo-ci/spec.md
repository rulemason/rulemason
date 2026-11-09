## ADDED Requirements

### Requirement: 本仓 CI 对约定中文文件跑排版检查
对 `main` 的 PR 与推送，名为 `test` 的检查在 ruff 与既有测试之外，SHALL 对约定文件跑 `cjk_typography` 确定性检查（经 pytest 或同 job 内等价调用）。约定文件 MUST 至少含仓库根 `README.md` 与 `rules/**/*.md`；MUST NOT 将 `README.en.md` 或 `openspec/changes/archive/` 纳入该门禁。喂数方式 MUST 为按文件构造运行记录（`text` 为文件正文），本地确定性、不调模型。任一文排版失败时 `test` MUST 失败。本仓该检查所用 requirements 的 allowlist MUST 初始为空（或不写该键），仅在有证据的例外出现后按需追加。

#### Scenario: README 引入全角数字
- **WHEN** PR 修改 `README.md` 写入全角数字且启用的规则含 fullwidth_digit
- **THEN** 名为 `test` 的检查失败，并能看到规则短名与文件路径

#### Scenario: 仅改英文 README
- **WHEN** PR 只改 `README.en.md` 的英文文句
- **THEN** 不因该英文文件触发中文排版门禁失败

#### Scenario: 规则文件合规
- **WHEN** `rules/` 下 Markdown 均通过首批 `cjk_typography` 规则
- **THEN** 排版相关断言通过，不单独阻挡 ruff 与其余测试已通过的 `test` job

#### Scenario: 初始无预置白名单
- **WHEN** 本仓 CI 所用 `cjk_typography` requirements 尚未登记任何例外
- **THEN** allowlist 为空或不出现，命中规则不得被预置品牌表静默豁免
