# Tasks

## 1. 规矩正文

- [x] 1.1 在 `rules/product-artifact-caution.md` 增补验证走查原则（规矩正文不写外部来源），并确认仍写明结构≠质量、init 不扫仓（人工通读该文件）
- [x] 1.2 若用户确认改为独立规矩文件，则新增必复制路径并更新 `check.py`/`shared` 复制清单；否则在汇报中写明维持并入方案（对照 design 否决项）

## 2. result-check 预设与 CLI

- [x] 2.1 新增包内 `verification-walkthrough.hint.json` 与 `.strict.json`，用 pattern 检查约定小节标题；本地对夹具记录跑通 hint 提示 / strict 失败
- [x] 2.2 在 `shared.py` 登记预设文件名与 id，在 `cli.py` 扩展 `--preset` choices；验证非法 preset 仍报错，旧 preset 名行为不变
- [x] 2.3 扩展 `seed_result_check_presets`：缺失才种入；用临时目录测「已存在则跳过」

## 3. 测试与说明

- [x] 3.1 补充单元/CLI 测试覆盖新预设 hint/strict、不偷换 prose/product-artifact 短名；`uv run pytest` 相关用例通过
- [x] 3.2 跑 `uv run ruff check .` 与针对本 change 的 `rulemason judge --change verification-walkthrough`（若环境可用），修格式类 block
- [x] 3.3 完成汇报写入 `verification.md`：对照 design 行数估计，列出未实现的 Non-goals

## Workflow follow-up

- 用户确认并实现完成后，再归档本 change；发版按仓库惯例最后一位 +1。
- 不在本 change 内推送/开 PR/发版，除非用户另指令。
