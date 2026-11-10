@AGENTS.md
@.rulemason/rules/code-style.md
@.rulemason/rules/python.md
@.rulemason/rules/react.md
@.rulemason/rules/cjk-typography.md
@.rulemason/rules/result-check-contracts.md
@.rulemason/rules/prose-hygiene.md
@.rulemason/rules/agent-coding-caution.md
@.rulemason/rules/product-artifact-caution.md
@.rulemason/rules/workflow-gates.md

Claude Code 下，workflow gates 的「自动精简」一步用 `/simplify` 执行，替换手工精简：
- 只在本次 diff 改了代码逻辑时调用；只改文档、配置或生成副本时跳过，汇报写「无代码改动，跳过精简」。
- 只采纳行为保持的修改：性能优化类修改，以及会改变需求、外部行为或 API 的修改要撤回，并在汇报中说明。
- `/simplify` 不可用时，按 `.rulemason/rules/workflow-gates.md` 手工精简。
- 之后的独立只读审查、ruff 与测试照旧。
