## Why

`rulemason init` 找不到 `.rulemason.yaml` 时，以所在 git 仓库的根为项目根（`src/rulemason/shared.py:75-84` 的 `find_root`，规格 rulekit-cli「项目根按最近的 .rulemason.yaml 确定」）。Windows 实测时，在工作区目录下新建的测试子目录里运行 init，而工作区目录恰好是一个没有提交、装着几十个项目的 git 仓库：rulemason 与代跑的 `openspec init` 都写进了工作区目录，测试子目录里什么都没有，计划里也没写项目根在哪，事后靠 `rulemason remove` 加手动删除收拾（Notion 第 71 篇）。

OpenSpec 的做法不同：`openspec init` 在当前目录建 `openspec/`，其他命令才往上找已有的 `openspec/`。git、uv 也是「新建用当前目录，查找才往上找」。rulemason 把「找已有项目」的规则套到了「新建项目」上：猜对了省一步，猜错了会写进一个更大、不相干的目录；而按当前目录建，错了只是子目录里多几个一眼能看出的文件。

## What Changes

- 找不到 `.rulemason.yaml` 时，项目根就是当前目录，不再退到 git 仓库根；`init` 在当前目录接入，代跑的 `openspec init` 也在当前目录。
- 当前目录在某个 git 仓库里、而仓库根不是当前目录时，`init` 的计划（含 `--plan` 与 `--yes`）写明「当前目录在 git 仓库 <根> 里；要接入整个仓库，到仓库根运行，或运行 `rulemason init <根>`」；`update` 报告「先运行 rulemason init」时同样写明，`check` 在识别表里写明仓库根。
- 不变：`check`、`update`、`remove`、`judge` 照旧往上找最近的 `.rulemason.yaml`、不越过 git 仓库根；找到已有清单时 `init` 仍以清单所在目录为项目根；`rulemason init <path>` 照旧以给出的路径为项目根。
- 不做：自动识别「装着多个仓库的工作区」并拒绝接入（启发式容易误判，写明位置已足够）；改 `openspec init` 本身的行为；为已经在仓库根以外接入的项目做迁移（本次只影响新接入）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `judge-engine`：「命令在项目根目录运行」去掉「与 init、update、check 相同的规则」的说法，写明 judge 找不到清单时仍用 git 仓库根及原因（行为不变）。
- `rulekit-cli`：「项目根按最近的 .rulemason.yaml 确定」——找不到清单时以当前目录为项目根；当前目录在 git 仓库子目录时写明仓库根与接入整个仓库的做法。原场景「在子目录运行 init 接入到仓库根」改为「在子目录接入并提示仓库根」。

## Impact

- 代码：`src/rulemason/shared.py` 的 `find_root` 及新增的 `repo_root`、`outer_repo`、`repo_root_hint`；`src/rulemason/cli.py` 没有清单时用当前目录并告诉 init 是否在当前目录接入；`src/rulemason/judge/judge.py` 没有清单时仍用仓库根；`init` 的计划输出与 `check`、`update` 的「先运行 rulemason init」提示加一句仓库根说明。
- 测试：`tests/test_shared.py` 中依赖「没有清单就退到 git 根」的 `test_find_root_stops_at_nested_repo`、`test_find_root_stops_at_git_file`，以及 `tests/test_init.py` 中子目录接入的用例，按新约定改写。
- 文档：README「接入」一句与 Notion 统一入口第 3 节。
- 接入项目：已接入的项目不受影响（都有清单）；以后在 monorepo 子目录运行 init 会在子目录接入，要接入整个仓库需到仓库根运行或写出路径，发布说明写明。
