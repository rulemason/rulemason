# Verification

## 检查点结果

| 步骤 | 结果 |
|---|---|
| 写代码前判断 `rulemason judge --change judge-onboarding-hints` | pass 3 / review 0 / block 0 |
| 1. 自动精简 | 源码只改了 `check.py` 两行、`init.py` 几行，没有重复或冗余，没有调用 `/simplify` 的四路审查。测试按已有测试的写法写，手工看过 |
| 1. 独立审查 | 一轮，block 0，review 若干，都已处理：①`check.py` 里塞进 append 的条件表达式拆成变量；②skill 第 8 步补「为 0 或「—」」；③补「已有 key、条件未满足」时 `init` 不输出新行的测试；④README「判断」一节开头新加的说明与结尾原有半句重复，删掉后半句；⑤测试文件里多余的空行整理。审查还提醒：`direct-edit-judgment` 是另一个 change，提交时用明确的路径，不混进来。只剩 review 的一轮，修完跑 ruff 与测试，不再审第二轮 |
| 2. `uv run ruff check .` | All checks passed |
| 3. `uv run pytest` | 615 passed（第一轮审查后相关文件 346 passed，ruff 通过） |
| 3. 判断回归 | 命令表没有这一行，跳过；本次没改判断规则文件或 `JEV_MODEL` |
| 4. 前端 lint | 无前端，跳过 |
| 5. 文案检查 | 无界面文案，跳过 |
| 6. 额外步骤（改了 `rules/`，在接入项目验证） | 见下文 3.1；不提交、不推送 |

## 3.1 实测

1. 三个已启用判断的接入项目，只读运行 `check`：「接入后归档 change」分别是 3、1、0，与各项目的接入日期相符；「判断」一行是「已启用」，没有出现新提示。
2. 用一个临时项目（git、3 个归档、没有 `openspec/judgments.yaml`、假 key）验证未启用的情形：
   - `check`：「判断」一行写「可选，未启用（条件已满足：要启用时在 AI 工具中运行 /rulemason）」，「接入后归档 change」是 0。
   - 在伪终端里交互运行 `rulemason init`（已有 key）：结尾多了一行「判断条件已满足；判断只审 OpenSpec 方案与界面文案。要启用，在 AI 工具中运行 /rulemason 并说明要启用判断。」，没有任何与 key 相关的提问。
3. 临时目录已删除，没有提交、没有推送。

## 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/init.py` | +6 / −2 | +5 / −2 | 一致 |
| `src/rulemason/check.py` | +3 | +2 | 一致 |
| `rules/workflow-gates.md` | +1 / −1 | +1 / −1 | 一致 |
| `skills/rulemason/SKILL.md` | +3 / −1 | +2 / −1 | 一致 |
| `README.md` | +2 | +1 / −1 | 一致：开头加一句，原来结尾半句删掉 |
| 三个测试文件 | +40 | +50 / −4 | 在一倍以内：审查后补了「条件未满足」用例 |

## 说明

- 这个 change 只改提示的时机与措辞，没有改任何文件格式。
- 规格里「归档后提示」的触发取「已归档正好 3」或「接入后归档正好 1」；检查点按 `facts` 里的字符串比较，「—」不等于 1，所以推算不出接入日期的项目只剩「正好 3」一个触发点，design 已接受。
