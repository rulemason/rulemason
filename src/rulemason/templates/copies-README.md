# .rulemason/：生成文件，勿手改

本目录由 `rulemason init` / `rulemason update` 生成，内容是 rulemason 共享规则正文（`rules/`）与 lint 基础配置（`lint/`）的只读副本，随项目提交，让克隆项目的人、云端 agent 与 CI 不装 rulemason 也能读到。

- 要改规矩：到 rulemason 仓库修改并发布新版本，再在本项目运行 `rulemason update`。
- 每个文件的校验值记在项目根的 `.rulemason.yaml`；手改会被 `rulemason check` 报告并以非 0 退出，`rulemason update` 会恢复原样。
