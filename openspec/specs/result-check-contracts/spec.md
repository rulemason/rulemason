# result-check-contracts Specification

## Purpose

规定改动被 result-check 覆盖的结构化输出契约时，必须同 change 更新检查要求与夹具并本地跑通；项目专属阈值仍只住各项目的 requirements 文件。

## Requirements

### Requirement: 契约规矩只住本仓库一份
本仓库 SHALL 提供 `rules/result-check-contracts.md`，说明：当修改某 result-check requirements 所覆盖的结构化输出 schema 或生成该输出的 prompt 时，同一次 change MUST 更新对应 requirements JSON 与相关夹具，并运行 `rulemason result-check`（或等价库调用）确认。项目专属字段名、阈值与白名单 MUST 只写在各项目 requirements / 夹具中，MUST NOT 写进该共享文件。

#### Scenario: 项目读到契约规矩
- **WHEN** 已接入项目运行 `rulemason update` 后打开 `.rulemason/rules/result-check-contracts.md`
- **THEN** 文件存在且含「同 change 更新 requirements 与夹具并跑 result-check」的要求

### Requirement: 改 schema 或 prompt 时同步检查契约
在已使用 result-check 的项目中，AI 若改动被现有 requirements 覆盖的 schema 或 prompt，SHALL 在同一 change 内更新 requirements 与夹具并跑通检查，MUST NOT 只改生产 schema 而留下过期夹具当作通过。

#### Scenario: 同 change 更新
- **WHEN** 某项目改动了被 `requirements_steps.json` 覆盖的输出字段名
- **THEN** 同一次 change 内 requirements 与夹具已改，且 `rulemason result-check` 对更新后的记录与要求退出 0 或按预期失败并已处理
