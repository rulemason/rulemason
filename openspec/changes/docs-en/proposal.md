## Why

仓库公开、发布在 PyPI，仓库标签也是英文，但 README、PyPI 简介与 GitHub 仓库简介全是中文。英文读者搜到后看不懂这是什么；装上后又发现命令行输出和规则正文全是中文，事先没有任何提示。

## What Changes

- 新增 `README.en.md`：简短英文版，写这个工具做什么（三件事）、安装、常用命令，开头写明命令行界面与规则正文都是中文。不写版本号与具体操作流程，避免和中文版对不上。
- `README.md` 顶部加 English 链接，用 GitHub 完整网址（PyPI 也渲染这份文件，相对路径在那里会是死链）。
- 新增测试：`README.md`「常用命令」表里的每条命令都必须出现在 `README.en.md` 中，命令表变了而英文版没跟上时测试失败。
- `pyproject.toml` 的 `description` 与 GitHub 仓库简介改为中英并列。GitHub 简介用 `gh repo edit` 修改，执行前先征得用户同意。
- 不做：翻译规则文件、命令行输出与 skill；英文版写完整流程；多语言切换。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：新增「README 提供英文简版」一条 requirement。

## Impact

- 文档：`README.md`、新增 `README.en.md`。
- 包元数据：`pyproject.toml` 的 `description`，随 0.8.8 发布到 PyPI。
- 仓库设置：GitHub 仓库简介，属对外操作。
- 测试：`tests/test_templates.py`。
