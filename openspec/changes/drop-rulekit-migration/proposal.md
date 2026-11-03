# Proposal

## Why

rulemason 的前身 rulekit 0.5 只有作者本人用过；三个接入项目和所有机器都已在 publish-rulemason 中迁到 0.8.0。从 rulekit 格式迁移的整条路径（迁移计划、旧接入方式识别、旧名残留巡检、skill 里的残留处理）从此没有任何触发它的用户，却占着 `migrate.py`、约 35 处识别代码、3 条规格要求、231 行测试和 README 一节，每次改 init / check 都要连带维护。公开版本里留着一个永远不会触发的功能，只会让读代码和读文档的人困惑。

## What Changes

- 删除 `src/rulemason/migrate.py` 与 `tests/test_migrate.py`；`init` 不再识别 `.rulekit.yaml`，`check`、`update`、`remove` 不再区分「rulekit 0.5 格式」。
- 删除「旧接入方式」（引用 `../rulekit/`、指向项目外的旧 skill 符号链接）识别与「旧名残留」巡检；`check` 的下一步不再有 `legacy`、`migrate`、`fix_residue` 三个代码，退出码不再因这两项非 0。
- `shared.py` 删去 `OLD_NAME`、`OLD_MANIFEST`、`OLD_COPY_DIR`；删除只为残留检查服务的 `MANAGED_BLOCK` 正则；跳过目录不再含 `.rulekit`。
- `/rulemason` skill 删去第二阶段第 0 步「旧名残留」与状态表里的 `legacy`、`migrate`、`fix_residue` 三行；描述中不再提迁移。
- README 删去「从 rulekit 迁移」一节与「出了问题怎么办」表里的迁移行；`AGENTS.md` 目录说明不再提迁移逻辑；`cli` 帮助文字同步。
- 规格：`rulekit-cli` 删除 3 条要求（init 从 rulekit 格式迁移、迁移前核对旧副本、check 报告旧名残留），另有 7 条要求与 `rules-layer-setup` 3 条要求去掉涉及迁移的句子与场景。
- 版本 0.8.2。
- 不做：改规格 id `rulekit-cli`；改 `judge` 读旧 key 位置 `~/.config/jev-judge/env` 的只读兜底（作者自己的机器仍在用）；改 `judge-engine` 规格「判定口径与迁移前一致」（说的是引擎口径，与 rulekit 无关）。
- 不做：清理 `update` 对 0.6.x 旧模板副本的删除逻辑（那是 rulemason 自己的历史版本，仍有用）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：删除三条迁移相关要求；init 预检、update、check 退出条件、项目根查找、跳过目录、check 第一行顺序、init --plan 七条要求去掉迁移内容。
- `rules-layer-setup`：skill 不再处理 rulekit 0.5 格式、旧接入方式与旧名残留。

## Impact

- 代码：删 `migrate.py`；改 `shared.py`、`check.py`、`init.py`、`update.py`、`remove.py`、`cli.py`。
- 测试：删 `test_migrate.py`；改 `test_check.py`、`test_init.py`、`test_remove.py`、`test_shared.py`、`test_templates.py`。
- 文档：`README.md`、`AGENTS.md`、`skills/rulemason/SKILL.md`。
- 接入项目：已迁移的项目不受影响，`update` 后 skill 副本少一步说明；仍持有 `.rulekit.yaml` 的项目（已知为零）在 0.8.2 下会被当作未接入项目。
