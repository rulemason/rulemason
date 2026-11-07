# 验证记录：judge-region-proxy-fallback

日期：2026-11-07

## 1. 方案后与写代码前的判断

- 方案写完：`rulemason judge --change judge-region-proxy-fallback` pass 3（proposal-states-non-goals、lint/design、design-no-speculative-extension）/ review 0 / block 0；`openspec validate --strict` valid。
- 写代码前重跑：pass 3 / block 0。
- 审查后 proposal 与 design 补了依赖（见第 3 节），改完用新代码实跑：pass 3 / block 0，直连成功，没有输出改用代理的说明。

## 2. 自动精简

新函数 `has_proxy`、`_system_one` 按名字在仓库检索，没有同名或同用途的实现。`_system_one` 里重发的 `system_one(...)` 只重复一行、不含判断，不到第 7 条的门槛，保持原样。无精简改动。

## 3. 独立审查

审查方式：子代理只读一份材料文件（仓库外的临时文件，审查后删除），不读其他文件、不运行命令。

### 第一轮：block 0、review 11；其中 SOCKS 一条核实后升为 block

- **SOCKS 代理（block）**：环境里只有 `ALL_PROXY=socks5://…` 时，`httpx2.Client(trust_env=True)` 在构造时就抛 `ImportError`（没装 `socksio`），命令行打印堆栈，违反规格。`env -i … ALL_PROXY=socks5://127.0.0.1:1` 实测复现。修法要改方案，停下问用户，用户选择新增依赖 `httpx2[socks]`。已加依赖，新增 `test_socks_proxy_connection_can_be_built`，proposal Impact 与 design 决策 6、文件表同步。
- **测试读到运行机器的真实代理**：本机 `getproxies()` 就有 `all`、`http`、`https`。`_fake_jev` 改为同时把 `httpx2.Client` 换成只记 `trust_env` 的假对象。
- **第二个 `Judge` 没有 `close()`**：已补。
- **`_jev` 说明没写换路**：已补。
- **「直连 451、有代理」没经过 `main`**：新增 `test_region_blocked_run_prints_switch_before_results`，断言说明行在结果之前、合计与退出码。
- **「只说明一次」依赖一次运行只建一个 `Judge`**：核对 `judge.py` 的 `main`，只建一个，未改。
- **换路时连接是否泄漏**：核对 SDK，`TypeSafeClient.close()` 会关闭传入的 `httpx2.Client`，未改。
- **代理连不上**：`TypeSafeAPIConnectionError` 属于 `OSError`，由 `cli` 已有分支给一句话，未改代码。
- **`NO_PROXY` 覆盖 Typesafe 时提示不准**：design 风险已接受，未改。
- **库里 `print`**：规格要求库用法同样输出说明，保持。
- **无关文件**：工作区里 `.claude/skills/`、`.cursor/` 下的改动与未跟踪文件不属于本次，不提交。

### 第二轮：block 0、review 1

- **`cli` 里 451 分支会不会先截走连接错误**：对照 SDK 源码，`TypeSafeAPIConnectionError` 继承 `TypeSafeError` 与 `ConnectionError`，不是 `TypeSafeAPIError` 的子类，不会被截走，代码不改。补 `test_connection_error_still_gives_one_line` 把这一点固定下来。

两轮后不审第三轮。

## 4. ruff 与测试

- `uv run ruff check .`：All checks passed（第二轮修复后重跑）。
- `uv run pytest`：第一轮修复后全量 640 passed；第二轮只加了一条测试，重跑 `uv run pytest tests/judge` 105 passed。
- 没有改判断规则文件与 `JEV_MODEL`，不跑判断回归。

## 5. 前端 lint、文案检查、额外步骤

本仓库没有前端与界面文案；没有改 `rules/` 或 `lint/`，额外步骤不适用。均跳过。

## 6. 端到端

- 直连这条路：用新代码真实运行 `rulemason judge --change judge-region-proxy-fallback`，结果与改动前相同（见第 1 节）。
- 直连 451、经代理成功这条路：本机直连 Typesafe 可用，无法真实复现，只用假客户端测过。发版后请 [issue #24](https://github.com/rulemason/rulemason/issues/24) 的报告人升级实测。

## 7. 与 design 估计行数的对照

| 文件 | 估计 | 实际 | 说明 |
|---|---|---|---|
| `src/rulemason/judge/judge.py` | +30 / −3 | +35 / −4 | |
| `tests/judge/test_engine.py` | +80 | +158 | 接近一倍：审查后补了假 `httpx2.Client`、经 `main` 的用例、SOCKS 与连接失败两条用例 |
| `README.md` | +2 | +2 | |
| `pyproject.toml`、`uv.lock` | +1、+16（审查后加入） | +1、+16 | |
