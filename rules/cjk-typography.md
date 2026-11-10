<!-- 中文混排排版：写文档、方案、规格时遵守。项目经 rulemason 生成的 .rulemason/ 副本引用：不把正文抄进项目指令，不手改副本 -->

写中文文档、OpenSpec 方案/规格、以及给人看的中文说明时遵守下列短名规则。代码标识符与纯英文段落不在此列。确定性强制手段：`rulemason result-check` 的检查类型 `cjk_typography`（可开关 rules、预处理剥离代码/URL、可选 allowlist）。反例可放行内代码，或用 HTML 注释 `<!-- rulemason-disable -->` / `<!-- rulemason-disable 短名, … -->` 临时关闭，配对 `<!-- rulemason-enable -->`（裸 enable 恢复全部）。

## 规则（短名）

- **fullwidth_digit**：不要使用全角数字（U+FF10 至 U+FF19）；用半角 0–9。
- **fullwidth_alpha**：不要使用全角拉丁字母；用半角 A–Z / a–z。
- **ideographic_space**：不要使用表意空格（U+3000）；用普通空格或去掉。
- **stacked_punct**：不要叠用叹号或问号。允许恰好一次的组合：`？！`、`?!`、`！？`、`!?`；不要再叠（如 `？！！`）。
- **cjk_latin_space**：汉字与拉丁字母相邻时加空格（如「使用 Git」）。
- **cjk_digit_space**：汉字与阿拉伯数字相邻时加空格（如「共 3 项」）。
- **unit_space**：数字与常用单位词（默认 GB、TB、Gbps、MB、KB、ms、px，可配置）之间加空格（如「10 Gbps」）。
- **degree_percent_nospace**：数字与 `°`、`%` 之间不要加空格（如「15%」「90°」）。
- **fw_punct_space**：全角标点两侧不要加多余 ASCII 空格（如「你好，世界」而非 ``你好， 世界``）；表格竖线、强调标记或 URL 旁的空格除外。
- **halfwidth_punct_cjk**：两个汉字之间不要夹半角 `,` `;` `:` `!` `?`（应用全角）；半角句点不在此列。

产品或品牌官方不加空格的写法，用检查配置的 `allowlist` 声明，不要在共享文件里写项目专名。
