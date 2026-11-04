# Design

## Context

动机见 proposal.md「Why」。现状（出处写在句末）：

- `find_root(start)` 从 start 往上找有清单的目录；遇到 `.git`（目录或文件）就停，返回该仓库根；都没有返回 start（`src/rulemason/shared.py:75-84`）。
- 命令行对所有子命令都先算一次 `find_root(Path.cwd())`，`init` 给了路径时改用该路径（`src/rulemason/cli.py:57-61`）。
- judge 另有 `root()`：同样调 `find_root`，再要求项目根下有 `openspec/`（`src/rulemason/judge/judge.py:47-54`）；judge-engine 规格写明「找不到时以 git 仓库根为项目根」（`openspec/specs/judge-engine/spec.md:26`）。
- 代跑 `openspec init` 的工作目录就是项目根（`src/rulemason/init.py` 的 `ensure_openspec`，`subprocess.run(..., cwd=root)`）。
- 未接入时：`update` 打印「没有 .rulemason.yaml：先运行 rulemason init（判断的项目根：…）」（`src/rulemason/update.py:94`）；`remove` 停下并写明判断的项目根（`src/rulemason/remove.py:211`）；check 的识别表第一项是「项目根」（`src/rulemason/check.py:316`）。
- init 的计划有一个「提示：」通道，只出现在文字输出、不进 `--json`（`src/rulemason/init.py` 的 `Plan.tips`、`list_block(TIPS_TITLE, …)`）。
- 测试依赖旧行为的：`test_init_in_subdirectory_uses_repo_root`（`tests/test_init.py:500`）、`test_find_root_stops_at_nested_repo`（`tests/test_shared.py:151`）、`test_find_root_stops_at_git_file`（`tests/test_shared.py:164`）。

## Goals / Non-Goals

**Goals:**
- 没有清单时，init、check、update、remove 都以当前目录为项目根，与 `openspec init` 一致。
- 当前目录在 git 仓库子目录时，用户能从输出里看出仓库根在哪、怎么接入整个仓库。

**Non-Goals:**
- 不改 judge 找项目根的方式。
- 不改 `--json` 的字段集合。

## Decisions

1. **把「找清单」与「找不到时用什么」拆开。** `find_root` 只负责往上找清单（不越过 git 仓库根），找不到返回 None；新增 `repo_root(start)` 返回所在 git 仓库根（不在 git 里返回 None）。命令行在没有清单时用当前目录；judge 在没有清单时用 `repo_root`，保持原规格。否决让 `find_root` 直接改为返回当前目录：judge 依赖「退到仓库根」去找 `openspec/`，在未接入 rulemason 的仓库子目录里运行 judge 会找不到产物。否决给 `find_root` 加一个 `fallback` 参数：两个调用方各自决定更直接，函数也只做一件事。
2. **仓库根说明走「提示：」通道，不算「需要你处理」。** init 的计划（交互摘要、`--plan`、`--yes` 结尾）在项目根与仓库根不同时加一条提示「当前目录在 git 仓库 <仓库根> 里；要接入整个仓库，到仓库根运行，或运行 rulemason init <仓库根>」。否决作为「需要你处理」：在子目录接入是合法选择，不是待办。否决交互时多问一句「要不要改到仓库根」：OpenSpec 不问，多一个提问也让 `--yes` 与交互行为不一致；提示已经足够让人发现。否决写进 `--json`：会改变字段集合，AI 读 `root` 字段即可知道项目根。
3. **check 另起一行写仓库根，update 补同一句说明。** check 的识别表在「项目根」之后加一行「所在 git 仓库根」（只在未接入且在仓库子目录里时出现）；update 的「先运行 rulemason init」提示后面补与 init 相同的说明。否决把仓库根并进「项目根」那一行：`check --json` 的 facts 里「项目根」的值会不再是纯路径，按路径解析的 AI 或脚本会出错。
4. **是否提示由命令行判断「项目根就是当前目录」。** `rulemason init` 不带路径、或带的路径解析后就是当前目录时，命令行把这一点传给 `init.run`；显式给出别的目录时当前目录不是项目根，「当前目录在 git 仓库……」说不通，不提示。否决在 `init.run` 里自己读 `Path.cwd()`：cli 已经算过当前目录，再读一次是隐式依赖。
5. **已有清单的行为完全不变。** 找到清单就用清单所在目录，不比较仓库根，不加提示。否决对所有子目录接入的项目都提示：它们是用户有意建的，每次巡检都提示是噪声。

## Risks / Trade-offs

- [monorepo 用户习惯在子目录运行 init，升级后会在子目录接入] → 提示写明仓库根与接入整个仓库的命令；发布说明写明这一变化。
- [在 git 仓库子目录接入后，`.gitignore` 放行规则、lint 继承都按子目录算] → 这正是「接入的是这个目录」的含义；与显式 `rulemason init <子目录>` 的行为相同，已有测试覆盖。
- [judge 与其他命令的找根规则不再相同] → 只在「没有清单」时不同；design 与 judge 的 docstring 写明原因，judge-engine 规格只改措辞，行为不变。
- [check 在未接入的子目录里给出的项目根变了] → 与 init 将要接入的位置一致，反而更准确；识别表同时写出仓库根。
- [交互运行时，代跑 openspec init 的提问先于计划出现，用户先同意了 openspec init 才看到仓库根提示] → 现在两者都写在当前目录，不会再写到别处；提示仍在写入 rulemason 文件之前的计划里出现。
- [judge-engine 规格原写「与 init、update、check 相同的规则」] → 本 change 同步修改那条措辞，judge 行为不变。

## Migration Plan

1. 改 `shared.find_root`、新增 `repo_root`，改命令行与 judge 的调用；init、check、update 加仓库根说明；改写依赖旧行为的测试并补新场景；README「接入」一句同步。
2. 发版（版本号按发版时 PyPI 已有版本递增），发布说明写明「找不到清单时在当前目录接入」。
3. 已接入项目不受影响；Notion 统一入口第 3 节同步。

回滚：`uv tool install rulemason==<上一版>`；本次不改任何项目文件格式，已在子目录接入的项目可用 `rulemason remove` 卸载后在仓库根重新接入。

## 文件改动与估计行数

| 文件 | 改动 | 估计行数 |
|---|---|---|
| `src/rulemason/shared.py` | `find_root` 找不到返回 None；新增 `repo_root` | +12 / −4 |
| `src/rulemason/cli.py` | 没有清单时用当前目录 | +3 / −2 |
| `src/rulemason/judge/judge.py` | `root()` 没有清单时用 `repo_root` | +3 / −2 |
| `src/rulemason/init.py` | 项目根与仓库根不同时加一条提示 | +8 |
| `src/rulemason/check.py` | 识别表另起一行写仓库根 | +5 / −1 |
| `src/rulemason/update.py` | 「先运行 rulemason init」补仓库根说明 | +4 / −1 |
| `README.md`、`README.en.md` | 「接入」一句：在要接入的目录运行 | +2 / −2 |
| `tests/test_shared.py` | `find_root` 返回 None、`repo_root` 用例 | +15 / −6 |
| `tests/test_init.py` | 子目录接入改写；工作区仓库下的新目录；提示文字 | +30 / −5 |
| `tests/test_check.py`、`tests/test_update.py` | 未接入子目录的项目根与提示 | +20 |
| `tests/test_remove.py` | 未接入子目录运行 remove | +8 |
| `tests/judge/test_engine.py` | 没有清单时 judge 用仓库根 | +6 |
| `specs/judge-engine/spec.md`（change 内增量） | 去掉「相同的规则」的说法 | 24 |
