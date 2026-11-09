# 验证：cjk-typography-check

版本 bump：**0.8.32**（`src/rulemason/__init__.py` + README CI 钉；`rulemason --version` → `rulemason 0.8.32`）。

## 样例跑（本仓 README.md + rules/**/*.md）

七条全开，allowlist 空（不写该键）。

| 阶段 | 命中数 | 结论 |
|---|---|---|
| 首跑（空格占位剥离） | 129 | 几乎全是 `fw_punct_space` 假阳性（行内代码旁全角标点） |
| 改占位为 U+E000 后再跑 | 6 | ≤20，本 change 内修 |
| 修文档后再跑 | 0 | CI 可绿 |

### 6 处处理

| 文件 | 行 | 规则 | 处理 |
|---|---|---|---|
| README.md | 28–30 | fw_punct_space | 改写三行表格描述，去掉句末全角括号紧贴单元格空格 |
| rules/cjk-typography.md | 7 | fullwidth_digit | 示例改为「U+FF10 至 U+FF19」 |
| rules/cjk-typography.md | 13 | fw_punct_space | 反例放进行内代码 |

实现：预处理占位由 ASCII 空格改为 `\ue000`；单测覆盖「文件（\`…\`）」类句子。

### CI allowlist

**无条目**（requirements 不写 `allowlist`）。样例后无需例外。

## 门禁结果

| 门禁 | 结果 |
|---|---|
| `uv run ruff check .` | 通过 |
| `uv run pytest` | **696 passed** |
| `openspec validate --all --strict` | 10 passed, 0 failed |
| `rulemason check` | 日常巡检：一切一致（exit 0） |
| 临时 Go→Python 项目 init/update | `.rulemason/rules/` 含两份新规则；update 后补 python；check 0 |
| `rulemason judge --change cjk-typography-check` | pass 3 / review 0 / block 0 |

## 未做（按用户要求）

不归档、不推送、不开 PR、不打 tag、不发 PyPI。
