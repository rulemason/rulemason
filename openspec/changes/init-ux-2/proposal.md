## Why

公司项目首次接入 0.8.0 时暴露了一批「识别不准、检查口径不对」的问题：`defineConfig([` 写法的 ESLint 配置被说成无法识别；旧路径指向已不存在的 `eslint-base.mjs`，init 又加一行新引入，两行并存导致 ESLint 一加载就崩；方案里的原型目录被当成 React 目录；工作区根与 API 目录因有 `package.json` 被当成前端目录；check 的下一步一直是「运行 rulemason update」，而 update 改不了剩下的手动项，用户原地打转。版本落后只看版本号，内容其实没变也提示升级。init-ux-1 已改完 init 体验，这次收口识别与检查。

## What Changes

- ESLint 配置再认 `export default defineConfig([` 与 `export default tseslint.config(` 两种写法；`.eslintrc*` 仍只报告。
- lint 配置引用的 `eslint-base.mjs` 或 `ruff-base.toml` 指向不存在的文件或项目外时，check 单独报「引用的文件不存在」；init 与 update 把这条路径改成正确路径，不另加一行。
- 扫描跳过 `openspec/changes/`（方案草稿与原型不参与语言、前端、lint 识别）。
- 前端目录改为「依赖里有界面框架，或同目录有 `index.html`」的 `package.json` 所在目录；只有工具依赖的 Node 包不再算前端目录。
- 版本落后改为比内容：本机版本会生成的副本与清单记录的校验值不一致时，算副本落后，非 0 退出，下一步 `rulemason update`；只有版本号落后时，第一行附一句，退出码 0。
- lint 层只剩 update 改不了的项时，下一步写明手动改哪个文件、加什么，不再写「运行 rulemason update」。
- 没有 `openspec/` 时，update 结尾加一行「方案检查点未启用」及补齐方法。
- 项目只有一个 Python 目录且全部 Python 文件都在其中时，init 把新建的 `ruff.toml` 写进该目录；否则仍写在项目根。
- 不做：`.eslintrc*` 老格式的自动改写；CommonJS 的 `module.exports` 写法；Vue / Svelte 等框架的专属落法文件；Windows 与 Cursor / OpenCode 的 skill 路径（推迟）；版本常量（被「比内容」取代）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `rulekit-cli`：init 补齐 lint 的写法识别、路径改正与 ruff.toml 位置；update 结尾提示；check 的退出码口径（副本内容落后）、下一步（手动项、只差版本号）、引用不存在的报告；扫描跳过方案目录；前端目录识别口径。

## Impact

- 代码：`src/rulemason/check.py`（前端目录、lint 引用、副本落后、下一步）、`src/rulemason/init.py`（ESLint 写法、路径改正、ruff.toml 位置）、`src/rulemason/shared.py`（扫描跳过）、`src/rulemason/update.py`（结尾提示）。
- 测试：`tests/test_check.py`、`tests/test_init.py`、`tests/test_update.py`。
- 接入项目：升级后 check 可能新报「副本落后」（非 0），运行一次 `rulemason update` 即恢复；CI 钉版本的项目不受影响。
