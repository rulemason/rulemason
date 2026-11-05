## ADDED Requirements

### Requirement: 放项目的文件夹给出提示

项目根识别不出语言、且列项目文件时至少有一个子目录因「另一个仓库」或「另一个 rulemason 项目」被跳过时，`init` 的计划 SHALL 在「提示」里加一行，`check` 的识别表 SHALL 加一行「提示」，内容相同：写明被跳过的这些项目，说明这里像是放项目的文件夹，建议到各项目里分别接入；同时改几个项目时，在主要改的项目里打开 AI 工具，再挂上相关项目。只是提示：`init` MUST NOT 因此停下或改变计划，`check` 的退出码与第一行 MUST NOT 因此改变。识别出语言，或没有这类被跳过的子目录时 MUST NOT 出现这一行。

#### Scenario: 在放项目的文件夹里接入
- **WHEN** 文件夹 `A/` 没有代码，下面的 `b/`、`c/` 各是 git 仓库，在 `A/` 运行 `rulemason init --plan`
- **THEN** 计划的「提示」里有一行写明 `b`、`c` 并建议到各项目里分别接入，计划要写的文件与没有这行提示时相同

#### Scenario: 已在文件夹里接入后巡检
- **WHEN** `A/` 已接入，下面的 `b/` 也已接入，在 `A/` 运行 `rulemason check`
- **THEN** 识别表有一行「提示」写明 `b` 与建议，退出码与第一行和没有这行提示时相同

#### Scenario: 有代码的项目里带子仓库
- **WHEN** 项目根有 `pyproject.toml` 与 Python 代码，下面有一个子模块目录 `libs/x/`（含 `.git`），运行 `rulemason check`
- **THEN** 识别表里没有这行提示，「跳过」一行照旧列出 `libs/x`
