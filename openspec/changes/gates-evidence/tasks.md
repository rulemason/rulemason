## 1. 实现

- [x] 1.1 `check.gate_records(root)`：取最新日期的全部归档，按关键词核对 `verification.md`，并作为「最近归档的检查点记录」接进 `audit` 末尾；验证：五个场景的测试（完整汇报、没有文件、缺审查、同日两个只报缺的、表格写法）通过，退出码与下一步不变
- [x] 1.2 `skills/rulemason/SKILL.md` 日常巡检加一句：这一项提醒下次归档前跑完检查点，不补写过去的汇报；验证：`grep` 能找到这句

## 2. 验证

- [x] 2.1 按 workflow gates 完成精简、独立审查、ruff、pytest；在项目甲、乙、丙的 worktree 运行本次代码的 check，记录这一项的结果；验证：写进 `verification.md`

## Workflow follow-up

- 发版 0.8.7：先查 `git tag` 与 PyPI 已有版本，bump 版本与 README 的 CI 钉版本，推送，按「归档」一节归档，打 tag。
