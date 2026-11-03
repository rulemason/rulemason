"""rulemason init：在项目根接入共享规则——预检、选工具、生成副本与入口、补齐配置，列计划一次确认后写入。"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

import yaml

from rulemason import banner, check
from rulemason.check import BlockError, block_body, find_block, for_languages, markers
from rulemason.shared import (
    COPY_DIR,
    MANIFEST,
    NAME,
    TOOL_IDS,
    TOOL_LABELS,
    ConfigError,
    ManifestError,
    bullets,
    dirty_files,
    dump_json,
    generated_files,
    has_git,
    is_source_repo,
    list_files,
    manifest_text,
    normalize_tools,
    read_manifest,
    sha256_file,
    sha256_text,
    skill_dirs,
    template,
    write_text,
)

TOOL_DIRS = {".opencode": "opencode", ".claude": "claude", ".cursor": "cursor", ".agents": "codex"}   # 已有目录 → 预勾选
OPENSPEC_INSTALL = "npm install -g @fission-ai/openspec@latest"
ROW_NAMES = ("判断", "ruff", "测试", "前端 lint", "文案检查")
NEXT_STEP = f"下一步：在 AI 工具中运行 /{NAME}，补项目简介、红线并确认命令表。"


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

    def text(self, root: Path, rel: str) -> str:
        """计划里已改过的内容优先（同一次 init 里前一步刚改过的文件），否则读磁盘。"""
        if rel in self.writes:
            return self.writes[rel]
        return (root / rel).read_text(encoding="utf-8")


def interactive() -> bool:
    return sys.stdin.isatty()


def ask_yes(question: str) -> bool:
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes", "是")


# ---------- 1. 标记块（init 与 update 共用） ----------

def set_block(text: str, name: str, body: str, heading: str | None) -> str:
    """把标记块内容换成 body；没有标记块时插到 heading 标题下，没有该标题就在文末新建（heading 为 None 直接加在文末）。"""
    start, end = markers(name)
    block = f"{start}\n{body}{end}"
    span = find_block(text, name)
    if span:
        return text[: span[0]] + block + text[span[1]:]
    match = re.search(rf"^##\s+{re.escape(heading)}.*$", text, re.M) if heading else None
    if match:
        return text[: match.end()] + "\n\n" + block + text[match.end():]
    title = f"## {heading}\n\n" if heading else ""
    prefix = text.rstrip("\n") + "\n\n" if text.strip() else ""
    return f"{prefix}{title}{block}\n"


def plan_blocks(root: Path, files: list[str], tools: list[str], plan: Plan, create: bool) -> None:
    """AGENTS.md 的两个标记块与 CLAUDE.md 的 rulemason:claude 块。
    create=False 时只刷新块齐全的文件；缺文件或缺块的交给 create=True（补齐计划）处理。"""
    for rel, blocks in check.block_targets(tools):
        path = root / rel
        if not path.is_file() and not create:
            continue
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        base = plan.writes.get(rel, current)                 # 前一步已改过该文件时，以改后的内容为起点
        text = base or (Template(template("AGENTS.md.tmpl")).safe_substitute(name=root.name) if rel == "AGENTS.md" else "")
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
        if rel == "CLAUDE.md" and find_block(base, "claude") is None and "@AGENTS.md" in base:
            plan.notes.append(f"CLAUDE.md 在 {NAME}:claude 块外已有 @AGENTS.md，与块内重复导入：请删去块外那一行")
        if text != current:
            plan.writes[rel] = text


# ---------- 2. 生成副本（init 与 update 共用） ----------

def plan_copies(root: Path, tools: list[str], record: dict[str, str], plan: Plan) -> dict[str, str]:
    """把已选工具的副本刷新为当前版本；返回新的校验值记录。被手改过的副本照样覆盖，并记进 overwritten。"""
    files = generated_files(tools)
    for rel, content in files.items():
        path = root / rel
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        if path.is_file() and rel in record and sha256_file(path) != record[rel]:
            plan.overwritten.append(rel)
        plan.writes[rel] = content
    return {rel: sha256_text(content) for rel, content in files.items()}


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


def default_tools(root: Path, manifest: dict | None) -> list[str]:
    if manifest is not None:
        return list(manifest["tools"])
    return normalize_tools([tool for d, tool in TOOL_DIRS.items() if (root / d).is_dir()])


def ask_tools(defaults: list[str]) -> list[str]:
    """打印带编号、已预勾选的清单；输入编号（逗号分隔），直接回车保持默认。"""
    print("选择本项目使用的 AI 工具（输入编号，逗号分隔；直接回车保持默认）：")
    for i, tool in enumerate(TOOL_IDS, 1):
        print(f"  {i}. [{'x' if tool in defaults else ' '}] {TOOL_LABELS[tool]}（{tool}）")
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
    return ask_tools(default_tools(root, manifest))


def ensure_openspec(root: Path, tools: list[str], yes: bool) -> None:
    """没有 openspec/ 时询问后代为运行 openspec init；拒绝、命令不存在或失败时抛 Stop。"""
    if (root / "openspec").is_dir():
        return
    if shutil.which("openspec") is None:
        raise Stop(f"项目没有 openspec/，本机也没有 openspec 命令。先安装：{OPENSPEC_INSTALL}，再运行 {NAME} init")
    command = ["openspec", "init", "--tools", ",".join(tools), "--language", "zh-CN"]
    if not yes and not ask_yes(f"项目没有 openspec/，现在运行 `{' '.join(command)}`？"):
        raise Stop(f"未运行 openspec init，{NAME} 需要 openspec/：未写任何文件", 0)
    sys.stdout.flush()                                      # 先输出前面的提示，再让 openspec 直接写终端
    if subprocess.run(command, cwd=root).returncode != 0:
        raise Stop(f"openspec init 失败（输出见上），{NAME} 未写任何文件")


# ---------- 4. 只在 init 做的计划：工具增删、命令表、配置 ----------

def plan_stale_copies(root: Path, record: dict[str, str], current: dict[str, str], plan: Plan) -> None:
    """清单记录过、当前版本不再生成的副本（取消了工具，或副本清单缩减）：与记录一致就删，手改过的保留并报告。
    清单只是仓库里的文本，记录的路径不在副本目录里就不碰。"""
    managed = (f"{COPY_DIR}/", *(f"{d}/" for d in skill_dirs(list(TOOL_IDS))))
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
    values = ("判断层未装", "；".join(ruff) or skip, "；".join(tests) or skip, "；".join(front) or skip, "判断层未装")
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


def _insert_ruff_extend(name: str, text: str, ref: str) -> str:
    line = f'extend = "{ref}"   # 选用规则与复杂度来自 {NAME} 基础配置的项目内副本\n'
    text = text if text.endswith("\n") else text + "\n"      # 末行没有换行时，插入行会被并进注释或表头
    if name == "ruff.toml":
        lines = text.splitlines(keepends=True)
        at = next((i for i, l in enumerate(lines) if l.strip() and not l.lstrip().startswith("#")), len(lines))
        return "".join(lines[:at] + [line] + lines[at:])
    header = re.search(r"^\[tool\.ruff\][ \t]*(#[^\n]*)?\n", text, re.M)
    if header:
        return text[: header.end()] + line + text[header.end():]
    sub = re.search(r"^\[tool\.ruff\.", text, re.M)
    if sub is None:
        raise ValueError("找不到 [tool.ruff] 表头")
    return text[: sub.start()] + "[tool.ruff]\n" + line + "\n" + text[sub.start():]


def config_ref(root: Path, config: str, target: Path) -> str:
    """配置文件里指向 target 的相对路径；ESLint 的 import 不带 ./ 会被当成包名，补上。"""
    ref = Path(os.path.relpath(target, (root / config).parent)).as_posix()
    if target.suffix == ".mjs" and not ref.startswith("."):
        return f"./{ref}"
    return ref


def plan_lint(root: Path, files: list[str], plan: Plan) -> None:
    """ruff 与 ESLint 继承 .rulemason/lint/；已有 select、其他 extend 或无法识别的 ESLint 格式只报告。"""
    base = root / COPY_DIR / "lint"
    configs = check.ruff_configs(root, files)
    if check.has_python(files) and not configs:
        plan.writes["ruff.toml"] = template("ruff.toml.tmpl")
    for f, text in configs:
        text = plan.text(root, f)
        if check.ruff_shared_refs(root, f, text):
            continue
        if check.has_select(text):
            plan.notes.append(f"{f} 写了 select，会覆盖基础规则：未修改，请删去 select 后重跑 {NAME} init")
        elif re.search(r"^\s*extend\s*=", text, re.M):
            plan.notes.append(f"{f} 已继承其他 ruff 配置：未修改，请改为继承 {COPY_DIR}/lint/ruff-base.toml")
        else:
            ref = config_ref(root, f, base / "ruff-base.toml")
            try:
                plan.writes[f] = _insert_ruff_extend(Path(f).name, text, ref)
            except ValueError as exc:
                plan.notes.append(f"{f} 无法安全写入 extend（{exc}）：未修改，请手动继承 {COPY_DIR}/lint/ruff-base.toml")
    for f in check.eslint_configs(files):
        text = plan.text(root, f)
        if check.eslint_shared_refs(root, f, text):
            continue
        ref = config_ref(root, f, base / "eslint-base.mjs")
        if Path(f).name.startswith(".eslintrc") or text.count("export default [") != 1:
            plan.notes.append(f"{f} 的格式无法自动识别：未修改，请手动 import \"{ref}\" 并展开进 rules")
            continue
        imported = f'import rulemasonBase from "{ref}";\n'
        first_import = re.search(r"^import\s", text, re.M)
        at = first_import.start() if first_import else text.index("export default [")
        text = text[:at] + imported + text[at:]
        plan.writes[f] = text.replace("export default [", "export default [\n  { rules: rulemasonBase },", 1)


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


def plan_fill(root: Path, files: list[str], tools: list[str], plan: Plan) -> None:
    """补齐用户自己的文件：缺的标记块、OpenCode 入口、方案写法基础规则、检查点提示、lint 继承、项目 workflow-gates 规格。init 与 update 共用。"""
    plan_blocks(root, files, tools, plan, create=True)
    if "opencode" in tools:
        plan_opencode(root, files, plan)
    plan_artifact_rules(root, plan)
    plan_operations(root, plan)
    plan_lint(root, files, plan)
    plan_workflow_spec(root, plan)


def build_plan(root: Path, manifest: dict | None, tools: list[str]) -> Plan:
    files = list_files(root)
    plan = Plan()
    record = (manifest or {}).get("files") or {}
    new_record = plan_copies(root, tools, record, plan)
    plan_stale_copies(root, record, new_record, plan)
    plan_removed_entries(root, files, (manifest or {}).get("tools") or [], tools, plan)
    plan_fill(root, files, tools, plan)
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


def render_plan(root: Path, plan: Plan, delete_title: str = INIT_DELETE_TITLE) -> str:
    added = [rel for rel in plan.writes if not is_modify(root, rel)]
    changed = [rel for rel in plan.writes if is_modify(root, rel)]
    lines = ["## 文件计划"]
    for title, items in (("新增", added), ("修改", changed), (delete_title, plan.deletes), ("覆盖手改过的副本", plan.overwritten)):
        if items:
            lines.append(f"{title}：")
            lines += [f"  - {rel}" for rel in items]
    untouched = untouched_dirty(root, plan)
    if untouched is None:
        lines.append("不会碰：没有 git，无法统计未提交改动；计划以外的文件都不改")
    else:
        lines.append(f"不会碰：其余 {untouched} 个未提交改动不变")
    if plan.notes:
        lines.append("已跳过，需要你处理：")
        lines += [f"  - {note}" for note in plan.notes]
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
    """打印文件计划；没有要改的文件时打印提示与跳过项。返回是否有要改的文件。"""
    if plan.writes or plan.deletes:
        print(render_plan(root, plan, delete_title))
        return True
    print("没有需要改动的文件。")
    print(bullets(plan.notes), end="")
    return False


def show_plan(root: Path, plan: Plan, tools: list[str], as_json: bool) -> None:
    """init --plan：只打印计划，不写文件、不运行 openspec init。"""
    openspec_init = not (root / "openspec").is_dir()
    if as_json:
        print(plan_to_json(root, plan, tools, openspec_init))
        return
    print("工具：" + ("、".join(tools) or "未选"))
    print_plan(root, plan)
    if openspec_init:
        print("将先运行 openspec init；方案写法规则在那之后补齐。")
    print(f"只列计划，未写任何文件。确认后运行 {NAME} init --tools {','.join(tools) or '<id,...>'} --yes")


def report(root: Path, plan: Plan) -> None:
    """写入之后的汇报：check 结果、本次改动的文件、下一步。"""
    try:
        text, _ = check.run(root)
    except ConfigError as exc:
        # 走到这里说明文件已写完，只是项目配置读不出来：照常收尾，不说成 init 失败
        text = f"check 未完成：{exc}；修正后运行 {NAME} check"
    print("\n" + text + "\n")
    if plan.writes or plan.deletes:
        print("本次改动的文件：" + "、".join([*plan.writes, *plan.deletes]))
    print(NEXT_STEP)


def run(root: Path, tools_arg: str | None, yes: bool, plan_only: bool = False, as_json: bool = False) -> int:
    try:
        # 1. 非交互环境写入时必须给全参数，不等待输入；只看计划不受限。交互运行先显示启动画面
        if not plan_only and not interactive() and (tools_arg is None or not yes):
            raise Stop("不是交互终端：请用 --tools <id,...> --yes 运行", 2)
        if not (yes or plan_only) and banner.interactive():
            banner.show(banner.INIT_FOOTER)
        # 2. 预检、选工具；只看计划时不运行 openspec init
        manifest, tools = prepare(root, tools_arg, plan_only)
        if not plan_only:
            ensure_openspec(root, tools, yes)
        # 3. 计划
        plan = build_plan(root, manifest, tools)
    except Stop as exc:
        print(str(exc))
        return exc.code
    if plan_only:
        show_plan(root, plan, tools, as_json)
        return 0

    # 4. 确认后写入
    if print_plan(root, plan):
        if not yes and not ask_yes("按计划写入？"):
            print("已取消，未写任何文件。")
            return 0
        try:
            apply(root, plan)
        except ValueError as exc:
            print(str(exc))
            return 1

    # 5. 汇报：check 结果、改动清单、下一步
    report(root, plan)
    return 0
