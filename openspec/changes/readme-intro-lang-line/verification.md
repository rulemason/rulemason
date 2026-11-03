# readme-intro-lang-line 验证记录

## 1. 方案与写代码前的判断

- 方案写完：`rulemason judge --change readme-intro-lang-line` 结果为 pass 3 / review 0 / block 0。
- 写代码前：结果为 pass 3 / block 0。

## 2. 自动精简（/simplify，四路并行）

- **效率**：pass。正则在 Python 里有缓存，代码每次 init 只对 README 的几段跑一次。
- **层次**：pass。前缀跳过看的是行首，`_links_only` 看的是去掉链接后剩下的内容，两者互不覆盖，各自独立判断的写法是对的。
- **采纳**：
  - 「去掉链接」和「去掉分隔符」原来挤在一行，拆成两行（一行只做一件事）；
  - 中文句末标点「。！？」原来散在三处，抽成常量 `SENTENCE_END_ZH`。
- **不采纳**：把分隔符的正则也改成模块常量。这条是可选建议，改了收益很小。

## 3. 独立审查

审查者只读 scratchpad 里的一份材料文件，不读仓库、不运行命令。

### 第 1 轮：没有 block，review 4 条

- **已修（正确性与测试）**：最初的判断是「去掉空白后剩下不超过 10 个字」，英文短简介会被误跳，例如「A CLI for [OpenSpec](…)」剩下「ACLIfor」，只有 7 个字。
  - 改为按词判断：分隔符换成空格后切成词，只剩一个词、不超过 10 个字、没有句末标点，才算链接行。
  - 新增用例：「A CLI for [OpenSpec](…)」照常取；「English | [日本語](…) | [中文](…)」被跳过。
  - design D1 与 proposal 已同步。
- **不改**：网址里带括号、行内图片 `![a](x)`、嵌套徽章这几种情况。都很少见，处理结果偏保守，审查者也认为可以接受。

### 第 2 轮：没有 block，review 2 条，已修，按规定不审第 3 轮

- 代码的分隔符里有全角「，」，design 与 proposal 原来没写，已补上。
- `_links_only` 的 return 一行判断三个条件，`"".join(rest)` 也写了两遍，已拆成逐条提前返回。
- 审查者另外指出：「Português (Brasil)」这类中间有空格的语言名会被当成正文。很少见，接受。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed。
- `uv run pytest`：451 passed，未联网。
- 用本仓库 README 调用 `readme_intro`，结果为「给 AI 编码工具（Claude Code、OpenCode、Cursor、Codex）的共享规则与检查点。它只管三件事：」，语言切换行已被跳过。
- 判断回归、前端 lint、文案检查不适用，跳过。

## 5. 与 design 的偏差

- 判断规则从「剩下不超过 10 个字」改成了「只剩一个不超过 10 个字的词」，见第 3 节，design 已同步。

## 6. 估计行数对照（新增 / 删除）

| 文件 | 估计 | 实际 |
|---|---|---|
| `src/rulemason/init.py` | +12 | +25 / −3（超出一倍：审查后把三重条件拆成逐条提前返回，又抽出了 `SENTENCE_END_ZH`） |
| `tests/test_init.py` | +6 | +7 |
