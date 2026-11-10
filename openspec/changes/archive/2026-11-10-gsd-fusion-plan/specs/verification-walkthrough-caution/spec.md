# Spec Delta

## Purpose

定义验证走查类交接文的共享指导边界与可选结构检查：只分发自研原则与种子预设，不自动扫仓，不把结构命中写成质量或业务验证通过。

## ADDED Requirements

### Requirement: 验证走查指导随产品产物规矩分发
本仓库 SHALL 在自研 `rules/product-artifact-caution.md`（或经确认的等价必复制规矩）中写入验证走查原则：先写可观察期望、再请人确认、逐条记录差距；禁止编造「已测/已通过」。MUST 归因行为启发来源为固定 URL 与 commit，MUST NOT 嵌入第三方工作流或模板全文。MUST NOT 列入默认判断红线。

#### Scenario: update 后可见走查原则
- **WHEN** 已接入项目运行 `rulemason update`
- **THEN** 分发的产品产物规矩副本含验证走查原则与归因说明

### Requirement: 走查结构预设只经 result-check 显式调用
确定性走查结构检查 SHALL 仅在调用方运行 `rulemason result-check` 且选用 `--preset verification-walkthrough.hint` 或 `verification-walkthrough.strict`（或等价 requirements）时执行。`init`/`update`/`check` MUST NOT 因缺走查小节而自动扫描仓库或单独因此失败。

#### Scenario: init 不扫走查文件
- **WHEN** 项目运行 `rulemason init` 或 `update`
- **THEN** 工具只分发规矩与缺失种子，不遍历仓库寻找 UAT/verification 文件做结构检查
