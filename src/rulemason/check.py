"""rulemason check：只读识别项目与接入状态，第一行给「阶段：下一步」，再输出识别表、各层状态与巡检，并按结果给退出码。"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from string import Template
from typing import NamedTuple

from rulemason import __version__
from rulemason import judge as engine
from rulemason.judge.judge import api_key
from rulemason.shared import (
    CHECKPOINTS_OFF,
    COPIED_SHARED,
    COPY_DIR,
    JOINED,
    KEY_URL,
    MANIFEST,
    NAME,
    TOOL_LABELS,
    ConfigError,
    ManifestError,
    Scan,
    copy_record,
    dirty_files,
    dump_json,
    folder_hint,
    generated_files,
    has_git,
    has_openspec,
    has_python,
    ignored_files,
    is_source_repo,
    joined_date,
    languages,
    outer_repo,
    parse_version,
    read_judgments,
    read_manifest,
    read_yaml,
    scan,
    sha256_file,
    shared_root,
    shown_list,
    skill_dirs,
    skill_hint_lines,
    template,
)

LANGUAGE_RULES = ("rules/python.md", "rules/react.md")       # 按项目语言决定是否引用的落法，顺序即入口里的顺序
INSTRUCTIONS_ARRAY = re.compile(r'"instructions"\s*:\s*\[(.*?)\]', re.S)   # OpenCode 配置里的 instructions 数组（只取这一项，不解析整份 JSONC）
DEPENDENCY_KEYS = ("dependencies", "devDependencies", "peerDependencies")   # 判断 React 与前端目录时看的 package.json 依赖段
FRONTEND_DEPS = ("react", "vue", "svelte", "@angular/core", "preact", "solid-js", "next", "nuxt")   # 有这些依赖才算前端目录
ESLINT_ANCHORS = ("export default [", "export default defineConfig([", "export default tseslint.config(")   # 能自动插入基础规则的写法
RUFF_BASE = "lint/ruff-base.toml"
ESLINT_BASE = "lint/eslint-base.mjs"
CHAIN_LIMIT = 10                                            # ruff 继承链最多走这么多层，再深按「过深」报告
RERUN = f"改完运行：{NAME} update"
ENGINE_BASE = Path(engine.__file__).parent / "base"      # 引擎自带的通用规则与通用词表
# 主规格写法的文本规则：数字取自 OpenSpec 严格校验（MIN_PURPOSE_LENGTH、MAX_REQUIREMENT_TEXT_LENGTH），不调 openspec
SPEC_PURPOSE_MIN = 50
SPEC_REQUIREMENT_MAX = 500
NO_PURPOSE = "缺 Purpose"
PLACEHOLDER_PURPOSE = "Purpose 是占位"
SHORT_PURPOSE = f"Purpose 不足 {SPEC_PURPOSE_MIN} 字"
DELTA_HEADINGS = "用了增量格式标题"
NO_REQUIREMENTS = "没有 ## Requirements 一节"
LONG_REQUIREMENT = f"requirement 正文超过 {SPEC_REQUIREMENT_MAX} 字"
NO_SCENARIO = "requirement 没有场景"
SPEC_PROBLEMS = (NO_PURPOSE, PLACEHOLDER_PURPOSE, SHORT_PURPOSE, DELTA_HEADINGS, NO_REQUIREMENTS, LONG_REQUIREMENT, NO_SCENARIO)   # 也是报告顺序
LINT_PLACEHOLDER = re.compile(r"\s*(|true|:|exit\s+0|echo([ \t][^&;|\n`$]*)?)\s*")   # 只有一条什么都不查的命令
CODE_FENCE = re.compile(r"^\s*(```|~~~)")                  # 代码块边界：块内不算 requirement 正文
METADATA_LINE = re.compile(r"^\*\*[^*]+\*\*:")          # **ID**: 一类元数据行，OpenSpec 不计入正文
DELTA_HEADING = re.compile(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", re.M)
MIN_ARCHIVED = 3                                            # 判断层至少要这么多已归档 change 作测试用例
ARCHIVE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-")       # openspec archive 生成的归档目录名：日期前缀
TASK_BOX = re.compile(r"^\s*-\s+\[([^\]]*)\]", re.M)       # tasks.md 的勾选框；框内去掉空白后是 x 或 X 才算完成
GATE_RECORDS = (                                           # 完成汇报里要写到的两项：(名称, 匹配)
    # 英文按 ASCII 词边界：preview、latest 不算；紧贴汉字的「独立review」「单元test」要算（默认 Unicode 边界把汉字当字母）
    ("审查", re.compile(r"审查|\breview", re.I | re.A)),
    ("测试", re.compile(r"测试|\btest|pytest", re.I | re.A)),
)
LOCKFILES = (("uv", "uv.lock"), ("pip", "requirements.txt"), ("pnpm", "pnpm-lock.yaml"), ("npm", "package-lock.json"))
SKILL_ENTRIES = (f".claude/skills/{NAME}", f".agents/skills/{NAME}")
PENDING_MARKS = (f"待 /{NAME} 补充", "自动识别，请确认")      # init 留给 /rulemason 补的内容
INVALID = "配置无效"
WORKFLOW_SPEC = "openspec/specs/workflow-gates/spec.md"


@dataclass
class Report:
    facts: list[tuple[str, str]] = field(default_factory=list)       # 识别表
    layers: dict[str, list[str]] = field(default_factory=dict)       # 层名 → 缺失项；空表示已装好
    findings: list[tuple[str, list[str]]] = field(default_factory=list)   # 巡检项 → 偏离；空表示一致
    notes: dict[str, str] = field(default_factory=dict)              # 巡检项 → 没有偏离时代替「一致」的说明（只进文字版）
    next_notes: list[str] = field(default_factory=list)              # 跟在第一行后的补充说明，不改变下一步


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
BEHIND = "副本与本机版本应生成的不一致"
VERSION_ONLY = "只有版本号落后，副本内容相同"


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


def python_dirs(files: list[str]) -> list[str]:
    return _dirs_with(files, ("pyproject.toml", "requirements.txt"))


def frontend_dirs(root: Path, files: list[str]) -> list[str]:
    """依赖里有界面框架，或同目录有 index.html（不用框架的网页入口）的 package.json 所在目录；
    只有工具依赖的 Node 包（如工作区根、后端）不算。"""
    pages = set(_dirs_with(files, ("index.html",)))
    web_entries = [d for d in _dirs_with(files, ("package.json",)) if d in pages]
    return sorted({*package_dirs(root, files, FRONTEND_DEPS), *web_entries})


def copied_rules(root: Path, files: list[str]) -> list[str]:
    """项目用得上的共享文件：九条、检查点、中文排版、result-check 契约、文案卫生与编码审慎必复制；
    Python 落法与 ruff 基础配置随 Python；React 落法随 React 目录；
    ESLint 基础配置随 React 目录或已有的 ESLint 配置；文案语气随前端目录或已启用的判断。"""
    react = bool(react_dirs(root, files))
    wanted = {
        "rules/code-style.md",
        "rules/workflow-gates.md",
        "rules/cjk-typography.md",
        "rules/result-check-contracts.md",
        "rules/prose-hygiene.md",
        "rules/agent-coding-caution.md",
    }
    if has_python(files):
        wanted |= {"rules/python.md", RUFF_BASE}
    if react:
        wanted.add("rules/react.md")
    if react or eslint_configs(files):
        wanted.add(ESLINT_BASE)
    if frontend_dirs(root, files) or (root / "openspec/judgments.yaml").is_file():
        wanted.add("rules/copy-voice.md")
    return [rel for rel in COPIED_SHARED if rel in wanted]


def for_languages(text: str, root: Path, files: list[str]) -> str:
    """去掉模板里项目用不到的语言落法的引用行。"""
    absent = set(LANGUAGE_RULES) - set(language_rules(root, files))
    return "".join(line for line in text.splitlines(keepends=True) if not any(ref in line for ref in absent))


def block_body(name: str, root: Path, files: list[str]) -> str:
    """标记块在当前版本下应有的内容；没接 OpenSpec 的项目，检查点块用说明「未启用」的版本。"""
    if name == "workflow-gates" and not has_openspec(root):
        return template("workflow-gates-no-openspec.block.md")
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


def react_dirs(root: Path, files: list[str]) -> list[str]:
    return package_dirs(root, files, ("react",))


def package_jsons(root: Path, files: list[str]) -> list[tuple[str, object]]:
    """项目里每个 package.json：(相对路径, 解析结果)；读不出来时抛 ConfigError。"""
    found = []
    for f in files:
        if Path(f).name != "package.json":
            continue
        try:
            found.append((f, json.loads(_read(root, f))))
        except ValueError as exc:                                 # 含 JSONDecodeError 与 UnicodeDecodeError
            raise ConfigError(f"{f} 不是合法的 JSON（{exc}）") from exc
    return found


def package_dirs(root: Path, files: list[str], names: tuple[str, ...]) -> list[str]:
    """依赖里有 names 任一项的 package.json 所在目录（项目根记为「.」）；package.json 读不出来时抛 ConfigError。"""
    dirs = []
    for f, data in package_jsons(root, files):
        sections = [data.get(key) for key in DEPENDENCY_KEYS] if isinstance(data, dict) else []
        if any(isinstance(d, dict) and any(name in d for name in names) for d in sections):
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
    if manifest is None:
        return Selection([], f"未选择（缺少 {MANIFEST}）", [f"没有 {MANIFEST}：先运行 {NAME} init"], None)
    tools = manifest["tools"]
    return Selection(tools, "、".join(TOOL_LABELS[t] for t in tools) or "未选择", [], manifest)


def skipped_label(skipped: list[tuple[str, str]]) -> str:
    """「目录（原因）」，多了只列前面的并写总数（见 shown_list）；没有写「—」。"""
    return shown_list([f"{d}（{reason}）" for d, reason in skipped]) or "—"


def archive_dirs(root: Path) -> list[Path]:
    """openspec/changes/archive/ 下的 change 目录；没有归档目录时为空。"""
    d = root / "openspec/changes/archive"
    return [p for p in d.iterdir() if p.is_dir()] if d.is_dir() else []


def archived(root: Path) -> int:
    return len(archive_dirs(root))


def dated_archives(root: Path, since: str | None) -> list[tuple[str, Path]]:
    """(日期, 目录)：openspec 生成的归档里日期晚于 since 的；since 为 None 时不筛。接入当天的按接入前算，分不清先后。"""
    dated = []
    for p in archive_dirs(root):
        m = ARCHIVE_NAME.match(p.name)
        if m and (since is None or m.group(1) > since):
            dated.append((m.group(1), p))
    return dated


def gate_records(dated: list[tuple[str, Path]]) -> list[str]:
    """dated（见 dated_archives）里日期最新的那一天归档的每个 change：没有 verification.md，或没写到审查、测试时各给一条。"""
    if not dated:
        return []
    latest = max(day for day, _ in dated)
    problems = []
    for change in sorted(p for day, p in dated if day == latest):
        report = change / "verification.md"
        if not report.is_file():
            problems.append(f"{change.name}：没有 verification.md")
            continue
        text = report.read_text(encoding="utf-8")
        missing = [name for name, pattern in GATE_RECORDS if not pattern.search(text)]
        if missing:
            problems.append(f"{change.name}：verification.md 没有写到{'、'.join(missing)}")
    return problems


def tasks_finished(text: str) -> bool:
    """至少有一个勾选框，且每个框内去掉空白后是 x 或 X。没有框时不算完成。"""
    boxes = TASK_BOX.findall(text)
    return bool(boxes) and all(box.strip().lower() == "x" for box in boxes)


def unarchived_finished(root: Path) -> list[str]:
    """openspec/changes/ 下任务已全部勾完、还没归档的 change。没有汇报和有汇报分成两句。"""
    changes = root / "openspec/changes"
    if not changes.is_dir():
        return []
    found = []
    for change in sorted(p for p in changes.iterdir() if p.is_dir() and (p / ".openspec.yaml").is_file()):
        tasks = change / "tasks.md"
        if not tasks.is_file() or not tasks_finished(_read(root, tasks.relative_to(root).as_posix())):
            continue
        state = "尚未归档" if (change / "verification.md").is_file() else "没有 verification.md"
        found.append(f"{change.name}：{state}")
    return found


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


def identify(root: Path, scanned: Scan, n_archived: int, sel: Selection, since: str | None, entry_issues: list[str], report: Report) -> None:
    """识别表：项目根、语言与包管理、目录与跳过的目录、openspec、归档数与接入日期、CI、未提交改动、工具与版本。"""
    files = scanned.files
    report.facts.append(("项目根", str(root)))
    repo = outer_repo(root)
    if repo:
        report.facts.append(("所在 git 仓库根", str(repo)))   # 只在未接入、又在仓库子目录里时出现，「项目根」的值保持纯路径
    # 1. 语言与包管理
    names = {Path(f).name for f in files}
    managers = [m for m, lock in LOCKFILES if lock in names]
    report.facts.append(("语言", "、".join(languages(files)) or "未识别"))
    report.facts.append(("包管理", "、".join(managers) or "无锁文件"))

    # 2. 目录
    report.facts.append(("Python 目录", "、".join(python_dirs(files)) or "—"))
    react = react_dirs(root, files)
    front = [f"{d}（React）" if d in react else d for d in frontend_dirs(root, files)]
    report.facts.append(("前端目录", "、".join(front) or "—"))
    report.facts.append(("跳过", skipped_label(scanned.skipped)))
    hint = folder_hint(scanned)
    if hint:
        report.facts.append(("提示", hint))

    # 3. openspec、CI、工作区
    report.facts.append(("openspec", "有" if has_openspec(root) else f"无（{CHECKPOINTS_OFF}）"))
    report.facts.append(("已归档 change", str(n_archived)))
    if since is None:
        joined = "—"
    elif JOINED not in sel.manifest:                      # 走到这里说明有清单（since 只在有清单时算）
        joined = f"{since}（推算）"                            # 清单还没记，按 git 推算
    else:
        joined = since
    report.facts.append(("接入日期", joined))
    after_joined = str(len(dated_archives(root, since))) if since else "—"
    report.facts.append(("接入后归档 change", after_joined))
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


def version_order(sel: Selection) -> int:
    """项目记录的版本与本机比：-1 记录较旧，0 相同或没有记录，1 记录较新。"""
    recorded = (sel.manifest or {}).get(NAME)
    if recorded is None:
        return 0
    mine, theirs = parse_version(__version__), parse_version(str(recorded))
    return (theirs > mine) - (theirs < mine)


def version_only(sel: Selection, behind: list[str]) -> bool:
    """记录的版本较旧、副本内容又比过且相同：只有版本号落后。清单没有副本记录时没法比，不算。"""
    return version_order(sel) < 0 and not behind and bool((sel.manifest or {}).get("files"))


def managed_prefixes(tools: list[str]) -> tuple[str, ...]:
    """rulemason 自己管的副本所在目录：.rulemason/ 与已选工具的 skill 目录。"""
    return (f"{COPY_DIR}/", *(f"{d}/" for d in skill_dirs(tools)))


def copies_behind(root: Path, files: list[str], sel: Selection) -> list[str]:
    """本机版本会生成的副本与清单记录的校验值不一致（共享内容变了，或项目语言变了）时给一条。
    源码仓库没有副本；记录比本机新时不比，由版本巡检提示先升级本机；清单没有记录时由 copy_issues 报告。"""
    record = (sel.manifest or {}).get("files") or {}
    if is_source_repo(root) or not record or version_order(sel) > 0:
        return []
    prefixes = managed_prefixes(sel.tools)
    recorded = {(rel, digest) for rel, digest in record.items() if rel.startswith(prefixes)}
    expected = set(copy_record(generated_files(sel.tools, copied_rules(root, files))).items())
    differ = {rel for rel, _ in recorded ^ expected}
    return [f"{BEHIND}（{len(differ)} 个文件；共享内容更新，或项目语言、判断启用状态变了）：运行 {NAME} update"] if differ else []


def copy_issues(root: Path, sel: Selection) -> list[str]:
    """已选工具应有的生成副本：缺失、与 .rulemason.yaml 记录的校验值不符，或在 git 仓库里被忽略。"""
    if sel.manifest is None:
        return []
    record = sel.manifest.get("files") or {}
    if not record:
        return [f"{MANIFEST} 没有记录生成副本：运行 {NAME} init"]
    problems = []
    rels = [rel for rel in record if rel.startswith(managed_prefixes(sel.tools))]
    for rel in rels:
        # 以项目记录为准：本机版本新增的文件不算缺失，与本机应生成的不一致由 copies_behind 报告
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


def _target(root: Path, file: str, ref: str) -> Path:
    """配置中的相对路径按配置文件所在目录解析。"""
    target = Path(ref).expanduser()
    if not target.is_absolute():
        target = (root / file).parent / ref
    return target.resolve()


def _resolves_to(root: Path, file: str, ref: str, canonical: str) -> bool:
    """引用是否指向项目应引用的共享文件。"""
    return _target(root, file, ref) == (root / shared_ref(root, canonical)).resolve()


def ruff_refs(text: str) -> list[str]:
    """ruff 配置 extend 里的全部路径原文。"""
    match = re.search(r"^\s*extend\s*=\s*(.+)$", text, re.M)
    return re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)) if match else []


def eslint_refs(text: str) -> list[str]:
    """ESLint 配置 import 里文件名是 eslint-base.mjs 的路径原文。"""
    return re.findall(r"from\s+['\"]([^'\"]*eslint-base\.mjs)['\"]", text)


def ruff_shared_refs(root: Path, file: str, text: str) -> list[str]:
    """ruff 配置 extend 里指向共享基础配置的引用原文。"""
    return [ref for ref in ruff_refs(text) if _resolves_to(root, file, ref, RUFF_BASE)]


def eslint_shared_refs(root: Path, file: str, text: str) -> list[str]:
    """ESLint 配置 import 里指向共享基础规则的引用原文。"""
    return [ref for ref in eslint_refs(text) if _resolves_to(root, file, ref, ESLINT_BASE)]


def _ref_kind(root: Path, file: str, ref: str, canonical: str) -> str | None:
    """一个引用与基础配置的关系：linked 指向项目内副本；broken 同名但目标不存在或在项目外（多是旧路径）；
    old_copy 同名、在项目内存在却不是 .rulemason/ 副本（旧位置副本，如 remove 移到 lint/ 的）；None 与基础配置无关。
    ruff 与 ESLint 共用这一个判断。"""
    if _resolves_to(root, file, ref, canonical):
        return "linked"
    if Path(ref).name != Path(canonical).name:
        return None
    target = _target(root, file, ref)
    return "old_copy" if target.is_file() and root.resolve() in target.parents else "broken"


def broken_refs(root: Path, file: str, refs: list[str], canonical: str) -> list[str]:
    """文件名与基础配置相同、却不指向项目内副本，且目标不存在或在项目外的引用原文（多是旧路径）。"""
    return [ref for ref in refs if _ref_kind(root, file, ref, canonical) == "broken"]


def _base_ref(root: Path, file: str, canonical: str) -> str:
    """这份配置里应写的基础配置路径（指向项目内副本，按配置所在目录写相对路径）。"""
    return config_ref(root, file, root / shared_ref(root, canonical))


def has_select(text: str) -> bool:
    return re.search(r"^\s*select\s*=", text, re.M) is not None


def _insert_ruff_extend(name: str, text: str, ref: str) -> str:
    line = f'extend = "{ref}"   # 选用规则与复杂度来自 {NAME} 基础配置的项目内副本\n'
    text = text if text.endswith("\n") else text + "\n"      # 末行没有换行时，插入行会被并进注释或表头
    if name != "pyproject.toml":
        # 走到这里说明是 ruff 格式的配置：ruff.toml，或继承链上任意命名的 .toml
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
    """配置文件里指向 target 的相对路径；ESLint 的 import 不以 ./ 或 ../ 开头会被当成包名（含 .rulemason/ 这种点开头的目录），补上。"""
    ref = Path(os.path.relpath(target, (root / config).parent)).as_posix()
    if target.suffix == ".mjs" and not ref.startswith(("./", "../")):
        return f"./{ref}"
    return ref


@dataclass(frozen=True)
class LintFix:
    """一份 lint 配置怎么接上基础配置；全为 None 表示已接好。
    text：target（为空即这份配置本身）改好的内容；note：改不了时给人的说明（第一行摘要，后面缩进写步骤）；
    problem：能自动改时 check 报告里的那一行；tip：改完后顺带告诉人的事，不算待处理。"""
    text: str | None = None
    note: str | None = None
    problem: str | None = None
    tip: str | None = None
    target: str | None = None


def repoint(text: str, refs: list[str], new_ref: str) -> str:
    """把引号里的旧路径换成新路径，单双引号都认；变量名与用法不动。"""
    for ref in refs:
        text = re.sub(r"(['\"])" + re.escape(ref) + r"\1", lambda m: f"{m.group(1)}{new_ref}{m.group(1)}", text)
    return text


def _lines_with(text: str, pattern: str) -> list[tuple[int, str]]:
    """匹配 pattern 的各行：(行号从 1 起, 去掉首尾空白的原文)。"""
    return [(n, line.strip()) for n, line in enumerate(text.splitlines(), 1) if re.search(pattern, line)]


def _line_with(text: str, pattern: str) -> tuple[int, str]:
    """第一处匹配 pattern 的行；找不到返回 (0, "")。"""
    return next(iter(_lines_with(text, pattern)), (0, ""))


def _manual(summary: str, *steps: str) -> str:
    """改不了的项给人的说明：第一行摘要（check 第一行只取它），后面每步缩进一行。"""
    return summary + "".join(f"\n    {step}" for step in steps)


def _project_rel(root: Path, target: Path) -> str:
    return target.relative_to(root.resolve()).as_posix()


def _is_base_copy(root: Path, target: Path, canonical: str) -> bool:
    """项目内另一份同名文件是否就是基础配置：与项目里的副本（若已生成）或本机版本将写入的内容相同（换行统一成 LF 再比）。"""
    candidates = [shared_root() / canonical, root / shared_ref(root, canonical)]
    return sha256_file(target) in {sha256_file(p) for p in candidates if p.is_file()}


def _old_copy_fix(root: Path, file: str, text: str, old_ref: str, canonical: str, verb: str) -> LintFix:
    """配置引用的是项目内旧位置的基础配置（如 remove 移到 lint/ 的）：内容没改过就改指向项目内副本，改过就写明怎么手动合并。"""
    ref = _base_ref(root, file, canonical)
    target = _target(root, file, old_ref)
    old = _project_rel(root, target)
    if _is_base_copy(root, target, canonical):
        return LintFix(
            text=repoint(text, [old_ref], ref), target=file,
            problem=f"{file} {verb}的是旧位置的基础配置副本：{old_ref}",
            tip=f"{old} 是基础配置的旧位置副本；{file} 改为引用 {COPY_DIR}/ 下的副本后，确认没有别处引用就可以删除",
        )
    n, line = _line_with(text, re.escape(old_ref))
    return LintFix(note=_manual(
        f"{file} {verb}的 {old} 与基础配置不同（被改过或来自旧版本）：未修改",
        f"先看差异：diff {old} {shared_ref(root, canonical)}",
        f"把被改过的那份里要保留的设置（如 ignore、per-file-ignores、line-length）写进 {file}",
        f"再把第 {n} 行 {line} 里的 {old_ref} 改为 {ref}",
        RERUN,
    ), target=file)


def lint_fix(root: Path, file: str, text: str, read: Callable[[str], str] | None = None) -> LintFix:
    """init、update 与 check 共用的判断：这份 ruff 或 ESLint 配置能否自动接上基础配置；read 见 ruff_chain。"""
    if Path(file).name in ("ruff.toml", "pyproject.toml"):
        fix = _ruff_fix(root, file, text, read)
    else:
        fix = _eslint_fix(root, file, text)
    return replace(fix, target=fix.target or file)


# ---------- 2.1 ruff 继承链 ----------

class Chain(NamedTuple):
    """一份 ruff 配置沿 extend 走出的继承链。
    links：链上项目内的配置 (路径, 内容)，第一份是起点，最后一份是走到的位置。
    end：linked 接上了项目内副本；tail 到了没有 extend 的末端；broken 引用同名基础配置但目标不存在或在项目外；
         old_copy 引用项目内旧位置的同名基础配置；outside 继承了项目外的配置；missing 继承的文件不存在；
         cycle 绕回链上已有的配置；deep 超过 CHAIN_LIMIT 层；unreadable 继承的文件读不出（不是 UTF-8 文本或没有读权限）。
    ref：最后一份配置里让链停下的引用原文（tail 时为空）。"""
    links: list[tuple[str, str]]
    end: str
    ref: str = ""


def ruff_chain(root: Path, file: str, text: str, read: Callable[[str], str] | None = None) -> Chain:
    """沿 extend 走链，相对路径按所在配置文件的目录解析；ruff 的 extend 只能写一个路径。
    read 读链上其他配置（init 传计划里已改的内容），默认读磁盘。"""
    read = read or (lambda rel: _read(root, rel))
    project = root.resolve()
    links = [(file, text)]
    while True:
        current, body = links[-1]
        refs = ruff_refs(body)
        if not refs:
            return Chain(links, "tail")
        ref = refs[0]
        kind = _ref_kind(root, current, ref, RUFF_BASE)
        if kind:
            return Chain(links, kind, ref)
        target = _target(root, current, ref)
        if project not in target.parents:
            return Chain(links, "outside", ref)
        if not target.is_file():
            return Chain(links, "missing", ref)
        rel = _project_rel(root, target)
        if rel in {f for f, _ in links}:
            return Chain(links, "cycle", ref)
        if len(links) >= CHAIN_LIMIT:
            return Chain(links, "deep", ref)
        try:
            links.append((rel, read(rel)))
        except (OSError, UnicodeDecodeError):
            return Chain(links, "unreadable", ref)


def _select_note(file: str, text: str) -> str:
    n, line = _line_with(text, r"^\s*select\s*=")
    multiline = "（数组跨多行时只改这一行开头的 select）" if line.endswith("[") else ""
    return _manual(
        f"{file} 写了 select，会覆盖基础规则：未修改",
        f"位置：第 {n} 行 {line}",
        f"做法一（在基础规则上多开几条）：改为 {re.sub(r'^select', 'extend-select', line)}{multiline}",
        "做法二（不需要额外规则）：删去这一行（数组跨多行时连同整个数组）",
        RERUN,
    )


def _chain_note(root: Path, chain: Chain, ref: str) -> str:
    """继承链走到项目外、引用不存在、绕回自己或过深时给人的说明；ref 是末端配置应写的基础配置路径。"""
    file, body = chain.links[-1]
    n, line = _line_with(body, re.escape(chain.ref))
    if chain.end == "outside":
        return _manual(
            f"{file} 继承了项目外的 {chain.ref}：未修改（{NAME} 不改项目外的文件）",
            f"位置：第 {n} 行 {line}",
            f'改为：extend = "{ref}"',
            f"{chain.ref} 里本项目要用的设置（如 ignore、line-length）复制进 {file}",
            RERUN,
        )
    if chain.end == "missing":
        return _manual(f"{file} 继承的 {chain.ref} 不存在：未修改", f"位置：第 {n} 行 {line}", f'改为：extend = "{ref}"', RERUN)
    if chain.end == "unreadable":
        return _manual(
            f"{file} 继承的 {chain.ref} 读不出（不是 UTF-8 文本或没有读权限）：未修改",
            f"把 {chain.ref} 存成 UTF-8 文本或放开读权限；或把第 {n} 行 {line} 改为：extend = \"{ref}\"",
            RERUN,
        )
    if chain.end == "cycle":
        loop = " → ".join([f for f, _ in chain.links] + [_project_rel(root, _target(root, file, chain.ref))])
        return _manual(f"ruff 继承链绕回自己：{loop}：未修改", f"删去 {file} 第 {n} 行 {line}，或让其中一份不再 extend", RERUN)
    # 走到这里说明链超过 CHAIN_LIMIT 层
    return _manual(
        f"{chain.links[0][0]} 的 ruff 继承链超过 {CHAIN_LIMIT} 层：未修改",
        f"把链上某一份配置的 extend 直接改为继承 {shared_ref(root, RUFF_BASE)}（按该文件所在目录写相对路径）",
        RERUN,
    )


def _ruff_fix(root: Path, file: str, text: str, read: Callable[[str], str] | None) -> LintFix:
    """先看链上有没有 select，再按链停下的原因处理：接上了不改；末端能补就在末端补一行；旧位置副本改指向；其余写明怎么手动改。"""
    chain = ruff_chain(root, file, text, read)
    for rel, body in chain.links:
        if has_select(body):
            return LintFix(note=_select_note(rel, body), target=rel)
    if chain.end == "linked":
        return LintFix()
    tail, body = chain.links[-1]
    ref = _base_ref(root, tail, RUFF_BASE)
    if chain.end == "broken":
        return LintFix(text=repoint(body, [chain.ref], ref), target=tail, problem=f"{tail} 引用的基础配置不存在：{chain.ref}")
    if chain.end == "old_copy":
        return _old_copy_fix(root, tail, body, chain.ref, RUFF_BASE, "继承")
    if chain.end != "tail":
        return LintFix(note=_chain_note(root, chain, ref), target=tail)
    via = f"（继承链末端 {tail}）" if tail != file else ""
    try:
        new = _insert_ruff_extend(Path(tail).name, body, ref)
    except ValueError as exc:
        return LintFix(note=_manual(
            f"{tail} 无法安全写入 extend（{exc}）：未修改",
            f'在文件里加入这两行：[tool.ruff] 与 extend = "{ref}"',
            RERUN,
        ), target=tail)
    return LintFix(text=new, target=tail, problem=f"{file} 没有继承 {shared_ref(root, RUFF_BASE)}{via}")


# ---------- 2.2 ESLint ----------

def _use_steps(text: str, n: int, line: str) -> list[str]:
    """删去第 n 行的引入后，还要处理的每一处使用：只有这一项的整行删，还有别的内容的只去掉对它的使用；
    认不出引入的名字（如 import { x }、import * as x）时笼统提醒一句。"""
    name = re.fullmatch(r"import\s+(\w+)\s+from.*", line)
    if not name:
        return ["再删去配置里用到它的地方"]
    var = name.group(1)
    steps = []
    for m, use in _lines_with(text, rf"\b{var}\b"):
        if m == n:
            continue
        alone = re.fullmatch(rf"(\{{\s*rules:\s*{var}\s*\}}|\.\.\.{var}),?", use)
        # 用到它的那一行还有别的内容时整行删会删坏配置：只说去掉对它的使用
        steps.append(f"再删去用到它的第 {m} 行 {use}" if alone else f"再在第 {m} 行去掉对 {var} 的使用：{use}")
    return steps


def _duplicate_note(root: Path, file: str, text: str, others: list[str]) -> str:
    """同一份配置既引入了项目内副本，又引入了别处的同名基础规则：写明要删的引入行与每一处使用；
    别处那份是被改过（或来自旧版本）的旧副本时，先提醒看差异，免得删掉自定义规则。"""
    steps = []
    for ref in others:
        target = _target(root, file, ref)
        n, line = _line_with(text, re.escape(ref))
        if target.is_file() and not _is_base_copy(root, target, ESLINT_BASE):
            old = _project_rel(root, target)
            steps.append(f"先看差异：diff {old} {shared_ref(root, ESLINT_BASE)}，要保留的规则写进 {file}")
        steps.append(f"删去第 {n} 行 {line}")
        steps += _use_steps(text, n, line)
    return _manual(f"{file} 重复引入基础规则（{'、'.join(others)} 与 {COPY_DIR}/ 下的副本）：未修改", *steps, f"改完运行：{NAME} check")


def _eslint_manual(root: Path, file: str, text: str) -> str:
    """ESLint 配置写法认不出时给人的说明。"""
    if Path(file).name.startswith(".eslintrc"):
        return _manual(
            f"{file} 是旧格式 .eslintrc，{NAME} 只接扁平配置：未修改",
            f"先运行：npx @eslint/migrate-config {file}（在同目录生成 eslint.config.mjs）",
            f"再运行：{NAME} update",
        )
    ref = _base_ref(root, file, ESLINT_BASE)
    n, _ = _line_with(text, r"^import\s")
    where = f"第 {n} 行（第一条 import）之前" if n else "文件开头"
    return _manual(
        f"{file} 的格式无法自动识别：未修改",
        f'在{where}加入：import rulemasonBase from "{ref}";',
        "在导出的配置数组（或 config( 调用）的第一项加入：{ rules: rulemasonBase },",
        RERUN,
    )


def _eslint_fix(root: Path, file: str, text: str) -> LintFix:
    kinds = {r: _ref_kind(root, file, r, ESLINT_BASE) for r in eslint_refs(text)}
    others = [r for r, kind in kinds.items() if kind in ("broken", "old_copy")]
    if "linked" in kinds.values():
        # 走到这里说明已有正确引入；还留着别处的同名引入时，删行要连带删变量的用法，不自动做
        return LintFix(note=_duplicate_note(root, file, text, others)) if others else LintFix()
    ref = _base_ref(root, file, ESLINT_BASE)
    bad = [r for r, kind in kinds.items() if kind == "broken"]
    if bad:
        return LintFix(text=repoint(text, bad, ref), problem=f"{file} 引用的基础配置不存在：{'、'.join(bad)}")
    if others:
        # 走到这里说明引用的是项目内旧位置的同名基础规则
        return _old_copy_fix(root, file, text, others[0], ESLINT_BASE, "引入")
    imported = f'import rulemasonBase from "{ref}";\n'
    anchors = [anchor for anchor in ESLINT_ANCHORS if anchor in text]
    if Path(file).name.startswith(".eslintrc") or len(anchors) != 1 or text.count(anchors[0]) != 1:
        return LintFix(note=_eslint_manual(root, file, text))
    anchor = anchors[0]
    first_import = re.search(r"^import\s", text, re.M)
    at = first_import.start() if first_import else text.index(anchor)
    text = text[:at] + imported + text[at:]
    return LintFix(
        text=text.replace(anchor, f"{anchor}\n  {{ rules: rulemasonBase }},", 1),
        problem=f"{file} 没有引入 {shared_ref(root, ESLINT_BASE)}",
    )


def _with_eslint(root: Path, files: list[str], ruff: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """ruff 配置之后接上全部 ESLint 配置的 (文件, 内容)。"""
    return ruff + [(f, _read(root, f)) for f in eslint_configs(files)]


def manual_lint(root: Path, files: list[str]) -> tuple[str, str] | None:
    """lint 层的缺口 update 全都改不了时，返回第一个 (要改的文件, 说明)；update 能改其中任何一处时返回 None。"""
    ruff = ruff_configs(root, files)
    if needs_ruff_config(files, ruff):
        return None
    fixes = [lint_fix(root, f, text) for f, text in _with_eslint(root, files, ruff)]
    if any(fix.text is not None for fix in fixes):
        return None
    return next(((fix.target, fix.note) for fix in fixes if fix.note), None)


def react_without_eslint(root: Path, files: list[str]) -> list[str]:
    """本身和上级目录（直到项目根）都没有 ESLint 配置的 React 目录；ESLint 扁平配置从当前目录往上找。"""
    config_dirs = {Path(f).parent for f in eslint_configs(files)}
    return [f"{d}：是 React 目录，但它和上级目录都没有 ESLint 配置" for d in react_dirs(root, files)
            if not config_dirs & {Path(d), *Path(d).parents}]


def needs_ruff_config(files: list[str], configs: list[tuple[str, str]]) -> bool:
    """有 Python 代码却没有任何 ruff 配置：init / update 会新建一份。"""
    return has_python(files) and not configs


def check_lint(root: Path, files: list[str]) -> list[str]:
    """ruff 沿继承链接上基础配置且链上不写 select；ESLint 引入基础规则且不重复引入。只检查项目实际有的语言。
    能自动改的报一行问题，改不了的报带步骤的说明；多份配置共用一个末端时同一条只报一次。"""
    ruff = ruff_configs(root, files)
    problems = ["有 Python 代码但没有 ruff 配置"] if needs_ruff_config(files, ruff) else []
    fixes = [lint_fix(root, f, text) for f, text in _with_eslint(root, files, ruff)]
    problems += [fix.note or fix.problem for fix in fixes if fix.note or fix.problem]
    return list(dict.fromkeys(problems))


def layers(root: Path, files: list[str], sel: Selection, entry_issues: list[str], behind: list[str], report: Report) -> None:
    report.layers["接入 代码规矩与 gates"] = check_agents(root, files)
    report.layers["接入 工具入口"] = sel.problems + entry_issues
    if not is_source_repo(root):
        report.layers["接入 生成副本"] = copy_issues(root, sel) + behind + block_issues(root, files, sel)
    # 产物写法只看有没有 rules 段；有但与基础版不一致是巡检发现，不是没装。没接 OpenSpec 的项目这一层不算缺，识别表写明检查点未启用
    if has_openspec(root):
        report.layers["接入 产物写法"] = [] if project_artifact_rules(root) else ["openspec/config.yaml 没有 rules 段"]
    report.layers["接入 lint 继承"] = check_lint(root, files)


def block_issues(root: Path, files: list[str], sel: Selection) -> list[str]:
    if sel.manifest is None:
        return []
    return [f"{STALE_BLOCK}：{rel} 的 {name}" for rel, name in stale_blocks(root, files, sel.manifest)]


def judge_blockers(root: Path, n_archived: int) -> list[str]:
    """启用判断还缺什么：没有 git，或已归档 change 不够；空表示条件已满足。"""
    missing = []
    if not has_git(root):
        missing.append("当前没有 git")
    if n_archived < MIN_ARCHIVED:
        missing.append(f"还差 {MIN_ARCHIVED - n_archived} 个")
    return missing


def judge_label(root: Path, n_archived: int) -> str:
    """判断是可选功能：已启用，或写明启用还缺什么。"""
    if (root / "openspec/judgments.yaml").exists():
        return "已启用"
    missing = judge_blockers(root, n_archived)
    if missing:
        return f"可选，未启用（需要 git 与至少 {MIN_ARCHIVED} 个已归档 change；{'，'.join(missing)}）"
    if not api_key():
        return f"可选，未启用（条件已满足；本机未配置 key：运行 {NAME} key，申请地址 {KEY_URL}）"
    return f"可选，未启用（条件已满足：要启用时在 AI 工具中运行 /{NAME}）"


# ---------- 3. 巡检 ----------

def version_findings(sel: Selection, behind: list[str]) -> list[str]:
    """项目记录的 rulemason 版本与本机安装版本比较；副本内容落后由「接入 生成副本」报告并决定退出码，这里只说版本号。"""
    order = version_order(sel)
    if order == 0:
        return []
    recorded = sel.manifest[NAME]
    if order > 0:
        return [f"项目记录 {recorded}，高于本机 {__version__}：先升级本机 {NAME}"]
    if version_only(sel, behind):
        return [f"项目记录 {recorded}，本机 {__version__}：{VERSION_ONLY}"]
    return [f"项目记录 {recorded}，本机 {__version__}：运行 {NAME} update 后在项目跑一遍 lint 与测试"]


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


def requirement_text(body: str) -> str:
    """requirement 正文按 OpenSpec 的算法取：跳过代码块、空行与元数据行，每行去首尾空白后用换行连起来。"""
    lines = []
    fenced = False
    for line in body.splitlines():
        if CODE_FENCE.match(line):
            fenced = not fenced
            continue
        stripped = line.strip()
        if fenced or not stripped or METADATA_LINE.match(stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def spec_problems(text: str) -> list[str]:
    """一份主规格读主规格判路时会「看不见」或不合严格校验的地方，取值见 SPEC_PROBLEMS。"""
    found = []
    purpose = (_section(text, "Purpose") or "").strip()
    if not purpose:
        found.append(NO_PURPOSE)
    elif purpose.upper().startswith(("TBD", "TODO")):         # openspec archive 给新能力写的占位以 TBD 开头
        found.append(PLACEHOLDER_PURPOSE)
    elif len(purpose) < SPEC_PURPOSE_MIN:
        found.append(SHORT_PURPOSE)
    if DELTA_HEADING.search(text):
        found.append(DELTA_HEADINGS)
    if _section(text, "Requirements") is None:
        found.append(NO_REQUIREMENTS)
    for block in re.split(r"^### Requirement:.*$", text, flags=re.M)[1:]:
        requirement = re.split(r"^##\s", block, flags=re.M)[0]          # 到下一个二级标题为止
        body, *scenarios = re.split(r"^#### Scenario:", requirement, flags=re.M)
        if len(requirement_text(body)) > SPEC_REQUIREMENT_MAX:
            found.append(LONG_REQUIREMENT)
        if not scenarios:
            found.append(NO_SCENARIO)
    return found


def spec_writing(root: Path, files: list[str]) -> list[str]:
    """按问题类型分组：「问题：能力路径、…」；项目文件里没有主规格时为空。"""
    by_problem: dict[str, list[str]] = {}
    for f in sorted(f for f in files if f.startswith("openspec/specs/") and f.endswith("/spec.md")):
        capability = f.removeprefix("openspec/specs/").removesuffix("/spec.md")
        try:
            text = _read(root, f)
        except UnicodeDecodeError as exc:
            raise ConfigError(f"{f} 不是 UTF-8 编码（{exc}）") from exc
        for problem in dict.fromkeys(spec_problems(text)):
            by_problem.setdefault(problem, []).append(capability)
    return [f"{problem}：{shown_list(by_problem[problem])}" for problem in SPEC_PROBLEMS if problem in by_problem]


def lint_placeholders(root: Path, files: list[str]) -> list[str]:
    """scripts.lint 只是占位（空、true、:、exit 0、单条 echo）的 package.json：「路径：原文」。"""
    found = []
    for f, data in package_jsons(root, files):
        scripts = data.get("scripts") if isinstance(data, dict) else None
        script = scripts.get("lint") if isinstance(scripts, dict) else None
        if isinstance(script, str) and LINT_PLACEHOLDER.fullmatch(script):
            found.append(f"{f}：{script!r}")
    return found


def audit(root: Path, files: list[str], sel: Selection, behind: list[str], since: str | None, report: Report) -> None:
    report.findings.append((f"{NAME} 版本", version_findings(sel, behind)))
    report.findings.append(("产物写法与基础版的差异", artifact_rules_diff(root)))
    report.findings.append(("检查点提示与基础版的差异", operations_diff(root)))
    report.findings.append(("React 目录缺少 ESLint", react_without_eslint(root, files)))
    report.findings.append(("判断引擎副本", engine_copies(root, files)))
    report.findings.append(("与通用规则重复的项目规则", duplicate_rules(root)))
    report.findings.append(("项目词表中已在通用词表的词", lexicon_overlap(root)))
    gates = "最近归档的检查点记录"
    dated = dated_archives(root, since)
    report.findings.append((gates, gate_records(dated) + unarchived_finished(root)))
    if since and not dated and dated_archives(root, None):
        report.notes[gates] = "接入后尚未归档，无记录可查"            # 走到这里说明有归档，但都在接入当天或之前
    report.findings.append(("主规格写法", spec_writing(root, files)))
    report.findings.append(("lint 脚本为占位", lint_placeholders(root, files)))


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


def next_stage(root: Path, files: list[str], report: Report, sel: Selection, behind: list[str]) -> Next:
    """按原因给出具体命令或动作，多个原因时取最靠前的；只有版本号落后时在动作后附一句，不改变下一步。"""
    nxt = _next_by_cause(root, files, report, sel)
    if version_only(sel, behind):
        nxt = replace(nxt, action=f"{nxt.action}；版本号落后（{sel.manifest[NAME]} → {__version__}），副本内容相同")
    return nxt


def _next_by_cause(root: Path, files: list[str], report: Report, sel: Selection) -> Next:
    """阶段只有接入、补项目信息、日常巡检。"""
    copies = report.layers.get("接入 生成副本", [])
    missing = [name for name, items in report.layers.items() if name.startswith("接入") and items]
    if sel.label == INVALID:
        return Next("接入", "fix_manifest", f"先修正 {MANIFEST}")
    if sel.manifest is None and not is_source_repo(root):
        return Next("接入", "init", f"运行 {NAME} init")
    if any(item.startswith(IGNORED_COPY) for item in copies):
        return Next("接入", "fix_gitignore", f"修改 .gitignore，放行 skills/{NAME}/（副本要随项目提交）")
    manual = manual_lint(root, files) if missing == ["接入 lint 继承"] else None
    if manual:
        # 走到这里说明接入只剩 update 改不了的 lint 项：第一行写要改的文件与摘要，具体步骤在「接入 lint 继承」下，不再让人原地重跑 update
        return Next("接入", "manual_lint", f"手动修改 {manual[0]}（{NAME} update 改不了）：{manual[1].splitlines()[0]}")
    if missing:
        return Next("接入", "update", f"运行 {NAME} update")
    if _has_pending(root):
        return Next("补项目信息", "fill_project_info", f"在 AI 工具中运行 /{NAME}")
    if version_order(sel) > 0:
        return Next("日常巡检", "upgrade_machine", f"先升级本机 {NAME}")
    return Next("日常巡检", "none", "一切一致")


def exit_code(report: Report) -> int:
    """接入各层有缺（入口、副本或标记块被改、副本与本机应生成的不一致、lint 未继承或引用不存在、manifest 无效）时为 1；只差版本号等巡检发现不影响。"""
    return 1 if any(missing for name, missing in report.layers.items() if name.startswith("接入")) else 0


# ---------- 5. 跑 ----------

def collect(root: Path) -> tuple[Report, Next]:
    """识别、各层、巡检，返回 (报告, 下一步)。命令行、init 与测试共用这一条流程。"""
    scanned = scan(root)
    files = scanned.files
    n = archived(root)
    sel = tool_selection(root)
    entry_issues = check_tool_entries(root, files, sel.tools)
    behind = copies_behind(root, files, sel)
    since = joined_date(root, sel.manifest) if sel.manifest is not None else None
    report = Report()
    identify(root, scanned, n, sel, since, entry_issues + sel.problems, report)
    layers(root, files, sel, entry_issues, behind, report)
    audit(root, files, sel, behind, since, report)
    nxt = next_stage(root, files, report, sel, behind)
    if nxt.code == "fill_project_info":
        report.next_notes += skill_hint_lines(sel.tools)
    return report, nxt


def render(root: Path, report: Report, nxt: Next) -> str:
    lines = [nxt.line, *report.next_notes, "", f"# {NAME} 识别：{root.name}", "", "## 识别表"]
    lines += [f"- {k}：{v}" for k, v in report.facts]
    if not has_git(root):
        lines.append("- 提示：没有 git，无法用 diff 查看改动，副本也无法通过仓库共享")
    lines += ["", "## 各层状态"]
    for name, missing in report.layers.items():
        lines.append(f"- {name}：{'齐全' if not missing else '缺'}")
        lines += [f"  - {m}" for m in missing]
    lines += ["", "## 巡检"]
    for name, items in report.findings:
        lines.append(f"- {name}：{'' if items else report.notes.get(name, '一致')}")
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
