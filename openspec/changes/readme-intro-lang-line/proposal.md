## Why

`rulemason init` 新建 `AGENTS.md` 时，会从 README 取第一段正文当项目简介。很多 README 在标题下先放一行语言切换（如「中文 · [English](…)」）或导航链接，本仓库在 docs-en 之后也是这样。现在的跳过规则只认标题、徽章、图片、以 `http` 开头的行，这类行会被当成简介写进 `AGENTS.md`。新用户第一次接入时，看到的简介就是「中文 · English」。

## What Changes

- 取简介时，额外跳过「只有链接与分隔符」的段落：去掉段内所有 Markdown 链接后，剩下的只有分隔符（`·`、`|`、`/`、`、`、`,`、`，`）和一个不超过 10 个字的词，且没有句末标点。
- 正文里带链接的句子不受影响，照常取作简介。
- 不做：识别 HTML 写的语言切换（`<p align=…>` 开头的段落原本就会被跳过）；修改已有 `AGENTS.md` 的简介；从 README 之外的地方取简介。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：「init 预填项目信息」补上跳过语言切换与导航链接行。

## Impact

- 代码：`src/rulemason/init.py` 的 `readme_intro`。
- 测试：`tests/test_init.py` 的简介预填参数化用例。
- 只影响新建 `AGENTS.md` 的项目；已接入的项目不受影响。
