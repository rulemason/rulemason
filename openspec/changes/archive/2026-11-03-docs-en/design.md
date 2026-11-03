## Context

见 proposal.md 的 Why。现状：

- `README.md` 共 169 行、13 节，`pyproject.toml` 的 `readme = "README.md"`，PyPI 页面渲染的就是这份文件。
- `README.md` 的「常用命令」是一张两列表格，命令写在反引号里，共 7 条：`rulemason init`、`rulemason update`、`rulemason check`、`rulemason key`、`rulemason remove`、`rulemason judge --change 功能名`、`/rulemason`。
- 启动画面的常用命令（`banner.COMMANDS`）是这张表的子集。

## Goals / Non-Goals

**Goals:**
- 英文读者装之前就知道这是什么、界面是什么语言。
- 中文 README 的常用命令变化时，英文版不会悄悄落后。

**Non-Goals:**
- 不保证两份 README 逐段对应，英文版只写最基本的部分。

## Decisions

### D1 英文版只写四部分，不写版本号与流程

`README.en.md` 只写四部分：
- 开头一段：工具是什么，并说明界面与规则是中文；
- What it does：三件事；
- Install；
- Common commands：命令表，用英文说明用途；

最后链回中文 README 看完整说明。
否决：全文翻译。169 行要两边同步维护，每改一处中文都得记得改英文，最先过时的一定是英文版。

### D2 同步测试以中文 README 的命令表为准

测试从 `README.md` 的「## 常用命令」到下一个「## 」之间，取出所有反引号里的命令，逐条断言在 `README.en.md` 中出现。`judge --change 功能名` 这类带中文占位的命令，只比较占位前的部分（`rulemason judge --change`）。
否决：以 `banner.COMMANDS` 为准。它不含 `remove`、`judge`、`/rulemason`，README 表里有而英文版漏掉时测不出来。

### D3 链接用完整网址

`README.md` 顶部写 `[English](https://github.com/rulemason/rulemason/blob/main/README.en.md)`。
否决：相对路径 `README.en.md`。在 GitHub 上能用，在 PyPI 页面上会变成死链。

### D4 简介中英并列，英文在前

`description` 改为 `Shared rules and checkpoints for AI coding tools（给 AI 编码工具的共享规则与检查点）…`，保留原来的中文要点，只在前面加英文。GitHub 仓库简介用同一句。改 GitHub 简介属于对外操作，apply 时先问用户再运行 `gh repo edit`。
否决：只改 README、不改简介。英文搜索结果里显示的是简介，读者进不到 README。

## Risks / Trade-offs

- [英文版描述的行为与实际不符] → 英文版不写流程与输出细节，只写三件事、安装与命令；命令清单由测试守住。
- [GitHub 简介的修改不经过 PR 记录] → 在 `verification.md` 里写下改前与改后的原文。

## Migration Plan

1. 实现并通过 ruff 与测试，征得同意后修改 GitHub 仓库简介。
2. 发版 0.8.8，PyPI 简介随之更新；接入项目无需任何操作。
3. 回滚：把 `README.md`、`pyproject.toml` 改回原样并删除 `README.en.md`，再用 `gh repo edit` 恢复原来的仓库简介（原文记录在 `verification.md` 里）。

## 文件与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `README.en.md` | 新增 | +40 |
| `README.md` | 顶部 English 链接 | +2 |
| `pyproject.toml` | `description` | ±1 |
| `tests/test_templates.py` | 命令同步测试、链接为完整网址 | +20 |
