# Tasks

## 1. 检测库：预处理、区间、收窄与新规则

- [ ] 1.1 扩展预处理：`~~~` 围栏、缩进代码块、引用式链接定义、尖括号自动链接；保持 U+E000 占位与偏移。验证：单测覆盖四类不误报。
- [ ] 1.2 汉字区间含扩展 A 与兼容区；收窄 `fw_punct_space`（URL 占位、`**`、`|` 例外）。验证：扩展 A 贴拉丁可检出；表格 `） |` 不报；「你好， 世界」仍报。
- [ ] 1.3 实现 `halfwidth_punct_cjk`（`,;:!?`，不含 `.`）、`fullwidth_alpha`、`ideographic_space`；加入 `KNOWN_RULES`；不改 `fullwidth_digit`。验证：正/反例单测；未列入 rules 不启用。
- [ ] 1.4 实现 HTML 注释 `rulemason-disable` / `rulemason-enable`（裸关全部 / 带名列表）；未知短名 → 配置错误。验证：关闭区间不命中；未知名 exit 2。
- [ ] 1.5 干净室：源码与规则正文无 autocorrect 路径或大段原文。验证：`rg` 无上游特征拷贝。

## 2. 报告与 result-check 接线

- [ ] 2.1 失败列出全部命中（规则、行、列、offset、length）与总数；不回显全文；退出码 0/1/2 不变；可选 `max_hits`（默认 50）。验证：多命中 pytest；旧夹具仍 exit 0。
- [ ] 2.2 更新 `--help` 提及新短名与 disable 注释。验证：help 可检索。

## 3. 规则层、CI、版本与致谢

- [ ] 3.1 更新 `rules/cjk-typography.md`：三新短名 + disable 约定。验证：通读无上游原文。
- [ ] 3.2 本仓 CI pytest 的 rules 打开三新短名；allowlist 仍空。验证：故意插入半角夹逗号可红；修回绿。
- [ ] 3.3 README 致谢 autocorrect（MIT，仅行为参考）；bump **0.8.33**（`__init__.py` + README CI 钉）。验证：`--version` 为 0.8.33。
- [ ] 3.4 对本仓 README + `rules/` 样例；≤20 非平凡则修，>20 停列清单。写 `verification.md`；全量 ruff/pytest/`rulemason check`。验证：汇报含数字；tasks 无提前勾选。
- [ ] 3.5 PR 说明含致谢句；注明 Yaomancy 同步另开。验证：人工确认文案（发 PR 时）。
