## ADDED Requirements

### Requirement: 检查点以被改文件所属项目为准

共享检查点 SHALL 写明：检查点所说的「本项目」（命令表、红线规则、额外步骤、主规格）指被改文件往上最近的 `.rulemason.yaml` 所在目录，不是打开 AI 工具的目录。一次改动涉及多个接入项目时，AI SHALL 对每个项目各跑一遍检查点：命令在该项目根执行，diff、审查材料与提交按项目分开。只涉及一个项目时，检查点的行为 MUST NOT 改变。

#### Scenario: 在文件夹里打开工具改子项目
- **WHEN** 在文件夹 `A/` 打开 AI 工具，`A/` 与 `A/b/` 都已接入，`A/` 的命令表 ruff 写「无，跳过」，`A/b/` 的写 `uv run ruff check .`，这次只改了 `A/b/` 里的文件
- **THEN** AI 在 `A/b/` 运行 `uv run ruff check .`，不按 `A/` 的命令表跳过

#### Scenario: 一次改动涉及两个项目
- **WHEN** 在 `b/` 打开 AI 工具并挂上 `../c`，一次不走 OpenSpec 的改动同时改了 `b/` 与 `c/` 的文件
- **THEN** AI 在 `b/` 与 `c/` 各自的根目录按各自命令表跑 ruff 与测试，汇报按项目分开写结果
