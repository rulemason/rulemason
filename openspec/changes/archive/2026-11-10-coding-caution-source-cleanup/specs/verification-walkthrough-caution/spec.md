# Spec Delta

## MODIFIED Requirements

### Requirement: 验证走查指导随产品产物规矩分发
本仓库 SHALL 在自研 `rules/product-artifact-caution.md`（或经确认的等价必复制规矩）中写入验证走查原则：先写可观察期望、再请人确认、逐条记录差距；禁止编造「已测/已通过」。MUST NOT 在规矩正文中写第三方仓库名、URL 或 commit，MUST NOT 嵌入第三方工作流或模板全文。MUST NOT 列入默认判断红线。

#### Scenario: update 后可见走查原则
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** 分发的产品产物规矩副本含验证走查原则，且不含第三方仓库名、URL 或 commit
