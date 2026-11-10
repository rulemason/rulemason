共享正文是 rulemason 生成的只读副本，勿手改；要改到 rulemason 仓库修改，再运行 `rulemason update`：

- `.rulemason/rules/code-style.md`：所有语言通用原则
- `.rulemason/rules/python.md`：仅在处理 Python 代码时阅读
- `.rulemason/rules/react.md`：仅在处理 React / TSX 代码时阅读
- `.rulemason/rules/cjk-typography.md`：写中文文档、方案、规格时阅读
- `.rulemason/rules/result-check-contracts.md`：改结构化输出或 result-check 要求时阅读
- `.rulemason/rules/prose-hygiene.md`：写给人读的文案时阅读；检查默认 hint（`result-check --preset hint`），严格门禁用 `--preset strict`
- `.rulemason/rules/agent-coding-caution.md`：写码/改码时阅读（过程指导，非自动禁词检测）
- `.rulemason/rules/product-artifact-caution.md`：写工程交接用的产品产物时阅读；结构检查用 `--preset product-artifact.hint`（默认提示）/ `product-artifact.strict`（显式门禁）；验证走查结构用 `--preset verification-walkthrough.hint` / `verification-walkthrough.strict`；init/update 只分发不扫仓

开始相关代码工作前，读取并遵守适用的共享规则。
