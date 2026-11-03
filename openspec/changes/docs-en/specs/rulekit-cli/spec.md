## ADDED Requirements

### Requirement: README 提供英文简版

仓库根目录 SHALL 有 `README.en.md`：用英文写明工具做什么、安装方法与常用命令，开头 MUST 说明命令行界面与规则正文都是中文。`README.md` 顶部 SHALL 有指向它的链接，链接 MUST 用 GitHub 完整网址，使其在 PyPI 页面上同样可用。`README.md`「常用命令」表中的每条命令 MUST 出现在 `README.en.md` 中。包简介 SHALL 中英并列。

#### Scenario: 在 PyPI 页面点 English
- **WHEN** 读者在 PyPI 的 rulemason 页面点 README 顶部的 English 链接
- **THEN** 打开 GitHub 上的 `README.en.md`，而不是 PyPI 上的死链

#### Scenario: 英文读者装之前就知道界面是中文
- **WHEN** 英文读者读 `README.en.md`
- **THEN** 第一屏就读到命令行输出与规则正文是中文的说明

#### Scenario: 新增常用命令后忘了改英文版
- **WHEN** `README.md` 的常用命令表新增 `rulemason foo`，`README.en.md` 没有提到它
- **THEN** 测试失败，指出缺少 `rulemason foo`
