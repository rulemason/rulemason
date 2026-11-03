## 1. 实现

- [x] 1.1 `init.py` 新增 `_links_only`，`readme_intro` 跳过只有链接与分隔符的段落；验证：`test_agents_intro_is_prefilled_from_readme` 新增用例全部通过——「中文 · [English](…)」与「[English](…) · 中文」后接正文时取正文、导航行被跳过、正文带链接照常取、「见 [文档](…)」被跳过
- [x] 1.2 用本仓库 README 调用 `readme_intro`；验证：结果以「给 AI 编码工具」开头，不含「English」

## 2. 验证

- [x] 2.1 按 workflow gates 完成精简、独立审查、ruff、pytest；验证：写进 `verification.md`

## Workflow follow-up

- 发版：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送，按「归档」一节归档，打 tag。
