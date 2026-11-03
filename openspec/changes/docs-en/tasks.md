## 1. 文档与元数据

- [x] 1.1 新增 `README.en.md`（开头说明界面与规则是中文、三件事、安装、常用命令、链回中文 README）；`README.md` 顶部加 English 完整网址链接；验证：两份文件中的链接都指向 GitHub 完整网址，在 GitHub 上预览可点击
- [x] 1.2 `pyproject.toml` 的 `description` 改为中英并列；验证：`uv build` 后包元数据的 Summary 为新简介
- [x] 1.3 测试：`README.md` 常用命令表里的每条命令都出现在 `README.en.md` 中，且 English 链接是完整网址；验证：删掉英文版一条命令时测试失败，恢复后通过

## 2. 对外与验证

- [x] 2.1 征得用户同意后用 `gh repo edit rulemason/rulemason --description …` 改 GitHub 仓库简介；验证：`gh repo view --json description` 显示新简介，改前与改后的原文写进 `verification.md`
- [x] 2.2 按 workflow gates 完成独立审查、ruff、pytest（无代码逻辑改动，跳过精简）；验证：写进 `verification.md`

## Workflow follow-up

- 发版 0.8.8：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送，按「归档」一节归档，打 tag；发布后确认 PyPI 页面的简介与 English 链接。
