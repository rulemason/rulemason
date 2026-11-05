## MODIFIED Requirements

### Requirement: 项目根按最近的 .rulemason.yaml 确定

`rulemason init`、`update`、`check`、`remove` SHALL 从当前目录往上找最近的 `.rulemason.yaml`，以它所在目录为项目根；向上查找 MUST NOT 越过当前目录所在 git 仓库的根目录。找不到时 SHALL 以当前目录为项目根，MUST NOT 退到 git 仓库根；`check` 与 `update` SHALL 报告「先运行 rulemason init」并写明判断出的项目根。找不到清单、项目根就是当前目录（没有显式给出别的路径）、且当前目录在 git 仓库里而不是仓库根时，`init` 的计划与 `update` 的提示 SHALL 写明仓库根以及接入整个仓库的做法（到仓库根运行，或 `rulemason init <仓库根>`），`check` 的识别表 SHALL 写明仓库根。`rulemason init <path>` 显式给出路径时 SHALL 以该路径为项目根，不再向上查找。

#### Scenario: 在已接入项目的子目录运行
- **WHEN** 在已接入项目的 `app/` 子目录运行 `rulemason check`
- **THEN** 以项目根目录检查，结果与在项目根运行相同，不提示「先运行 rulemason init」

#### Scenario: 在子目录运行 init
- **WHEN** 在一个尚未接入的 git 仓库的 `web/src/` 目录运行 `rulemason init --tools claude --yes`
- **THEN** 在 `web/src/` 接入，仓库根不出现 `.rulemason.yaml` 或 `.rulemason/`；输出写明「当前目录在 git 仓库 <仓库根> 里；要接入整个仓库，到仓库根运行，或运行 rulemason init <仓库根>」

#### Scenario: 工作区仓库下的新目录
- **WHEN** 工作区目录是一个装着多个项目的 git 仓库，在其下新建的、自己还不是 git 仓库的 `rm-test/` 里运行 `rulemason init`，同意代跑 `openspec init`
- **THEN** rulemason 与 `openspec init` 都写在 `rm-test/`，工作区目录里不出现任何新文件；计划写明工作区的仓库根

#### Scenario: 工作区里的独立仓库
- **WHEN** 工作区根目录已接入（有 `.rulemason.yaml`），在其中一个独立 git 仓库 `app-a/` 里运行 `rulemason check`
- **THEN** 不向上找到工作区的 `.rulemason.yaml`，报告 `app-a/` 尚未接入，提示「先运行 rulemason init」

#### Scenario: 在未接入仓库的子目录运行 check
- **WHEN** 在一个尚未接入的 git 仓库的 `web/` 目录运行 `rulemason check`
- **THEN** 识别表的项目根写 `web/`，另起一行写所在 git 仓库根；第一行为「接入：运行 rulemason init」

#### Scenario: 显式给出路径
- **WHEN** 运行 `rulemason init packages/web --tools claude --yes`
- **THEN** 以 `packages/web/` 为项目根接入，不向上查找；当前目录不是项目根，不提示所在 git 仓库根
