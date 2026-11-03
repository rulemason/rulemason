## MODIFIED Requirements

### Requirement: init 预填项目信息

`init` 新建 `AGENTS.md` 时 SHALL 预填项目简介：取项目根 README 第一段正文（跳过标题、徽章、空行，以及语言切换、导航这类只有链接与分隔符的行），截到两句以内；没有 README 或第一段不是文字时保留「待 /rulemason 补充」占位。红线一节 SHALL 写「暂无」。「本项目样板与豁免」与命令表的「自动识别，请确认」MUST 保留，使 `check` 的下一步仍指向 `/rulemason`。已有的 `AGENTS.md` MUST NOT 被改写简介或红线。

#### Scenario: 有 README 的新项目
- **WHEN** 项目 README 第一段写着「章法是一个给书法爱好者的字帖检索站，按书家与作品浏览单字。它只收录公有领域作品。」
- **THEN** 新建的 `AGENTS.md` 简介为这两句，红线一节为「暂无」，命令表仍带「自动识别，请确认」

#### Scenario: 没有 README
- **WHEN** 项目没有 README 文件
- **THEN** 简介保留「待 /rulemason 补充」占位，红线仍写「暂无」

#### Scenario: 已有 AGENTS.md
- **WHEN** 项目已有自己写的 `AGENTS.md`，简介是一句别的话
- **THEN** init 只补标记块，简介与红线原样保留

#### Scenario: README 开头是语言切换行
- **WHEN** README 标题下第一段是「中文 · [English](https://example.com/README.en.md)」，下一段是「章法是一个字帖检索站。」
- **THEN** 新建的 `AGENTS.md` 简介为「章法是一个字帖检索站。」，不是「中文 · English」

#### Scenario: 正文里带链接
- **WHEN** README 第一段是「本工具是 [OpenSpec](https://example.com) 的配套检查器，给 AI 编码用。」
- **THEN** 简介取这一段，链接不影响判断
