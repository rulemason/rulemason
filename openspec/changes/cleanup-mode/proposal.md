## Why

存量清理要等用户先点名一类违规（例如清掉嵌套三元），skill 才按六步动手。仓库里哪个模块值得先清、软冗余有多少，没有只读诊断。检查点只审本次 diff，既有代码不会因此被改；九条第 8、9 条已经能指出三类冗余，但没有按模块去清的入口。

## What Changes

- `/rulemason` 增加 `cleanup` 用法（自然语言说要清理同样算）：不带模块名只诊断全仓，不改文件；带模块名只修该模块。
- 诊断分三层：lint 硬指标、临时启用的机械软指标与重复检测、每模块抽样的精简潜力。汇报最后一行写出下一步输入。
- 修模块仍走现有六步。模块名只划定范围，动手前仍列计划等确认；修之前通读该模块，用户选择落地哪些软建议。
- 进度不另存文件：硬指标看「接入前遗留」条目是否还在，软指标看提交说明 `refactor(cleanup): <模块>`。skill 自己不提交。
- 不做：
  - 不新增 skill，也不改成插件的 `/rulemason:cleanup`。
  - 不把诊断或进度写进 `.rulemason/`。
  - 不在安装或 init 时安装查重工具，不把 `ARG` 等规则写进 lint 基础配置。
  - 不改九条正文，不改 `src/rulemason/`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rules-layer-setup`：存量清理增加入口闸门、三层诊断和按模块修复；「每次只做第一个未完成阶段」在用户要清理时让路。

## Impact

- `skills/rulemason/SKILL.md`：第 1 节加一句入口，第 7 节改成诊断与按模块修。
- `tests/test_templates.py`：补断言，并放宽第 7 节的行数上限。
- 接入项目运行 `rulemason update` 后拿到新 skill。命令行与 lint 基础配置不变。
