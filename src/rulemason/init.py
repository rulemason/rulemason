"""rulemason init：在项目根接入共享规则——预检、选工具、生成副本与入口、补齐配置，列计划一次确认后写入。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from string import Template

import yaml

from rulemason import banner, check, select
from rulemason import key as key_cmd
from rulemason.check import BlockError, block_body, find_block, for_languages, markers
from rulemason.judge import judge as engine
from rulemason.shared import (
    COPY_DIR,
    DIM,
    KEY_URL,
    MANIFEST,
    NAME,
    SKY_BOLD,
    TOOL_IDS,
    TOOL_LABELS,
    YELLOW,
    ConfigError,
    ManifestError,
    bullets,
    copy_record,
    dirty_files,
    dump_json,
    generated_files,
    has_git,
    has_openspec,
    ignored_files,
    is_source_repo,
    list_files,
    manifest_text,
    normalize_tools,
    paint,
    read_manifest,
    sha256_file,
    skill_dirs,
    template,
    write_text,
)

TOOL_DIRS = {".opencode": "opencode", ".claude": "claude", ".cursor": "cursor", ".agents": "codex"}   # 已有目录 → 标注「检测到」；--plan 时据此推断
README_NAMES = ("README.md", "README.rst", "README")
OPENSPEC_HINT = f"检查点与方案写法需要 OpenSpec：安装后在项目根运行 openspec init，再运行 {NAME} update 补齐"
OPENSPEC_INSTALL = "npm install -g @fission-ai/openspec@latest"
ROW_NAMES = ("判断", "ruff", "测试", "前端 lint", "文案检查")
NEXT_STEP = f"下一步：在 AI 工具中运行 /{NAME}，补项目简介、红线并确认命令表。"
TIPS_TITLE = "提示："


class Stop(Exception):
    """预检或参数不满足，停止且不写任何文件；code 为退出码。"""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


@dataclass
class Plan:
    writes: dict[str, str] = field(default_factory=dict)     # 相对路径 → 新内容（只放有变化的）
    deletes: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)     # 被覆盖的手改副本
    notes: list[str] = field(default_factory=list)           # 跳过并需要人处理的情况
    tips: list[str] = field(default_factory=list)            # 顺带告诉人的事（如旧副本可删），不算待处理

    def text(self, root: Path, rel: str) -> str:
        """计划里已改过的内容优先（同一次 init 里前一步刚改过的文件），否则读磁盘。"""
        if rel in self.writes:
            return self.writes[rel]
        return (root / rel).read_text(encoding="utf-8")


def print_notes(notes: list[str], heading: str, color: str | None = YELLOW) -> None:
    """打印标题 + 列表；没有就不打印。需要用户处理的事用黄色标题，顺带告诉人的事（tips）不上色。init 与 update 共用。"""
    if notes:
        print(paint(heading, color) if color else heading)
        print(bullets(notes), end="")


def add_once(items: list[str], item: str | None) -> None:
    """item 非空且还没有时追加；多份配置共用一个末端时同一条说明只出现一次。"""
    if item and item not in items:
        items.append(item)


def list_block(title: str, items: list[str]) -> list[str]:
    """计划里的一段列表：标题一行，每项一行「  - 项」；没有项时为空。"""
    return [title, *(f"  - {item}" for item in items)] if items else []


def interactive() -> bool:
    return sys.stdin.isatty()


YES = ("y", "yes", "是")


def ask_yes(question: str) -> bool:
    return input(f"{question} [y/N] ").strip().lower() in YES


# ---------- 1. 标记块（init 与 update 共用） ----------

def unfenced(lines: list[str]) -> list[tuple[int, str]]:
    """``` 或 ~~~ 代码块以外的行及其下标；代码块以开头同一种字符的标记结束。Claude Code 不解析代码块里的导入。"""
    out, fence = [], None
    for i, line in enumerate(lines):
        mark = line[:3]
        if mark in ("```", "~~~") and fence in (None, mark):
            fence = None if fence else mark
        elif fence is None:
            out.append((i, line))
    return out


def seed_line(lines: list[str], seed: str) -> int | None:
    """代码块以外，seed 只出现一次、且恰好顶格独占一行时返回该行下标，否则返回 None。"""
    outside = unfenced(lines)
    if sum(line.count(seed) for _, line in outside) != 1:
        return None
    return next((i for i, line in outside if line.splitlines()[0] == seed), None)


def set_block(text: str, name: str, body: str, heading: str | None) -> str:
    """把标记块内容换成 body；没有标记块时插到 heading 标题下，没有该标题就在文末新建。
    heading 为 None（即 CLAUDE.md 的 claude 块）时，正文第一行（模板里是 @AGENTS.md，remove 后会单独留下这一行）
    若按 seed_line 的条件独占一行，就地换成整块，否则加在文末。"""
    start, end = markers(name)
    block = f"{start}\n{body}{end}"
    span = find_block(text, name)
    if span:
        return text[: span[0]] + block + text[span[1]:]
    lines = text.splitlines(keepends=True)
    at = seed_line(lines, body.splitlines()[0]) if heading is None and body.strip() else None
    if at is not None:
        lines[at] = block + lines[at][len(lines[at].splitlines()[0]):]          # 保留原行的换行符
        return "".join(lines)
    match = re.search(rf"^##\s+{re.escape(heading)}.*$", text, re.M) if heading else None
    if match:
        return text[: match.end()] + "\n\n" + block + text[match.end():]
    title = f"## {heading}\n\n" if heading else ""
    prefix = text.rstrip("\n") + "\n\n" if text.strip() else ""
    return f"{prefix}{title}{block}\n"


AGENTS_IMPORT = re.compile(r"@(?:\./)?AGENTS\.md\b")


def imports_agents(text: str) -> bool:
    return any(AGENTS_IMPORT.search(line) for _, line in unfenced(text.splitlines()))


def plan_blocks(root: Path, files: list[str], tools: list[str], plan: Plan, create: bool) -> None:
    """AGENTS.md 的两个标记块与 CLAUDE.md 的 rulemason:claude 块。
    create=False 时只刷新块齐全的文件；缺文件或缺块的交给 create=True（补齐计划）处理。"""
    for rel, blocks in check.block_targets(tools):
        path = root / rel
        if not path.is_file() and not create:
            continue
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        base = plan.writes.get(rel, current)                 # 前一步已改过该文件时，以改后的内容为起点
        text = base or (agents_template(root) if rel == "AGENTS.md" else "")
        try:
            if not create and any(find_block(text, name) is None for name, _ in blocks):
                # 走到这里说明块不齐：只刷新模式不动这个文件，留给补齐计划
                continue
            for name, heading in blocks:
                body = block_body(name, root, files)
                text = set_block(text, name, body, heading)
        except BlockError as exc:
            # 走到这里说明该文件无法安全写入，整份跳过，前一步对它的改动也一并撤掉
            plan.writes.pop(rel, None)
            plan.notes.append(f"{rel}：{exc}；未修改")
            continue
        if rel == "CLAUDE.md" and find_block(base, "claude") is None and imports_agents(drop_block(text, "claude")):
            plan.notes.append(f"CLAUDE.md 在 {NAME}:claude 块外已导入 AGENTS.md，与块内重复导入：请删去块外那一行")
        if text != current:
            plan.writes[rel] = text


# ---------- 2. 生成副本（init 与 update 共用） ----------

def plan_copies(root: Path, tools: list[str], rules: list[str], record: dict[str, str], plan: Plan) -> dict[str, str]:
    """把已选工具的副本刷新为当前版本；返回新的校验值记录。被手改过的副本照样覆盖，并记进 overwritten。"""
    files = generated_files(tools, rules)
    for rel, content in files.items():
        path = root / rel
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        if path.is_file() and rel in record and sha256_file(path) != record[rel]:
            plan.overwritten.append(rel)
        plan.writes[rel] = content
    return copy_record(files)


def plan_manifest(root: Path, current: dict | None, tools: list[str], files: dict[str, str], plan: Plan) -> None:
    text = manifest_text(current, tools, files)
    path = root / MANIFEST
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        plan.writes[MANIFEST] = text


def unsafe_targets(root: Path, rels: list[str]) -> list[str]:
    """目标是符号链接，或解析后落在项目外（父目录是指向外面的链接）的路径。"""
    project = root.resolve()
    return [rel for rel in rels if (root / rel).is_symlink() or project not in (root / rel).resolve().parents]


def apply(root: Path, plan: Plan) -> None:
    """先校验全部目标再动手；有不安全的目标就一个都不写，抛 ValueError。"""
    unsafe = unsafe_targets(root, [*plan.writes, *plan.deletes])
    if unsafe:
        raise ValueError("以下目标是符号链接或在项目外，未写任何文件：" + "、".join(unsafe))
    for rel, content in plan.writes.items():
        write_text(root / rel, content)
    for rel in plan.deletes:
        path = root / rel
        path.unlink()
        for parent in path.parents:
            # 只清理删空的 skill 目录，到项目根为止
            if parent == root or any(parent.iterdir()):
                break
            parent.rmdir()


# ---------- 3. 预检、选工具、openspec ----------

def preflight(root: Path, command: str) -> dict | None:
    """init 与 update 共用的预检：不满足条件抛 Stop；返回已有 manifest（没有为 None）。"""
    if not root.is_dir():
        raise Stop(f"项目目录不存在：{root}")
    if is_source_repo(root):
        raise Stop(f"这是 {NAME} 仓库本身，它直接引用 rules/，不需要 {NAME} {command}")
    if not has_git(root):
        print("提示：没有 git，无法用 diff 查看改动、副本无法通过仓库共享；继续。", file=sys.stderr)
    try:
        return read_manifest(root)
    except ManifestError as exc:
        raise Stop(f"{exc}；请先修正 {MANIFEST}") from exc


def detected_tools(root: Path) -> list[str]:
    """项目里已有目录的工具：只看目录，不看清单。"""
    return normalize_tools([tool for d, tool in TOOL_DIRS.items() if (root / d).is_dir()])


def default_tools(root: Path, manifest: dict | None) -> list[str]:
    """--plan 不提问时用的工具：清单记录的，没有清单就按已有目录推断。"""
    if manifest is not None:
        return list(manifest["tools"])
    return detected_tools(root)


def ask_tools(checked: list[str], detected: list[str]) -> list[str]:
    """终端里用空格勾选；读不了单键时退回编号输入。checked 是预勾的（重跑时为清单记录的），detected 只标注不预勾。"""
    labels = [f"{TOOL_LABELS[tool]}（{tool}）" for tool in TOOL_IDS]
    notes = ["检测到" if tool in detected and tool not in checked else "" for tool in TOOL_IDS]
    try:
        picked = select.choose("选择本项目使用的 AI 工具", labels, [tool in checked for tool in TOOL_IDS], notes)
    except select.Unsupported:
        return ask_tools_numbered(checked, labels, notes)
    if picked is None:
        raise Stop("已取消，未写任何文件。", 0)
    return normalize_tools([TOOL_IDS[i] for i in picked])


def ask_tools_numbered(defaults: list[str], labels: list[str], notes: list[str]) -> list[str]:
    """读不了单键时的退路：打印带编号、已预勾选的清单；输入编号（逗号分隔），有预勾项时直接回车保持默认。"""
    print("选择本项目使用的 AI 工具（输入编号，逗号分隔" + ("；直接回车保持默认" if defaults else "") + "）：")
    for i, (tool, label, note) in enumerate(zip(TOOL_IDS, labels, notes, strict=True), 1):
        print(f"  {i}. [{'x' if tool in defaults else ' '}] {label}" + (f"  {note}" if note else ""))
    while True:
        answer = input("> ").strip()
        if not answer and defaults:
            return defaults
        numbers = [part.strip() for part in answer.replace("，", ",").split(",") if part.strip()]
        if numbers and all(n.isdigit() and 1 <= int(n) <= len(TOOL_IDS) for n in numbers):
            return normalize_tools([TOOL_IDS[int(n) - 1] for n in numbers])
        print(f"请输入 1–{len(TOOL_IDS)} 的编号，至少选一个。")


def choose_tools(root: Path, manifest: dict | None, tools_arg: str | None) -> list[str]:
    if tools_arg is not None:
        try:
            tools = normalize_tools([t for t in tools_arg.split(",") if t.strip()])
        except ValueError as exc:
            raise Stop(str(exc), 2) from exc
        if not tools:
            raise Stop("--tools 至少要选一个工具", 2)
        return tools
    checked = list(manifest["tools"]) if manifest is not None else []
    return ask_tools(checked, detected_tools(root))


def ensure_openspec(root: Path, tools: list[str], yes: bool) -> bool:
    """返回项目是否有 openspec/。没有时：交互运行先问要不要代跑 openspec init；--yes、拒绝或本机没有命令时不跑，
    只接入「读」层（规则副本、入口、lint）。代跑失败抛 Stop。"""
    if has_openspec(root):
        return True
    if shutil.which("openspec") is None:
        print(f"项目没有 openspec/，本机也没有 openspec 命令（安装：{OPENSPEC_INSTALL}）；先只接入规则与 lint。")
        return False
    command = ["openspec", "init", "--tools", ",".join(tools), "--language", "zh-CN"]
    if yes or not ask_yes(f"项目没有 openspec/，现在运行 `{' '.join(command)}`？（否则先只接入规则与 lint）"):
        return False
    sys.stdout.flush()                                      # 先输出前面的提示，再让 openspec 直接写终端
    if subprocess.run(command, cwd=root).returncode != 0:
        raise Stop(f"openspec init 失败（输出见上），{NAME} 未写任何文件")
    return True


# ---------- 4. 只在 init 做的计划：工具增删、命令表、配置 ----------

def plan_stale_copies(root: Path, record: dict[str, str], current: dict[str, str], plan: Plan) -> None:
    """清单记录过、当前版本不再生成的副本（取消了工具，或副本清单缩减）：与记录一致就删，手改过的保留并报告。
    清单只是仓库里的文本，记录的路径不在副本目录里就不碰。"""
    managed = check.managed_prefixes(list(TOOL_IDS))
    for rel in record:
        path = root / rel
        if rel in current or not path.is_file():
            continue
        if not rel.startswith(managed) or ".." in Path(rel).parts:
            # 走到这里说明清单被写错或被改过：不在副本目录里的文件一律不删
            plan.notes.append(f"{MANIFEST} 记录了副本目录以外的 {rel}，未删除")
            continue
        if record[rel] == sha256_file(path):
            plan.deletes.append(rel)
        else:
            plan.notes.append(f"{rel} 被手改过，已不再生成但保留，请自行处理")


def detect_commands(root: Path, files: list[str]) -> dict[str, str]:
    """按 design 决策 6 识别命令：uv 项目的 ruff 与 pytest，package.json scripts 的 lint 与 test。"""
    ruff, tests, front = [], [], []
    for f in sorted(files):
        directory = Path(f).parent
        prefix = "" if str(directory) == "." else f"cd {directory} && "
        if Path(f).name == "pyproject.toml" and (root / directory / "uv.lock").is_file():
            ruff.append(f"`{prefix}uv run ruff check .`")
            if (root / directory / "tests").is_dir():
                tests.append(f"`{prefix}uv run pytest`")
        elif Path(f).name == "package.json":
            try:
                scripts = json.loads((root / f).read_text(encoding="utf-8")).get("scripts") or {}
            except json.JSONDecodeError:
                continue
            runner = "pnpm" if (root / directory / "pnpm-lock.yaml").is_file() else "npm"
            front += [f"`{prefix}{runner} run lint`"] if "lint" in scripts else []
            tests += [f"`{prefix}{runner} run test`"] if "test" in scripts else []
    skip = "无，跳过"
    optional = "可选，未启用"
    values = (optional, "；".join(ruff) or skip, "；".join(tests) or skip, "；".join(front) or skip, optional)
    return dict(zip(ROW_NAMES, values, strict=True))


def command_table(rows: dict[str, str]) -> str:
    lines = ["本项目命令表（自动识别，请确认）：", "", "| 名称 | 命令 |", "|---|---|"]
    return "\n".join(lines + [f"| {name} | {value} |" for name, value in rows.items()])


def plan_command_table(root: Path, files: list[str], plan: Plan) -> None:
    """AGENTS.md 没有命令表时，把识别出的表插在 rulemason:workflow-gates 块之后。"""
    path = root / "AGENTS.md"
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    text = plan.writes.get("AGENTS.md", current)
    if re.search(r"^\|\s*(名称|name)\s*\|\s*(命令|command)\s*\|", text, re.M | re.I):
        return
    try:
        span = find_block(text, "workflow-gates")
    except BlockError:
        return
    if span is None:
        # 走到这里说明 AGENTS.md 已因标记块问题跳过，命令表一并不写
        return
    plan.writes["AGENTS.md"] = text[: span[1]] + "\n\n" + command_table(detect_commands(root, files)) + text[span[1]:]


def _yaml_item(item: str, indent: str) -> str:
    return indent + yaml.safe_dump([item], allow_unicode=True, width=10_000)


def _list_end(lines: list[str], key_at: int, key_indent: int) -> int:
    """列表键下最后一行的下标：缩进更深的行，或与键同缩进的「- 」条目。"""
    last = key_at
    for i in range(key_at + 1, len(lines)):
        stripped = lines[i].strip()
        indent = len(lines[i]) - len(lines[i].lstrip())
        if not stripped:
            continue
        if indent > key_indent or (indent == key_indent and stripped.startswith("- ")):
            last = i
        else:
            break
    return last


def append_section(text: str, key: str, value: object, comment: str = "") -> str:
    """在 YAML 文末追加一个顶层段，原文逐字保留；comment 是段前的注释行（含换行）。"""
    dumped = yaml.safe_dump({key: value}, allow_unicode=True, sort_keys=False, width=10_000)
    return text.rstrip("\n") + "\n\n" + comment + dumped


def same_except(before: dict, after: dict, key: str) -> bool:
    """除 key 以外的顶层键在改动前后完全相同（追加或合并没有碰到项目的其他配置）。"""
    return {k: v for k, v in after.items() if k != key} == {k: v for k, v in before.items() if k != key}


def add_artifact_rules(text: str, base: dict[str, list[str]]) -> str:
    """只追加基础 rules 中缺少的条目，其余文字逐字保留；结构异常时抛 ValueError。"""
    data = yaml.safe_load(text) or {}
    project = data.get("rules")
    if project is None and not re.search(r"^rules\s*:", text, re.M):
        return append_section(text, "rules", base)
    if not isinstance(project, dict):
        raise ValueError("rules 不是映射")
    lines = text.splitlines(keepends=True)
    rules_at = next((i for i, line in enumerate(lines) if re.match(r"^rules\s*:\s*(#.*)?$", line)), None)
    if rules_at is None:
        raise ValueError("rules 不是块格式")
    for artifact, items in base.items():
        missing = [item for item in items if item not in (project.get(artifact) or [])]
        if not missing:
            continue
        key_at = next((i for i in range(rules_at + 1, len(lines)) if re.match(rf"^\s+{re.escape(artifact)}\s*:", lines[i])), None)
        if key_at is None:
            end = _list_end(lines, rules_at, 0)
            lines[end + 1:end + 1] = [f"  {artifact}:\n"] + [_yaml_item(item, "    ") for item in missing]
            continue
        if not re.match(rf"^\s+{re.escape(artifact)}\s*:\s*(#.*)?$", lines[key_at]):
            raise ValueError(f"rules.{artifact} 不是块列表")
        key_indent = len(lines[key_at]) - len(lines[key_at].lstrip())
        end = _list_end(lines, key_at, key_indent)
        item_indent = " " * (key_indent + 2) if end == key_at else lines[end][: len(lines[end]) - len(lines[end].lstrip())]
        if not lines[end].endswith("\n"):
            lines[end] += "\n"
        lines[end + 1:end + 1] = [_yaml_item(item, item_indent) for item in missing]
    return "".join(lines)


def plan_artifact_rules(root: Path, plan: Plan) -> None:
    path = root / "openspec/config.yaml"
    if not path.is_file():
        plan.notes.append("没有 openspec/config.yaml：未补产物写法 rules")
        return
    current = path.read_text(encoding="utf-8")
    base = check.base_artifact_rules()
    try:
        text = add_artifact_rules(current, base)
        result = yaml.safe_load(text)
    except (ValueError, yaml.YAMLError) as exc:
        plan.notes.append(f"openspec/config.yaml 的 rules 无法安全合并（{exc}）：未修改，请手动补齐基础条目")
        return
    before = yaml.safe_load(current) or {}
    complete = all(item in (result["rules"].get(a) or []) for a, items in base.items() for item in items)
    if not (complete and same_except(before, result, "rules")):
        plan.notes.append("openspec/config.yaml 的 rules 无法安全合并：未修改，请手动补齐基础条目")
    elif text != current:
        plan.writes["openspec/config.yaml"] = text


OPERATIONS_COMMENT = f"# {NAME}：apply / archive 时交给 AI 的检查点提示，只指路，正文在检查点文件\n"


def operations_section(root: Path) -> str:
    """init 追加到 config.yaml 文末的 operations 段原文（含前面的空行与注释）；remove 按同一原文识别并删除。"""
    return append_section("", "operations", check.base_operations(root), OPERATIONS_COMMENT)


def plan_operations(root: Path, plan: Plan) -> None:
    """config.yaml 没有 operations 段时在文末追加基础版；已有就不碰，差异由 check 报告。"""
    rel = "openspec/config.yaml"
    path = root / rel
    if not path.is_file():
        # 走到这里说明没有 config.yaml，plan_artifact_rules 已记过提示
        return
    current = plan.writes.get(rel) or path.read_text(encoding="utf-8")
    try:
        before = yaml.safe_load(current) or {}
    except yaml.YAMLError:
        return                                               # 解析不了的情况 plan_artifact_rules 已记过提示
    if not isinstance(before, dict) or "operations" in before:
        # 走到这里说明已有 operations 段（不论内容）或顶层不是映射：不追加，差异由 check 报告
        return
    text = current.rstrip("\n") + operations_section(root)
    try:
        after = yaml.safe_load(text)
    except yaml.YAMLError:
        after = None                                         # 原文以 `...` 等收尾时，追加的段会变成第二个文档
    if not isinstance(after, dict) or not same_except(before, after, "operations"):
        plan.notes.append("openspec/config.yaml 的 operations 无法安全追加：未修改，请手动补上检查点提示")
        return
    plan.writes[rel] = text


def ruff_home(files: list[str]) -> str:
    """新建 ruff.toml 放哪：Python 包目录只有一个、不是项目根且所有 .py 都在其中时放进该目录（单独克隆也读得到），否则放项目根。"""
    dirs = check.python_dirs(files)
    if len(dirs) == 1 and dirs[0] != "." and all(f.startswith(f"{dirs[0]}/") for f in files if f.endswith(".py")):
        return dirs[0]
    return "."


def plan_lint(root: Path, files: list[str], plan: Plan) -> None:
    """ruff 与 ESLint 继承 .rulemason/lint/；每份已有配置怎么改由 check.lint_fix 判断，改不了的只报告。"""
    configs = check.ruff_configs(root, files)
    if check.needs_ruff_config(files, configs):
        rel = (Path(ruff_home(files)) / "ruff.toml").as_posix()
        ref = check.config_ref(root, rel, root / COPY_DIR / check.RUFF_BASE)
        plan.writes[rel] = Template(template("ruff.toml.tmpl")).substitute(extend=ref)
    for f in [*(f for f, _ in configs), *check.eslint_configs(files)]:
        # 继承链上的其他配置读计划里的内容：两份配置共用一个末端时，第二份看到的是已补好的末端，不会重复改
        fix = check.lint_fix(root, f, plan.text(root, f), partial(plan.text, root))
        if fix.text is not None:
            plan.writes[fix.target] = fix.text
        add_once(plan.notes, fix.note)
        add_once(plan.tips, fix.tip)


def opencode_template(root: Path, files: list[str]) -> str:
    """init 生成的 opencode.jsonc 内容；取消 OpenCode 时据此判断文件是否被改过。"""
    return for_languages(template("opencode.jsonc.tmpl"), root, files)


def plan_opencode(root: Path, files: list[str], plan: Plan) -> None:
    configs = check.opencode_configs(root)
    if not configs:
        # 走到这里说明项目没有自己的 OpenCode 配置：按模板新建
        plan.writes["opencode.jsonc"] = opencode_template(root, files)
        return
    texts = {rel: plan.text(root, rel) for rel in configs}
    configured = [v for text in texts.values() for v in check.opencode_instruction_values(text)]
    missing = [ref for ref in check.rule_refs(root, files) if ref not in configured]
    if not missing:
        # 走到这里说明已有配置引用齐全
        return
    target = next((rel for rel, text in texts.items() if check.INSTRUCTIONS_ARRAY.search(text)), configs[0])
    appended = append_instructions(texts[target], missing)
    if appended is None:
        # 走到这里说明找不到能安全追加的数组：不冒险改用户的配置
        plan.notes.append(f"{target} 的 instructions 缺少 {'、'.join(missing)}：未修改，请手动加入")
        return
    plan.writes[target] = appended


JSON_STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')                 # JSON 字符串字面量（含转义）


def instructions_array(text: str) -> re.Match | None:
    """OpenCode 配置里能安全改写的 instructions 数组；数组不止一个、在注释里，或除字符串外还有别的内容
    （注释，或值里的 `]` 让数组被截断）时返回 None。"""
    arrays = list(check.INSTRUCTIONS_ARRAY.finditer(text))
    if len(arrays) != 1:
        return None
    match = arrays[0]
    before = text[: match.start()]
    line_start = before[before.rfind("\n") + 1:]
    if "//" in line_start or before.count("/*") > before.count("*/"):
        return None
    if not re.fullmatch(r"[\s,]*", JSON_STRING.sub("", match.group(1))):
        return None
    return match


def append_instructions(text: str, refs: list[str]) -> str | None:
    """在 OpenCode 配置唯一的 instructions 数组末尾追加 refs，其余文字逐字保留。
    没有能安全改写的数组（见 instructions_array），或追加后读出的值不等于原值加 refs 时返回 None。"""
    match = instructions_array(text)
    if match is None:
        return None
    body = match.group(1)
    head = body.rstrip()
    element = re.search(r'\n([ \t]*)"', body)
    pad = element.group(1) if element else "    "              # 单行或空数组时按模板的缩进
    has_items = bool(head)
    needs_comma = has_items and not head.endswith(",")
    sep = "," if needs_comma else ""
    added = ",".join(f'\n{pad}"{ref}"' for ref in refs)
    new = text[: match.start(1)] + head + sep + added + body[len(head):] + text[match.end(1):]
    if check.opencode_instruction_values(new) != check.opencode_instruction_values(text) + refs:
        return None
    return new


def plan_workflow_spec(root: Path, plan: Plan) -> None:
    path = root / check.WORKFLOW_SPEC
    if not path.is_file():
        plan.writes[check.WORKFLOW_SPEC] = template("workflow-gates-spec.md.tmpl")
        return
    text = plan.text(root, check.WORKFLOW_SPEC)
    # 各项目措辞不同(「…并审查」「…与独立审查」),按 requirement 标题前缀认定等价
    has_requirement = re.search(r"^### Requirement: Apply 后自动精简", text, re.M) is not None
    if f"{COPY_DIR}/rules/workflow-gates.md" not in text or not has_requirement:
        plan.notes.append(f"{check.WORKFLOW_SPEC} 已存在：未修改，需由 /{NAME} 合并「Apply 后自动精简并审查」requirement")


def plan_removed_entries(root: Path, files: list[str], old: list[str], new: list[str], plan: Plan) -> None:
    """取消的工具：删掉它的入口。CLAUDE.md 只删 rulemason:claude 块（删后为空就删文件）；opencode.jsonc 与模板相同才删。"""
    if "claude" in old and "claude" not in new:
        plan_drop_blocks(root, "CLAUDE.md", plan, "取消 Claude Code 后")
    if "opencode" in old and "opencode" not in new:
        generated = opencode_template(root, files)
        for rel in check.opencode_configs(root):
            if plan.text(root, rel) == generated:
                plan.deletes.append(rel)
            else:
                plan.notes.append(f"{rel} 改过，取消 OpenCode 后保留，请自行删去其中指向 {COPY_DIR}/ 的 instructions")


def drop_block(text: str, name: str) -> str:
    """删去标记块（含两行标记），收拢前后空行。没有该块原样返回；删完为空返回空串；不成对抛 BlockError。"""
    span = find_block(text, name)
    if span is None:
        return text
    rest = (text[: span[0]].rstrip("\n") + "\n\n" + text[span[1]:].lstrip("\n")).strip("\n")
    return rest + "\n" if rest else ""


def plan_drop_blocks(root: Path, rel: str, plan: Plan, why: str) -> None:
    """从 rel 删去它的全部 rulemason 标记块（见 check.BLOCKS）；删后为空就删文件，块不成对只报告。
    why 是写进提示的场合，如「取消 Claude Code 后」「卸载时」。"""
    if rel not in plan.writes and not (root / rel).is_file():
        return
    text = plan.text(root, rel)                             # 同一次 init 里前一步可能刚改过
    rest = text
    try:
        for name, _ in check.BLOCKS[rel]:
            rest = drop_block(rest, name)
    except BlockError as exc:
        plan.notes.append(f"{rel}：{exc}；{why}未删除，请自行处理")
        return
    if rest == text:
        # 走到这里说明没有 rulemason 标记块，不用动
        return
    if rest:
        plan.writes[rel] = rest
    else:
        plan.writes.pop(rel, None)
        plan.deletes.append(rel)


def plan_gitignore(root: Path, tools: list[str], copies: list[str], plan: Plan) -> None:
    """生成副本会被 .gitignore 挡住时，在文末追加放行规则：从被忽略的那一级目录起逐级放行，最后放行副本目录及其下全部文件，其余内容照旧忽略。"""
    if not has_git(root):
        return
    rel = ".gitignore"
    text = plan.text(root, rel) if rel in plan.writes or (root / rel).is_file() else ""
    added: list[str] = []
    for target in (COPY_DIR, *skill_dirs(tools)):
        if unsafe_targets(root, [target]):
            continue                                        # 目录是符号链接或在项目外：git 查不了，写入前的校验会报出来
        parts = Path(target).parts
        ancestors = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
        inside = [path for path in copies if path.startswith(f"{target}/")]
        # 目录路径带上 /：副本还没生成时，git 只对带 / 的路径套用「只匹配目录」的规则
        ignored = ignored_files(root, [*inside, *(f"{a}/" for a in ancestors)])
        if not any(path in ignored for path in inside):
            continue
        if f"!{target}/**" in text:
            # 走到这里说明放行规则已经写过，忽略来自别处（如子目录自己的 .gitignore）：不再重复追加，留给 check 报告
            continue
        top = next((a for a in ancestors if f"{a}/" in ignored), target)
        # 从被忽略的那一级起，每一级先放行目录再忽略其内容；最后放行副本目录与其下全部文件（文件级规则如 *.md 也能放行）
        for ancestor in ancestors[ancestors.index(top):-1]:
            added += [f"!{ancestor}/", f"{ancestor}/*"]
        added += [f"!{target}/", f"!{target}/**"]
    if not added:
        return
    block = f"\n# {NAME} 生成的副本要随项目提交；其余仍按上面的规则忽略\n" + "\n".join(dict.fromkeys(added)) + "\n"
    plan.writes[rel] = (text.rstrip("\n") + "\n" if text.strip() else "") + block


def plan_fill(root: Path, files: list[str], tools: list[str], copies: list[str], plan: Plan) -> None:
    """补齐用户自己的文件：缺的标记块、OpenCode 入口、lint 继承、.gitignore 放行；有 openspec/ 时再补方案写法基础规则、
    检查点提示与项目 workflow-gates 规格。init 与 update 共用。"""
    plan_blocks(root, files, tools, plan, create=True)
    if "opencode" in tools:
        plan_opencode(root, files, plan)
    if has_openspec(root):
        plan_artifact_rules(root, plan)
        plan_operations(root, plan)
        plan_workflow_spec(root, plan)
    plan_lint(root, files, plan)
    plan_gitignore(root, tools, copies, plan)


def build_plan(root: Path, manifest: dict | None, tools: list[str]) -> Plan:
    files = list_files(root)
    plan = Plan()
    record = (manifest or {}).get("files") or {}
    new_record = plan_copies(root, tools, check.copied_rules(root, files), record, plan)
    plan_stale_copies(root, record, new_record, plan)
    plan_removed_entries(root, files, (manifest or {}).get("tools") or [], tools, plan)
    plan_fill(root, files, tools, list(new_record), plan)
    plan_command_table(root, files, plan)
    plan_manifest(root, manifest, tools, new_record, plan)
    return plan


# ---------- 5. 跑 ----------

def untouched_dirty(root: Path, plan: Plan) -> int | None:
    """计划以外的未提交改动数；没有 git 时为 None。"""
    dirty = dirty_files(root)
    if dirty is None:
        return None
    return len([f for f in dirty if f not in plan.writes and f not in plan.deletes])


def is_modify(root: Path, rel: str) -> bool:
    """计划里的写入是改已有文件（否则是新增）。"""
    return (root / rel).exists()


INIT_DELETE_TITLE = "删除（内容未改动的旧副本与旧清单，或已取消工具的副本）"


def split_writes(root: Path, plan: Plan) -> tuple[list[str], list[str]]:
    """计划里的写入分成 (新增, 修改)。"""
    added = [rel for rel in plan.writes if not is_modify(root, rel)]
    return added, [rel for rel in plan.writes if rel not in added]


def untouched_line(root: Path, plan: Plan) -> str:
    untouched = untouched_dirty(root, plan)
    if untouched is None:
        return "不会碰：没有 git，无法统计未提交改动；计划以外的文件都不改"
    return f"不会碰：其余 {untouched} 个未提交改动不变"


def render_plan(root: Path, plan: Plan, delete_title: str = INIT_DELETE_TITLE) -> str:
    added, changed = split_writes(root, plan)
    lines = ["## 文件计划"]
    for title, items in (("新增", added), ("修改", changed), (delete_title, plan.deletes), ("覆盖手改过的副本", plan.overwritten)):
        if items:
            lines.append(f"{title}：")
            lines += [f"  - {rel}" for rel in items]
    lines.append(untouched_line(root, plan))
    lines += list_block("已跳过，需要你处理：", plan.notes)
    lines += list_block(TIPS_TITLE, plan.tips)
    return "\n".join(lines)


def _category(rel: str) -> str:
    if rel.startswith(f"{COPY_DIR}/lint/"):
        return "配置"
    if rel.startswith(f"{COPY_DIR}/"):
        return "规则副本"
    if f"skills/{NAME}/" in rel:
        return "skill"
    if rel in ("AGENTS.md", "CLAUDE.md", ".gitignore", MANIFEST) or rel.endswith("opencode.jsonc"):
        return "入口"
    return "配置"


def render_summary(root: Path, plan: Plan, delete_title: str = INIT_DELETE_TITLE) -> str:
    """交互确认时看的摘要：新增按类别计数，修改与删除逐个列出，再写不会碰的改动数与需要处理的事。"""
    added, changed = split_writes(root, plan)
    lines = [paint("## 文件计划", SKY_BOLD)]
    if added:
        counts = Counter(map(_category, added))
        lines.append(f"新增 {len(added)} 个文件：" + "、".join(f"{k} {v}" for k, v in counts.items()))
    for title, items in (("修改", changed), (delete_title, plan.deletes), ("覆盖手改过的副本", plan.overwritten)):
        if items:
            lines.append(f"{title} {len(items)} 个：" + "、".join(paint(rel, DIM) for rel in items))
    lines.append(untouched_line(root, plan))
    lines += list_block(paint(f"需要你处理 {len(plan.notes)} 项：", YELLOW), plan.notes)
    lines += list_block(TIPS_TITLE, plan.tips)
    return "\n".join(lines)


def plan_to_json(root: Path, plan: Plan, tools: list[str], openspec_init: bool) -> str:
    """init --plan --json 的输出：writes 按文件是否已存在标 add / modify。"""
    data = {
        "root": str(root),
        "tools": tools,
        "writes": [{"path": rel, "action": "modify" if is_modify(root, rel) else "add"} for rel in plan.writes],
        "deletes": plan.deletes,
        "overwritten": plan.overwritten,
        "notes": plan.notes,
        "untouched_dirty": untouched_dirty(root, plan),
        "openspec_init": openspec_init,
    }
    return dump_json(data)


def prepare(root: Path, tools_arg: str | None, plan_only: bool) -> tuple[dict | None, list[str]]:
    """预检、选工具，返回 (清单, 工具)；不满足条件抛 Stop。"""
    manifest = preflight(root, "init")
    if plan_only and tools_arg is None:
        # 走到这里说明只看计划：不提问，用清单记录的工具或按已有工具目录推断
        return manifest, default_tools(root, manifest)
    return manifest, choose_tools(root, manifest, tools_arg)


def print_plan(root: Path, plan: Plan, delete_title: str = INIT_DELETE_TITLE) -> bool:
    """打印完整文件计划（--plan 与 remove 用）；没有要改的文件时打印提示与跳过项。返回是否有要改的文件。"""
    if plan.writes or plan.deletes:
        print(render_plan(root, plan, delete_title))
        return True
    print("没有需要改动的文件。")
    print(bullets(plan.notes), end="")
    return False


def confirm_plan(root: Path, plan: Plan, yes: bool) -> bool:
    """交互确认：先看摘要，输入 d 展开完整清单后再问一次。--yes 只打印摘要。返回是否写入。"""
    print(render_summary(root, plan))
    if yes:
        return True
    while True:
        answer = input("按计划写入？ [y/N/d]（d 看完整清单） ").strip().lower()
        if answer == "d":
            print(render_plan(root, plan))
            continue
        return answer in YES


def show_plan(root: Path, plan: Plan, tools: list[str], as_json: bool) -> None:
    """init --plan：只打印计划，不写文件、不运行 openspec init。"""
    openspec_init = not has_openspec(root)
    if as_json:
        print(plan_to_json(root, plan, tools, openspec_init))
        return
    print("工具：" + ("、".join(tools) or "未选"))
    print_plan(root, plan)
    if openspec_init:
        print(f"将先询问是否运行 openspec init；不运行时只接入规则与 lint。{OPENSPEC_HINT}")
    print(f"只列计划，未写任何文件。确认后运行 {NAME} init --tools {','.join(tools) or '<id,...>'} --yes")


def report(root: Path, plan: Plan, with_openspec: bool) -> None:
    """写入之后的汇报：check 的结论一行、需要你处理的事、下一步；完整报告留给 rulemason check。"""
    try:
        text, _ = check.run(root)
    except ConfigError as exc:
        # 走到这里说明文件已写完，只是项目配置读不出来：照常收尾，不说成 init 失败
        text = f"check 未完成：{exc}；修正后运行 {NAME} check"
    print("\n" + paint(text.splitlines()[0], SKY_BOLD))
    if plan.writes or plan.deletes:
        print(paint("本次改动的文件：" + "、".join([*plan.writes, *plan.deletes]), DIM))
    print_notes(plan.notes, f"需要你处理 {len(plan.notes)} 项：")
    print_notes(plan.tips, TIPS_TITLE, color=None)
    if not with_openspec:
        print(OPENSPEC_HINT)
    print(NEXT_STEP)


MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")                  # Markdown 链接 [文字](网址)
LINK_LINE_REST = 10                                         # 去掉链接与分隔符后剩下的那一个词不超过这么多字，算语言切换 / 导航行
SENTENCE_END_ZH = "。！？"                                    # 中文句末标点；英文的 .!? 要看后面是不是空格，单独处理


def _links_only(text: str) -> bool:
    """段落只是一行链接（语言切换「中文 · [English](…)」、导航）：去掉链接与分隔符后只剩一个不超过 10 字的词、没有句末标点。
    剩下两个以上的词（如「A CLI for [OpenSpec](…)」）算正文。"""
    if not MD_LINK.search(text):
        return False
    without_links = MD_LINK.sub("", text)
    rest = re.sub(r"[·|/、,，]", " ", without_links).split()
    if len(rest) > 1:
        return False                                         # 剩两个以上的词，是正文
    word = "".join(rest)
    if len(word) > LINK_LINE_REST:
        return False
    return not re.search(rf"[{SENTENCE_END_ZH}.!?]", word)


def readme_intro(root: Path) -> str | None:
    """README 第一段正文截到两句；跳过标题、徽章、图片、链接行与语言切换 / 导航行；取不到返回 None。"""
    path = next((root / name for name in README_NAMES if (root / name).is_file()), None)
    if path is None:
        return None
    for paragraph in re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="replace")):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines or any(line.startswith(("#", "![", "<", "[![", "http", "---", ">", "|", "```", "=")) for line in lines):
            continue
        text = " ".join(lines)
        if _links_only(text):
            continue
        # 句末：中文标点，或后面是空格 / 行尾的英文标点（「Node.js」「v1.0」里的点不算）
        sentences = [m.group(0).strip() for m in re.finditer(rf"\S.*?(?:[{SENTENCE_END_ZH}]|[.!?](?=\s|$)|$)", text) if m.group(0).strip()]
        joiner = "" if sentences[0][-1] in SENTENCE_END_ZH else " "
        return joiner.join(sentences[:2])
    return None


def agents_template(root: Path) -> str:
    """新建 AGENTS.md 的内容：简介取自 README，取不到留占位。"""
    intro = readme_intro(root) or f"待 /{NAME} 补充：一两句话写这个项目是什么、给谁用。"
    return Template(template("AGENTS.md.tmpl")).safe_substitute(name=root.name, intro=intro)


def guide_key(root: Path) -> None:
    """交互 init 结尾：本机没有 key 时按判断条件提示或问一句；有 key 什么都不说。"""
    if engine.api_key():
        return
    if check.judge_blockers(root, check.archived(root)):
        print(f"判断功能需要 git 与至少 {check.MIN_ARCHIVED} 个已归档 change；满足后运行 {NAME} key 配置 Jev 的 key（申请：{KEY_URL}）")
        return
    if ask_yes(f"这个项目已满足开启判断的条件。现在配置 Jev 的 key（申请：{KEY_URL}）吗？"):
        key_cmd.run()
    else:
        print(f"以后运行 {NAME} key 即可配置。")


def run(root: Path, tools_arg: str | None, yes: bool, plan_only: bool = False, as_json: bool = False) -> int:
    try:
        # 1. 非交互环境写入时必须给全参数，不等待输入；只看计划不受限。交互运行先显示启动画面
        if not plan_only and not interactive() and (tools_arg is None or not yes):
            raise Stop("不是交互终端：请用 --tools <id,...> --yes 运行", 2)
        if not (yes or plan_only) and banner.interactive():
            banner.show(banner.INIT_FOOTER)
        # 2. 预检、选工具；只看计划时不运行 openspec init
        manifest, tools = prepare(root, tools_arg, plan_only)
        with_openspec = ensure_openspec(root, tools, yes) if not plan_only else has_openspec(root)
        # 3. 计划
        plan = build_plan(root, manifest, tools)
    except Stop as exc:
        print(str(exc))
        return exc.code
    if plan_only:
        show_plan(root, plan, tools, as_json)
        return 0

    # 4. 确认后写入
    if plan.writes or plan.deletes:
        if not confirm_plan(root, plan, yes):
            print("已取消，未写任何文件。")
            return 0
        try:
            apply(root, plan)
        except ValueError as exc:
            print(str(exc))
            return 1
    else:
        print_plan(root, plan)                                # 没有要改的文件：只打印提示与跳过项

    # 5. 汇报：结论、待办、下一步；交互时再引导配置 key
    report(root, plan, with_openspec)
    if not yes and interactive():
        guide_key(root)
    return 0
