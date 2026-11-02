"""rulemason check：只读识别项目与接入状态，第一行给「阶段：下一步」，再输出识别表、各层状态与巡检，并按结果给退出码。"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from string import Template

from rulemason import __version__
from rulemason import judge as engine
from rulemason.shared import (
    COPY_DIR,
    MANIFEST,
    NAME,
    OLD_COPY_DIR,
    OLD_MANIFEST,
    OLD_NAME,
    TOOL_LABELS,
    ConfigError,
    ManifestError,
    Scan,
    dirty_files,
    dump_json,
    has_git,
    ignored_files,
    is_source_repo,
    parse_version,
    read_judgments,
    read_manifest,
    read_yaml,
    scan,
    sha256_file,
    shared_root,
    skill_dirs,
    template,
    unmigrated,
)

LANGUAGE_RULES = ("rules/python.md", "rules/react.md")       # 按项目语言决定是否引用的落法，顺序即入口里的顺序
INSTRUCTIONS_ARRAY = re.compile(r'"instructions"\s*:\s*\[(.*?)\]', re.S)   # OpenCode 配置里的 instructions 数组（只取这一项，不解析整份 JSONC）
DEPENDENCY_KEYS = ("dependencies", "devDependencies", "peerDependencies")   # 判断 React 目录时看的 package.json 依赖段
ENGINE_BASE = Path(engine.__file__).parent / "base"      # 引擎自带的通用规则与通用词表
SHOWN_SKIPPED = 10                                          # 识别表「跳过」一行最多列出的目录数
MIN_ARCHIVED = 3                                            # 判断层至少要这么多已归档 change 作测试用例
LOCKFILES = (("uv", "uv.lock"), ("pip", "requirements.txt"), ("pnpm", "pnpm-lock.yaml"), ("npm", "package-lock.json"))
LEGACY_REF = f"../{OLD_NAME}/"                               # 0.4 及更早的旧接入方式：引用同级目录的 rulekit 仓库
SKILL_ENTRIES = (f".claude/skills/{NAME}", f".agents/skills/{NAME}")
LEGACY_SKILL_ENTRIES = (f".claude/skills/{OLD_NAME}", f".agents/skills/{OLD_NAME}")   # 0.4 时是指向项目外的符号链接
PENDING_MARKS = (f"待 /{NAME} 补充", "自动识别，请确认")      # init 留给 /rulemason 补的内容
LEGACY_FINDING = "旧接入方式（需迁移）"
RESIDUE_FINDING = "旧名残留"
INVALID = "配置无效"
TO_MIGRATE = f"未迁移（{OLD_NAME} 0.5 格式）"
WORKFLOW_SPEC = "openspec/specs/workflow-gates/spec.md"
RESIDUE_NAMES = (f"{OLD_COPY_DIR}/", "jev-judge", f"skills/{OLD_NAME}")   # 入口与配置里不该再出现的旧名
MANAGED_BLOCK = re.compile(rf"<!-- ({NAME}|{OLD_NAME}):([\w-]+) -->.*?<!-- /\1:\2 -->", re.S)   # 标记块内由工具刷新，不算残留


@dataclass
class Report:
    facts: list[tuple[str, str]] = field(default_factory=list)       # 识别表
    layers: dict[str, list[str]] = field(default_factory=dict)       # 层名 → 缺失项；空表示已装好
    findings: list[tuple[str, list[str]]] = field(default_factory=list)   # 巡检项 → 偏离；空表示一致


@dataclass
class Selection:
    """已选工具与 manifest 状态；manifest 为 None 表示没有或无效，problems 说明原因。"""
    tools: list[str]
    label: str
    problems: list[str]
    manifest: dict | None


class BlockError(ValueError):
    """标记块不成对或缺失，无法安全写入该文件。"""


BLOCKS = {                                                   # 文件 → (块名, 没有块时插在哪个二级标题下)
    "AGENTS.md": (("code-style", "Code style"), ("workflow-gates", "Workflow gates")),
    "CLAUDE.md": (("claude", None),),
}
IGNORED_COPY = "被 .gitignore 忽略，无法随项目提交"
STALE_BLOCK = "标记块与当前模板不一致（被手改，或项目新增了语言）"


# ---------- 1. 读项目 ----------

def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _dirs_with(files: list[str], names: tuple[str, ...]) -> list[str]:
    return sorted({str(Path(f).parent) for f in files if Path(f).name in names})


def markers(name: str) -> tuple[str, str]:
    return f"<!-- {NAME}:{name} -->", f"<!-- /{NAME}:{name} -->"


def find_block(text: str, name: str) -> tuple[int, int] | None:
    """标记块的 (起点, 终点) 下标；没有返回 None，不成对抛 BlockError。"""
    start, end = markers(name)
    n_start, n_end = text.count(start), text.count(end)
    if n_start == n_end == 0:
        return None
    if n_start != 1 or n_end != 1 or text.index(start) > text.index(end):
        raise BlockError(f"{NAME}:{name} 标记块不成对")
    return text.index(start), text.index(end) + len(end)


def language_rules(root: Path, files: list[str]) -> list[str]:
    """项目实际用到的语言落法：有 Python 要 python.md，有 React 目录要 react.md。"""
    used = {"rules/python.md": has_python(files), "rules/react.md": bool(react_dirs(root, files))}
    return [rule for rule in LANGUAGE_RULES if used[rule]]


def for_languages(text: str, root: Path, files: list[str]) -> str:
    """去掉模板里项目用不到的语言落法的引用行。"""
    absent = set(LANGUAGE_RULES) - set(language_rules(root, files))
    return "".join(line for line in text.splitlines(keepends=True) if not any(ref in line for ref in absent))


def block_body(name: str, root: Path, files: list[str]) -> str:
    """标记块在当前版本下应有的内容。"""
    return for_languages(template(f"{name}.block.md"), root, files)


def block_targets(tools: list[str]) -> list[tuple[str, tuple[tuple[str, str | None], ...]]]:
    """已选工具要有的标记块：AGENTS.md 总有，CLAUDE.md 只在选了 Claude Code 时有。"""
    return [(rel, blocks) for rel, blocks in BLOCKS.items() if rel != "CLAUDE.md" or "claude" in tools]


def stale_blocks(root: Path, files: list[str], manifest: dict) -> list[tuple[str, str]]:
    """与当前模板不一致的标记块 (文件, 块名)：清单版本与本机相同、块内容却与模板不同（被手改，或项目后来加了 Python 或 React）。
    版本不同的差异是正常升级，不算。"""
    if str(manifest.get(NAME)) != __version__:
        return []
    out = []
    for rel, blocks in block_targets(manifest["tools"]):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        for name, _ in blocks:
            try:
                span = find_block(text, name)
            except BlockError:
                continue                                    # 不成对由入口检查报告
            if span is None:
                continue
            start, end = markers(name)
            inside = text[span[0] + len(start): span[1] - len(end)]
            if inside.strip("\n") != block_body(name, root, files).strip("\n"):
                out.append((rel, name))
    return out


def has_python(files: list[str]) -> bool:
    return any(f.endswith(".py") for f in files)


def react_dirs(root: Path, files: list[str]) -> list[str]:
    """依赖里有 react 的 package.json 所在目录（项目根记为「.」）；package.json 读不出来时抛 ConfigError。"""
    dirs = []
    for f in files:
        if Path(f).name != "package.json":
            continue
        try:
            data = json.loads(_read(root, f))
        except ValueError as exc:                                 # 含 JSONDecodeError 与 UnicodeDecodeError
            raise ConfigError(f"{f} 不是合法的 JSON（{exc}）") from exc
        deps = [data.get(key) for key in DEPENDENCY_KEYS] if isinstance(data, dict) else []
        if any(isinstance(d, dict) and "react" in d for d in deps):
            dirs.append(str(Path(f).parent))
    return sorted(dirs)


def shared_ref(root: Path, path: str) -> str:
    """指令与配置中应写的共享路径：源码仓库本身直接引用，其他项目引用 .rulemason/ 副本。"""
    if is_source_repo(root):
        return path
    return f"{COPY_DIR}/{path}"


def rule_refs(root: Path, files: list[str]) -> list[str]:
    """项目应加载的共享正文：九条、用到的语言落法、workflow-gates。"""
    refs = ["rules/code-style.md", *language_rules(root, files), "rules/workflow-gates.md"]
    return [shared_ref(root, ref) for ref in refs]


def tool_selection(root: Path) -> Selection:
    try:
        manifest = read_manifest(root)
    except ManifestError as exc:
        return Selection([], INVALID, [str(exc)], None)
    if unmigrated(root, manifest):
        # 走到这里说明是 rulekit 0.5 的项目，还没迁移到新格式
        return Selection([], TO_MIGRATE, [f"有 {OLD_MANIFEST}：运行 {NAME} init 迁移格式"], None)
    if manifest is None:
        return Selection([], f"未选择（缺少 {MANIFEST}）", [f"没有 {MANIFEST}：先运行 {NAME} init"], None)
    tools = manifest["tools"]
    return Selection(tools, "、".join(TOOL_LABELS[t] for t in tools) or "未选择", [], manifest)


def skipped_label(skipped: list[tuple[str, str]]) -> str:
    """「目录（原因）」，多于 SHOWN_SKIPPED 个只列前面的并写总数；没有写「—」。"""
    shown = "、".join(f"{d}（{reason}）" for d, reason in skipped[:SHOWN_SKIPPED])
    if len(skipped) > SHOWN_SKIPPED:
        return f"{shown} 等共 {len(skipped)} 个"
    return shown or "—"


def archived(root: Path) -> int:
    d = root / "openspec/changes/archive"
    return sum(1 for p in d.iterdir() if p.is_dir()) if d.is_dir() else 0


def ci_files(files: list[str]) -> list[str]:
    return [f for f in files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]


def ci_refs(root: Path, files: list[str]) -> list[tuple[str, str]]:
    """CI 里检出或安装 rulemason 时钉的 ref，返回 (工作流文件, ref) 列表。"""
    patterns = (
        r"repository:\s*rulemason/rulemason\s*\n\s*ref:\s*(\S+)",
        r"github\.com/rulemason/rulemason@([^\s#'\"]+)",
        r"(?<![\w.-])rulemason==([^\s#'\"]+)",     # 前面不能是名字字符，免得把 foo-rulemason== 认成钉版本
    )
    out: list[tuple[str, str]] = []
    for f in ci_files(files):
        text = _read(root, f)
        for pattern in patterns:
            for m in re.finditer(pattern, text):
                if (f, m.group(1)) not in out:
                    out.append((f, m.group(1)))
    return out


def identify(root: Path, scanned: Scan, n_archived: int, sel: Selection, entry_issues: list[str], report: Report) -> None:
    """识别表：项目根、语言与包管理、目录与跳过的目录、openspec、归档数、CI、未提交改动、工具与版本。"""
    files = scanned.files
    report.facts.append(("项目根", str(root)))
    # 1. 语言与包管理
    names = {Path(f).name for f in files}
    managers = [m for m, lock in LOCKFILES if lock in names]
    langs = [lang for lang, ok in (("Python", has_python(files)), ("JS/TS", "package.json" in names)) if ok]
    report.facts.append(("语言", "、".join(langs) or "未识别"))
    report.facts.append(("包管理", "、".join(managers) or "无锁文件"))

    # 2. 目录
    report.facts.append(("Python 目录", "、".join(_dirs_with(files, ("pyproject.toml", "requirements.txt"))) or "—"))
    react = react_dirs(root, files)
    front = [f"{d}（React）" if d in react else d for d in _dirs_with(files, ("package.json",))]
    report.facts.append(("前端目录", "、".join(front) or "—"))
    report.facts.append(("跳过", skipped_label(scanned.skipped)))

    # 3. openspec、CI、工作区
    report.facts.append(("openspec", "有" if (root / "openspec").is_dir() else "无"))
    report.facts.append(("已归档 change", str(n_archived)))
    report.facts.append(("判断", judge_label(root, n_archived)))
    refs = ci_refs(root, files)
    if refs:
        ci = "、".join(f"{f} 钉 {r}" for f, r in refs)
    elif ci_files(files):
        ci = f"有，未引用 {NAME}"
    else:
        ci = "无"
    report.facts.append(("CI", ci))
    dirty = dirty_files(root)
    if dirty is None:
        report.facts.append(("未提交改动", "无 git，无法统计"))
    else:
        report.facts.append(("未提交改动", f"{len(dirty)} 个文件" if dirty else "无"))

    # 4. 工具与版本
    report.facts.append(("已选工具", sel.label))
    status = "未选择" if not sel.tools else "一致"
    if entry_issues:
        status = f"缺 {len(entry_issues)} 项"
    report.facts.append(("工具适配", status))
    recorded = (sel.manifest or {}).get(NAME, "—")
    report.facts.append((f"{NAME} 版本", f"项目记录 {recorded}，本机 {__version__}"))


# ---------- 2. 各层状态 ----------

def _section(text: str, heading: str) -> str | None:
    match = re.search(rf"^##\s+{re.escape(heading)}.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return match.group(1) if match else None


def check_agents(root: Path, files: list[str]) -> list[str]:
    """通用 AGENTS.md 的规则标题、共享路径与文件可达性。"""
    path = root / "AGENTS.md"
    if not path.exists():
        return ["没有 AGENTS.md"]
    text = path.read_text(encoding="utf-8")
    missing = []
    refs = rule_refs(root, files)
    checks = [("Workflow gates" if ref.endswith("workflow-gates.md") else "Code style", ref) for ref in refs]
    for heading, ref in checks:
        section = _section(text, heading)
        if section is None:
            missing.append(f"AGENTS.md 没有「## {heading}」")
        elif ref not in section:
            missing.append(f"「## {heading}」下没有引入 {ref}")
        elif not (root / ref).is_file():
            missing.append(f"共享规则文件不存在：{ref}")
    return list(dict.fromkeys(missing))


def opencode_configs(root: Path) -> list[str]:
    candidates = (".opencode/opencode.jsonc", ".opencode/opencode.json", "opencode.jsonc", "opencode.json")
    return [rel for rel in candidates if (root / rel).is_file()]


def opencode_instruction_values(text: str) -> list[str]:
    """从 JSONC 的 instructions 数组取路径；不解析或修改其他配置项。"""
    values = []
    for match in INSTRUCTIONS_ARRAY.finditer(text):
        values.extend(re.findall(r'"([^"\n]+)"', match.group(1)))
    return values


def _check_opencode(root: Path, refs: list[str]) -> list[str]:
    configs = opencode_configs(root)
    if not configs:
        return ["OpenCode 缺少 opencode.json(c) 配置"]
    configured = [value for rel in configs for value in opencode_instruction_values(_read(root, rel))]
    return [f"OpenCode instructions 未引用 {ref}" for ref in refs if ref not in configured]


def _check_skill(root: Path, tool: str, entry: str) -> list[str]:
    if not (root / entry / "SKILL.md").is_file():
        return [f"{TOOL_LABELS[tool]} 缺少 skill：{entry}/SKILL.md"]
    return []


def check_tool_entries(root: Path, files: list[str], tools: list[str]) -> list[str]:
    """只检查已选工具的入口：CLAUDE.md 导入、OpenCode instructions、skill 文件。"""
    problems = []
    refs = rule_refs(root, files)
    if "claude" in tools:
        claude = root / "CLAUDE.md"
        if not claude.is_file():
            problems.append("Claude Code 缺少 CLAUDE.md")
        else:
            text = claude.read_text(encoding="utf-8")
            problems += [f"CLAUDE.md 未导入 {ref}" for ref in ["AGENTS.md", *refs] if f"@{ref}" not in text]
        problems += _check_skill(root, "claude", SKILL_ENTRIES[0])
    if "opencode" in tools:
        problems += _check_opencode(root, refs)
    agents_tool = next((tool for tool in ("opencode", "cursor", "codex") if tool in tools), None)
    if agents_tool:
        problems += _check_skill(root, agents_tool, SKILL_ENTRIES[1])
    return problems


def copy_issues(root: Path, sel: Selection) -> list[str]:
    """已选工具应有的生成副本：缺失、与 .rulemason.yaml 记录的校验值不符，或在 git 仓库里被忽略。"""
    if sel.manifest is None:
        return []
    record = sel.manifest.get("files") or {}
    if not record:
        return [f"{MANIFEST} 没有记录生成副本：运行 {NAME} init"]
    managed = (f"{COPY_DIR}/", *(f"{d}/" for d in skill_dirs(sel.tools)))
    problems = []
    rels = [rel for rel in record if rel.startswith(managed)]
    for rel in rels:
        # 以项目记录为准：本机版本新增的文件不算缺失，版本落后只在巡检里报告
        path = root / rel
        if not path.is_file():
            problems.append(f"缺少生成副本：{rel}")
        elif sha256_file(path) != record[rel]:
            problems.append(f"与记录的校验值不符（被手改）：{rel}")
    if has_git(root):
        # 副本被忽略就进不了仓库，克隆项目的人、云端 agent 与 CI 都读不到
        problems += [f"{IGNORED_COPY}：{rel}" for rel in ignored_files(root, rels)]
    return problems


def project_artifact_rules(root: Path) -> dict:
    return read_yaml(root / "openspec/config.yaml", {}).get("rules") or {}


def base_artifact_rules() -> dict:
    return read_yaml(shared_root() / "openspec-base/artifact-rules.yaml", {}).get("rules") or {}


def artifact_rules_diff(root: Path) -> list[str]:
    """项目 config.yaml 的 rules 是否包含基础版每一条（一字不差）；项目追加的条目不算偏离。"""
    project = project_artifact_rules(root)
    if not project:
        # 走到这里说明整段 rules 都没有，已记在接入那一层，不再逐条重复
        return []
    missing = []
    for artifact, items in base_artifact_rules().items():
        have = project.get(artifact) or []
        missing += [f"rules.{artifact} 缺少或改写了：{item[:30]}…" for item in items if item not in have]
    return missing


def base_operations(root: Path) -> dict:
    """OpenSpec operations 基础版（与 config.yaml 同结构：操作 → guidance 列表），检查点路径按项目代入（源码仓库直接引用 rules/）。"""
    raw = read_yaml(shared_root() / "openspec-base/operations.yaml", {}).get("operations") or {}
    gates = shared_ref(root, "rules/workflow-gates.md")
    return {op: {"guidance": [Template(item).substitute(gates=gates) for item in body["guidance"]]} for op, body in raw.items()}


def operations_diff(root: Path) -> list[str]:
    """项目 config.yaml 的 operations 是否含基础版每一条；项目追加的条目不算偏离。"""
    path = root / "openspec/config.yaml"
    if not path.is_file():
        # 走到这里说明没有 config.yaml，接入层已报过
        return []
    config = read_yaml(path, {})
    if "operations" not in config:
        return ["openspec/config.yaml 没有 operations（apply / archive 时给 AI 的检查点提示）"]
    project = config["operations"]
    if not isinstance(project, dict):
        # 走到这里说明段存在但为空或不是映射：update 不会改它，只能手动补
        return ["openspec/config.yaml 的 operations 为空或不是映射：请手动补上基础条目"]
    missing = []
    for op, body in base_operations(root).items():
        entry = project.get(op)
        guidance = entry.get("guidance") if isinstance(entry, dict) else None
        have = guidance if isinstance(guidance, list) else []            # 写成字符串时不按子串比较
        missing += [f"operations.{op} 缺少：{item[:30]}…" for item in body["guidance"] if item not in have]
    return missing


def ruff_configs(root: Path, files: list[str]) -> list[tuple[str, str]]:
    """(文件, 内容) 列表：ruff.toml，以及含 [tool.ruff] 的 pyproject.toml。"""
    out = []
    for f in files:
        name = Path(f).name
        if name not in ("ruff.toml", "pyproject.toml"):
            continue
        text = _read(root, f)
        if name == "ruff.toml" or "[tool.ruff" in text:
            out.append((f, text))
    return out


def eslint_configs(files: list[str]) -> list[str]:
    return [f for f in files if Path(f).name.startswith(("eslint.config.", ".eslintrc"))]


def _resolves_to(root: Path, file: str, ref: str, canonical: str) -> bool:
    """配置中的相对路径按配置文件目录解析，并与项目应引用的共享文件比较。"""
    target = Path(ref).expanduser()
    if not target.is_absolute():
        target = (root / file).parent / ref
    return target.resolve() == (root / shared_ref(root, canonical)).resolve()


def ruff_shared_refs(root: Path, file: str, text: str) -> list[str]:
    """ruff 配置 extend 里指向共享基础配置的引用原文。"""
    match = re.search(r"^\s*extend\s*=\s*(.+)$", text, re.M)
    refs = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)) if match else []
    return [ref for ref in refs if _resolves_to(root, file, ref, "lint/ruff-base.toml")]


def eslint_shared_refs(root: Path, file: str, text: str) -> list[str]:
    """ESLint 配置 import 里指向共享基础规则的引用原文。"""
    refs = re.findall(r"from\s+['\"]([^'\"]*eslint-base\.mjs)['\"]", text)
    return [ref for ref in refs if _resolves_to(root, file, ref, "lint/eslint-base.mjs")]


def has_select(text: str) -> bool:
    return re.search(r"^\s*select\s*=", text, re.M) is not None


def react_without_eslint(root: Path, files: list[str]) -> list[str]:
    """本身和上级目录（直到项目根）都没有 ESLint 配置的 React 目录；ESLint 扁平配置从当前目录往上找。"""
    config_dirs = {Path(f).parent for f in eslint_configs(files)}
    return [f"{d}：是 React 目录，但它和上级目录都没有 ESLint 配置" for d in react_dirs(root, files)
            if not config_dirs & {Path(d), *Path(d).parents}]


def check_lint(root: Path, files: list[str]) -> list[str]:
    """ruff 继承基础配置且不写 select；ESLint 引入基础规则。只检查项目实际有的语言。"""
    problems = []
    configs = ruff_configs(root, files)
    if has_python(files) and not configs:
        problems.append("有 Python 代码但没有 ruff 配置")
    for f, text in configs:
        if not ruff_shared_refs(root, f, text):
            problems.append(f"{f} 没有继承 {shared_ref(root, 'lint/ruff-base.toml')}")
        if has_select(text):
            problems.append(f"{f} 仍写 select，会覆盖基础规则")
    for f in eslint_configs(files):
        if not eslint_shared_refs(root, f, _read(root, f)):
            problems.append(f"{f} 没有引入 {shared_ref(root, 'lint/eslint-base.mjs')}")
    return problems


def layers(root: Path, files: list[str], sel: Selection, entry_issues: list[str], report: Report) -> None:
    report.layers["接入 代码规矩与 gates"] = check_agents(root, files)
    report.layers["接入 工具入口"] = sel.problems + entry_issues
    if not is_source_repo(root):
        report.layers["接入 生成副本"] = copy_issues(root, sel) + block_issues(root, files, sel)
    # 产物写法只看有没有 rules 段；有但与基础版不一致是巡检发现，不是没装
    report.layers["接入 产物写法"] = [] if project_artifact_rules(root) else ["openspec/config.yaml 没有 rules 段"]
    report.layers["接入 lint 继承"] = check_lint(root, files)


def block_issues(root: Path, files: list[str], sel: Selection) -> list[str]:
    if sel.manifest is None:
        return []
    return [f"{STALE_BLOCK}：{rel} 的 {name}" for rel, name in stale_blocks(root, files, sel.manifest)]


def judge_label(root: Path, n_archived: int) -> str:
    """判断是可选功能：已启用，或写明启用还缺什么。"""
    if (root / "openspec/judgments.yaml").exists():
        return "已启用"
    missing = []
    if not has_git(root):
        missing.append("当前没有 git")
    if n_archived < MIN_ARCHIVED:
        missing.append(f"还差 {MIN_ARCHIVED - n_archived} 个")
    if missing:
        return f"可选，未启用（需要 git 与至少 {MIN_ARCHIVED} 个已归档 change；{'，'.join(missing)}）"
    return f"可选，未启用（条件已满足：要启用时在 AI 工具中运行 /{NAME}）"


# ---------- 3. 巡检 ----------

def legacy_issues(root: Path, files: list[str]) -> list[str]:
    """0.4 旧接入方式：指令、工具配置、lint 配置引用 ../rulekit/，或旧 skill 入口是指向项目外的符号链接。"""
    if is_source_repo(root):
        return []
    candidates = ["AGENTS.md", "CLAUDE.md", *config_refs(root, files)]
    problems = [f"{rel} 引用 {LEGACY_REF}" for rel in dict.fromkeys(candidates) if (root / rel).is_file() and LEGACY_REF in _read(root, rel)]
    project = root.resolve()
    for entry in LEGACY_SKILL_ENTRIES:
        path = root / entry
        if path.is_symlink() and project not in path.resolve().parents:
            problems.append(f"{entry} 是指向项目外的符号链接")
    return problems


def version_findings(sel: Selection) -> list[str]:
    """项目记录的 rulemason 版本与本机安装版本比较；落后只报告，不导致非 0 退出。"""
    if sel.manifest is None or NAME not in sel.manifest:
        return []
    recorded = str(sel.manifest[NAME])
    if parse_version(recorded) < parse_version(__version__):
        return [f"项目记录 {recorded}，本机 {__version__}：运行 {NAME} update 后在项目跑一遍 lint 与测试"]
    if parse_version(recorded) > parse_version(__version__):
        return [f"项目记录 {recorded}，高于本机 {__version__}：先升级本机 {NAME}"]
    return []


def engine_copies(root: Path, files: list[str]) -> list[str]:
    """项目里定义了 load_rules 的 .py 文件，视为判断引擎副本；rulemason 源码仓库本身就是引擎所在，不查。"""
    if is_source_repo(root):
        return []
    return [f for f in files if f.endswith(".py") and "def load_rules" in _read(root, f)]


def duplicate_rules(root: Path) -> list[str]:
    """项目规则中与通用规则同 id 且内容完全相同的条目；同 id 不同内容是有意覆盖，不算。"""
    base = {r["id"]: r for r in read_judgments(ENGINE_BASE / "judgments.yaml")}
    return [r["id"] for r in read_judgments(root / "openspec/judgments.yaml") if base.get(r["id"]) == r]


def lexicon_overlap(root: Path) -> list[str]:
    base = set(read_yaml(ENGINE_BASE / "copy-lexicon.yaml", {}).get("labels") or [])
    project = read_yaml(root / "openspec/copy-lexicon.yaml", {}).get("labels") or []
    return [w for w in project if w in base]


def audit(root: Path, files: list[str], sel: Selection, report: Report) -> None:
    report.findings.append((LEGACY_FINDING, legacy_issues(root, files)))
    report.findings.append((f"{NAME} 版本", version_findings(sel)))
    report.findings.append(("产物写法与基础版的差异", artifact_rules_diff(root)))
    report.findings.append(("检查点提示与基础版的差异", operations_diff(root)))
    report.findings.append(("React 目录缺少 ESLint", react_without_eslint(root, files)))
    report.findings.append(("判断引擎副本", engine_copies(root, files)))
    report.findings.append(("与通用规则重复的项目规则", duplicate_rules(root)))
    report.findings.append(("项目词表中已在通用词表的词", lexicon_overlap(root)))
    report.findings.append((RESIDUE_FINDING, residue_issues(root, files)))


def config_refs(root: Path, files: list[str]) -> list[str]:
    """会引用共享副本路径的工具配置：OpenCode instructions、ruff、ESLint。"""
    return [*opencode_configs(root), *(f for f, _ in ruff_configs(root, files)), *eslint_configs(files)]


def residue_candidates(root: Path, files: list[str]) -> list[str]:
    """会被工具读取、可能残留旧名的入口与配置；归档与历史记录不查。"""
    rels = ["AGENTS.md", "CLAUDE.md", *config_refs(root, files), WORKFLOW_SPEC, ".gitignore"]
    return [rel for rel in dict.fromkeys(rels) if (root / rel).is_file()]


def residue_in(text: str) -> list[str]:
    """标记块以外出现的旧名。"""
    outside = MANAGED_BLOCK.sub("", text)
    return [name for name in RESIDUE_NAMES if name in outside]


def residue_hits(root: Path, files: list[str], read: Callable[[str], str]) -> list[tuple[str, list[str]]]:
    """(文件, 其中的旧名)；read(rel) 给出文件内容，check 读磁盘，迁移读计划里的新内容。"""
    hits = [(rel, residue_in(read(rel))) for rel in residue_candidates(root, files)]
    return [(rel, found) for rel, found in hits if found]


def residue_issues(root: Path, files: list[str]) -> list[str]:
    """入口与配置里标记块外的旧名；源码仓库本身不查。"""
    if is_source_repo(root):
        return []
    return [f"{rel} 仍有 {'、'.join(found)}" for rel, found in residue_hits(root, files, lambda rel: _read(root, rel))]


# ---------- 4. 下一步与退出码 ----------

def _has_pending(root: Path) -> bool:
    path = root / "AGENTS.md"
    return path.is_file() and any(mark in path.read_text(encoding="utf-8") for mark in PENDING_MARKS)


@dataclass(frozen=True)
class Next:
    """下一步：阶段、给 AI 查表的稳定动作代码、给人看的动作文字。"""
    stage: str
    code: str
    action: str

    @property
    def line(self) -> str:
        """文字版报告的第一行「阶段：下一步」。"""
        return f"{self.stage}：{self.action}"


def next_stage(root: Path, report: Report, sel: Selection) -> Next:
    """按原因给出具体命令或动作，多个原因时取最靠前的。阶段只有接入、补项目信息、日常巡检。"""
    findings = dict(report.findings)
    copies = report.layers.get("接入 生成副本", [])
    if findings[LEGACY_FINDING]:
        return Next("接入", "legacy", f"旧接入方式，需迁移（先按文档迁移，迁移前不要运行 {NAME} init）")
    if sel.label == INVALID:
        return Next("接入", "fix_manifest", f"先修正 {MANIFEST}")
    if sel.label == TO_MIGRATE:
        return Next("接入", "migrate", f"运行 {NAME} init 迁移格式")
    if sel.manifest is None and not is_source_repo(root):
        return Next("接入", "init", f"运行 {NAME} init")
    if any(item.startswith(IGNORED_COPY) for item in copies):
        return Next("接入", "fix_gitignore", f"修改 .gitignore，放行 skills/{NAME}/（副本要随项目提交）")
    if findings[RESIDUE_FINDING]:
        return Next("补项目信息", "fix_residue", f"在 AI 工具中运行 /{NAME} 处理旧名残留")
    if any(missing for name, missing in report.layers.items() if name.startswith("接入")):
        return Next("接入", "update", f"运行 {NAME} update")
    if _has_pending(root):
        return Next("补项目信息", "fill_project_info", f"在 AI 工具中运行 /{NAME}")
    if findings[f"{NAME} 版本"]:
        return _version_next(sel)
    return Next("日常巡检", "none", "一切一致")


def _version_next(sel: Selection) -> Next:
    """版本不一致时：清单记录的比本机新，先升级本机；否则升级副本。"""
    if parse_version(sel.manifest[NAME]) > parse_version(__version__):
        return Next("日常巡检", "upgrade_machine", f"先升级本机 {NAME}")
    return Next("日常巡检", "upgrade_copies", f"运行 {NAME} update 升级副本")


def exit_code(report: Report) -> int:
    """接入各层有缺（入口、副本或标记块被改、lint 未继承、manifest 无效或未迁移）、旧接入方式、旧名残留时为 1；版本落后等巡检发现不影响。"""
    blocking = any(missing for name, missing in report.layers.items() if name.startswith("接入"))
    findings = dict(report.findings)
    return 1 if blocking or findings[LEGACY_FINDING] or findings[RESIDUE_FINDING] else 0


# ---------- 5. 跑 ----------

def collect(root: Path) -> tuple[Report, Next]:
    """识别、各层、巡检，返回 (报告, 下一步)。命令行、init 与测试共用这一条流程。"""
    scanned = scan(root)
    files = scanned.files
    n = archived(root)
    sel = tool_selection(root)
    entry_issues = check_tool_entries(root, files, sel.tools)
    report = Report()
    identify(root, scanned, n, sel, entry_issues + sel.problems, report)
    layers(root, files, sel, entry_issues, report)
    audit(root, files, sel, report)
    return report, next_stage(root, report, sel)


def render(root: Path, report: Report, nxt: Next) -> str:
    lines = [nxt.line, "", f"# {NAME} 识别：{root.name}", "", "## 识别表"]
    lines += [f"- {k}：{v}" for k, v in report.facts]
    if not has_git(root):
        lines.append("- 提示：没有 git，无法用 diff 查看改动，副本也无法通过仓库共享")
    lines += ["", "## 各层状态"]
    for name, missing in report.layers.items():
        lines.append(f"- {name}：{'齐全' if not missing else '缺'}")
        lines += [f"  - {m}" for m in missing]
    lines += ["", "## 巡检"]
    for name, items in report.findings:
        lines.append(f"- {name}：{'一致' if not items else ''}")
        lines += [f"  - {i}" for i in items]
    return "\n".join(lines)


def to_json(root: Path, report: Report, nxt: Next, text: str, code: int) -> str:
    """check --json 的输出：键名英文、值沿用文字版；text 是文字版全文，AI 一次拿到决策字段与汇报原文。"""
    data = {
        "schema": 1,
        "root": str(root),
        "next": asdict(nxt),
        "facts": dict(report.facts),
        "layers": report.layers,
        "findings": dict(report.findings),
        "exit_code": code,
        "text": text,
    }
    return dump_json(data)


def run(root: Path, as_json: bool = False) -> tuple[str, int]:
    """返回 (报告文本或 JSON, 退出码)。"""
    report, nxt = collect(root)
    text = render(root, report, nxt)
    code = exit_code(report)
    if as_json:
        return to_json(root, report, nxt, text, code), code
    return text, code
