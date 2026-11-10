"""共享数据定位、名字常量、生成副本清单、.rulemason.yaml 读写、校验值与列文件：init / update / check 共用这一份。"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from functools import cache
from pathlib import Path
from string import Template
from typing import Any, NamedTuple

import yaml

from rulemason import __version__

PACKAGE_SHARED = Path(__file__).parent / "_shared"           # wheel 安装：随包发布的共享数据
SOURCE_ROOT = Path(__file__).resolve().parents[2]            # 可编辑安装与测试：源码仓库根
NAME = "rulemason"                                          # 命令、skill、标记块前缀、清单版本键都用这个名字
MANIFEST = f".{NAME}.yaml"
COPY_DIR = f".{NAME}"                                       # 项目内只读副本目录
SCHEMA_VERSION = 1
JOINED = "joined"                                           # 清单里的接入日期键：巡检只看这天之后归档的 change
TOOL_IDS = ("opencode", "claude", "cursor", "codex")
TOOL_LABELS = {"opencode": "OpenCode", "claude": "Claude Code", "cursor": "Cursor", "codex": "Codex"}
AGENTS_SKILL_TOOLS = ("opencode", "cursor", "codex")         # 这三个工具都从 .agents/skills 发现 skill
OPENCODE_SKILL_HINT = f"OpenCode 里 skill 不在 / 列表：对它说「用 {NAME} skill」"   # 跟在「运行 /rulemason」之后，init 与 check 共用
COPIED_SHARED = (
    "rules/code-style.md",
    "rules/python.md",
    "rules/react.md",
    "rules/workflow-gates.md",
    "rules/copy-voice.md",
    "rules/cjk-typography.md",
    "rules/result-check-contracts.md",
    "rules/prose-hygiene.md",
    "rules/agent-coding-caution.md",
    "rules/product-artifact-caution.md",
    "lint/ruff-base.toml",
    "lint/eslint-base.mjs",
)
SKILL_FILES = ("SKILL.md",)                                  # skill 副本只有正文；判断层模板随安装包提供
TEMPLATES = Path(__file__).parent / "templates"
VENDOR_DIRS = ("bower_components", "uni_modules", "third_party", "jspm_packages", "Pods")   # 第三方代码，不属于本项目
VENDOR_MARKERS = ("autoload.php", "modules.txt")            # vendor/ 有 Composer 或 Go 的标记才算第三方；项目也会用它放自己的资源
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", COPY_DIR, ".pytest_cache", ".ruff_cache", "dist", "build"}
THIRD_PARTY = "第三方目录"                                  # 子目录不属于本项目的三种原因；后两种是放项目的文件夹提示的依据
OTHER_REPO = "另一个仓库"
OTHER_PROJECT = f"另一个 {NAME} 项目"
SHOWN_DIRS = 10                                             # 一行里最多列出的目录数（识别表「跳过」、放项目的文件夹提示）
PLAN_DIR = "openspec/changes"                              # 方案草稿与原型：不是项目代码，扫描时静默跳过
CHECKPOINTS_OFF = f"方案检查点未启用：安装 OpenSpec 并 openspec init 后再运行 {NAME} update"
KEY_URL = "https://typesafe.ai/"                            # 判断用的 Jev key 在这里申请
# 终端配色：一个强调色（天空蓝）点标题、标签与命令；次要文字暗色；待办黄色。启动画面与 init 共用
SKY_NUM = "117"                                             # 256 色的天空蓝（SkyBlue1）
SKY = f"38;5;{SKY_NUM}"
SKY_BOLD = f"1;38;5;{SKY_NUM}"
DIM = "2"
BOLD = "1"
YELLOW = "33"


class ManifestError(ValueError):
    """清单（.rulemason.yaml）无法读取或外形不对。"""


# ---------- 1. 共享数据 ----------

def shared_root() -> Path:
    """共享数据根：先找包内 _shared/，再找源码仓库根；两处都没有说明安装不完整。"""
    if PACKAGE_SHARED.is_dir():
        return PACKAGE_SHARED
    if (SOURCE_ROOT / "rules/code-style.md").is_file():
        return SOURCE_ROOT
    raise FileNotFoundError(f"找不到 {NAME} 共享数据：安装不完整，请重新安装 {NAME}")


def has_manifest(path: Path) -> bool:
    """目录里有 rulemason 清单。"""
    return (path / MANIFEST).is_file()


def find_root(start: Path) -> Path | None:
    """已接入的项目根：从 start 往上找最近的有清单的目录，不越过所在 git 仓库的根。找不到返回 None，
    由调用方决定用什么（init、check、update、remove 用当前目录，judge 用 git 仓库根）。"""
    repo = repo_root(start)
    for current in (start, *start.parents):
        if has_manifest(current):
            return current
        if current == repo:
            break                                            # 到了仓库根还没有清单：上层目录属于别的项目或工作区
    return None


def repo_root(start: Path) -> Path | None:
    """start 所在 git 仓库的根（.git 是目录或文件都算，worktree 与子模块的 .git 是文件）；不在 git 里返回 None。"""
    return next((current for current in (start, *start.parents) if (current / ".git").exists()), None)


def outer_repo(root: Path) -> Path | None:
    """root 还没接入、又是某个 git 仓库的子目录时，返回那个仓库根；已接入（子目录项目是有意建的）、就是仓库根或不在 git 里返回 None。"""
    repo = repo_root(root)
    if has_manifest(root) or repo in (None, root):
        return None
    return repo


def repo_root_hint(root: Path) -> str | None:
    """写明仓库根与接入整个仓库的做法；不需要时（见 outer_repo）返回 None。"""
    repo = outer_repo(root)
    return f"当前目录在 git 仓库 {repo} 里；要接入整个仓库，到仓库根运行，或运行 {NAME} init {repo}" if repo else None


def template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def color_enabled() -> bool:
    """没设 NO_COLOR 且标准输出是终端才上色；被管道接走时不让转义进日志。Windows 上还要控制台能解析 ANSI。"""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    return sys.platform != "win32" or windows_ansi()


@cache
def windows_ansi() -> bool:
    """为 Windows 控制台的标准输出打开 ANSI 解析（ENABLE_VIRTUAL_TERMINAL_PROCESSING）；旧版控制台打不开时返回 False。只试一次。
    ctypes 在这里才导入：缺 libffi 的 Python 导入它会失败，不能让其他平台跟着用不了；ctypes.windll 也只在 Windows 上存在。"""
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.GetStdHandle.restype = ctypes.c_void_p          # 句柄是指针宽度，按默认 int 取会在 64 位上截断
    handle = ctypes.c_void_p(kernel32.GetStdHandle(-11))     # STD_OUTPUT_HANDLE；传回时也按指针宽度传
    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))


def legacy_console() -> bool:
    """Windows 旧控制台（cmd.exe 与其中的 PowerShell）：既没有 WT_SESSION（Windows Terminal）也没有 TERM_PROGRAM（VS Code 一类终端）。
    它的字体按 GBK 取字形，缺半格块字符与 ✗，半格字符还按两格宽画。"""
    return sys.platform == "win32" and not (os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"))


def fail(message: str) -> str:
    """报错整句：开头加错误标记。旧控制台的字库里没有 ✗，改用 GBK 里有的 ×。"""
    mark = "×" if legacy_console() else "✗"
    return f"{mark} {message}"


def skill_hint_lines(tools: list[str]) -> list[str]:
    """跟在「运行 /rulemason」之后的补充：只有接入了 OpenCode 才说它那边的叫法。"""
    return [OPENCODE_SKILL_HINT] if "opencode" in tools else []


def paint(text: str, code: str | None, color: bool | None = None) -> str:
    """给文字加 ANSI 颜色；code 为 None 原样返回。color 不传时按当前终端决定。"""
    if code is None or not (color_enabled() if color is None else color):
        return text
    return f"\033[{code}m{text}\033[0m"


def has_openspec(root: Path) -> bool:
    """项目接了 OpenSpec：方案写法规则、检查点提示与项目检查点规格都以此为前提。"""
    return (root / "openspec").is_dir()


def is_source_repo(root: Path) -> bool:
    """rulemason 源码仓库本身：直接引用 rules/，不生成副本。用目录特征判断，wheel 与可编辑安装下结论一致。"""
    return (root / f"skills/{NAME}/SKILL.md").is_file() and (root / "rules/code-style.md").is_file()


def skill_dirs(tools: list[str]) -> list[str]:
    """已选工具的 skill 发现路径；OpenCode、Cursor、Codex 共用一份 .agents/skills。"""
    dirs = []
    if "claude" in tools:
        dirs.append(f".claude/skills/{NAME}")
    if any(tool in tools for tool in AGENTS_SKILL_TOOLS):
        dirs.append(f".agents/skills/{NAME}")
    return dirs


def generated_files(tools: list[str], rules: tuple[str, ...] | list[str] = COPIED_SHARED) -> dict[str, str]:
    """项目内只读副本：相对路径 → 内容。.rulemason/ 放 rules 指定的共享文件加 README，再加各已选工具的 skill。"""
    src = shared_root()
    out = {f"{COPY_DIR}/{rel}": (src / rel).read_text(encoding="utf-8") for rel in rules}
    listed = "\n".join(f"- `{rel}`" for rel in rules)
    out[f"{COPY_DIR}/README.md"] = Template(template("copies-README.md")).safe_substitute(files=listed)
    for target in skill_dirs(tools):
        for rel in SKILL_FILES:
            out[f"{target}/{rel}"] = (src / f"skills/{NAME}" / rel).read_text(encoding="utf-8")
    return out


def copy_record(files: dict[str, str]) -> dict[str, str]:
    """生成副本的清单记录：相对路径 → 校验值。init / update 写进清单，check 拿来比较是否落后。"""
    return {rel: sha256_text(content) for rel, content in files.items()}


# result-check 预设：仅首次种入，不进清单覆盖集
RESULT_CHECK_PRESET_DIR = f"{COPY_DIR}/result-check"
RESULT_CHECK_PRESETS = (
    "prose-hygiene.hint.json",
    "prose-hygiene.strict.json",
    "product-artifact.hint.json",
    "product-artifact.strict.json",
)
# --preset 取值 → 包内文件名（无 .json）。hint/strict 仍是 prose-hygiene 短别名，不得偷换成产物结构预设
RESULT_CHECK_PRESET_IDS: dict[str, str] = {
    "hint": "prose-hygiene.hint",
    "strict": "prose-hygiene.strict",
    "prose-hygiene.hint": "prose-hygiene.hint",
    "prose-hygiene.strict": "prose-hygiene.strict",
    "product-artifact.hint": "product-artifact.hint",
    "product-artifact.strict": "product-artifact.strict",
}


def normalize_result_check_preset(name: str) -> str:
    """把 CLI --preset 取值归一成包内文件名（无 .json）；非法则 ValueError。"""
    key = RESULT_CHECK_PRESET_IDS.get(name)
    if key is None:
        raise ValueError(
            "preset 必须是 hint、strict、prose-hygiene.hint、prose-hygiene.strict、"
            "product-artifact.hint 或 product-artifact.strict"
        )
    return key


def packaged_result_check_preset(name: str) -> str:
    """读取包内预设正文；name 为短别名或完整 id（见 RESULT_CHECK_PRESET_IDS）。"""
    key = normalize_result_check_preset(name)
    path = Path(__file__).parent / "templates" / "result-check" / f"{key}.json"
    return path.read_text(encoding="utf-8")


def resolve_result_check_preset(root: Path | None, name: str) -> Path | str:
    """项目种子优先，否则返回包内正文字符串。"""
    key = normalize_result_check_preset(name)
    if root is not None:
        seeded = root / RESULT_CHECK_PRESET_DIR / f"{key}.json"
        if seeded.is_file():
            return seeded
    return packaged_result_check_preset(key)


def seed_result_check_presets(root: Path) -> list[str]:
    """若目标不存在则写入预设；已存在则跳过。返回新写入的相对路径列表。"""
    written: list[str] = []
    for filename in RESULT_CHECK_PRESETS:
        rel = f"{RESULT_CHECK_PRESET_DIR}/{filename}"
        dest = root / rel
        if dest.is_file() or dest.is_symlink():
            continue
        stem = filename.removesuffix(".json")
        write_text(dest, packaged_result_check_preset(stem))
        written.append(rel)
    return written


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """按 LF 归一后计算：Windows 检出（autocrlf）的 CRLF 不算手改。"""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(text).lstrip("v").split("."))


# ---------- 2. 写文件与 manifest ----------

def write_text(path: Path, content: str) -> None:
    """在同一目录暂存再原子替换；拒绝写入符号链接。已有文件沿用原权限与 CRLF 换行，新文件按 umask 建、写 LF。"""
    if path.is_symlink():
        raise ValueError(f"拒绝写入符号链接：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        mode = path.stat().st_mode & 0o777
        if b"\r\n" in path.read_bytes():
            content = content.replace("\r\n", "\n").replace("\n", "\r\n")
    else:
        mode = 0o666 & ~_umask()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{NAME}-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:   # 原样写 LF，校验值与平台无关
            stream.write(content)
        os.chmod(temporary, mode)                            # mkstemp 建的是 0600
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _umask() -> int:
    current = os.umask(0)
    os.umask(current)
    return current


def read_manifest(root: Path) -> dict | None:
    """读 .rulemason.yaml；不存在返回 None，外形不对抛 ManifestError。其他用户字段原样保留。"""
    path = root / MANIFEST
    if path.is_symlink():
        raise ManifestError(f"拒绝读取符号链接 {MANIFEST}")
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:     # ValueError 含编码错误，以及不加引号的日期月日不存在
        raise ManifestError(f"无法读取 {MANIFEST}：{exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{MANIFEST} 必须是 YAML 对象")
    check_manifest_fields(data)
    return data


def check_manifest_fields(data: dict) -> None:
    """清单各键的外形；不对抛 ManifestError。接入日期就地统一成字符串。"""
    if data.get("version") != SCHEMA_VERSION:
        raise ManifestError(f"不支持的 {MANIFEST} version：{data.get('version')}")
    tools = data.get("tools")
    if not isinstance(tools, list):
        raise ManifestError(f"{MANIFEST} 的 tools 必须是列表")
    unknown = [tool for tool in tools if tool not in TOOL_IDS]
    if unknown:
        raise ManifestError(f"{MANIFEST} 有不支持的工具：{'、'.join(map(str, unknown))}")
    if NAME in data and not re.fullmatch(r"\d+(\.\d+)*", str(data[NAME])):
        raise ManifestError(f"{MANIFEST} 的 {NAME} 版本格式无效：{data[NAME]}")
    if not isinstance(data.get("files", {}), dict):
        raise ManifestError(f"{MANIFEST} 的 files 必须是对象")
    if JOINED in data:
        data[JOINED] = joined_text(data[JOINED])


def joined_text(value: object) -> str:
    """接入日期统一成 YYYY-MM-DD 字符串：用户手改去掉引号时 YAML 会读成 date。格式不对抛 ManifestError。"""
    text = str(value)
    error = ManifestError(f"{MANIFEST} 的 {JOINED} 格式无效（应为 YYYY-MM-DD）：{value}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise error
    try:
        date.fromisoformat(text)
    except ValueError as exc:                                # 形如日期、但月日不存在（如 2026-13-40）
        raise error from exc
    return text


def joined_date(root: Path, manifest: dict | None) -> str | None:
    """接入日期：清单有就用；没有就取 git 里第一次加入清单的提交日期；都没有返回 None。"""
    if manifest and JOINED in manifest:
        return manifest[JOINED]
    added = git(root, "log", "--diff-filter=A", "--format=%cs", "--", MANIFEST).split()
    return added[-1] if added else None                      # git log 新的在前，最后一行是第一次加入


def manifest_text(current: dict | None, tools: list[str], files: dict[str, str], joined: str) -> str:
    """新的 .rulemason.yaml 内容：只更新 rulemason 拥有的键，保留用户自加的键与顺序；接入日期新加时排在版本号之后。"""
    data = {"version": SCHEMA_VERSION, NAME: __version__, JOINED: joined}
    data |= {key: value for key, value in (current or {}).items() if key not in data}
    data["tools"] = normalize_tools(tools)
    data["files"] = dict(sorted(files.items()))
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def normalize_tools(tools: list[str]) -> list[str]:
    """校验工具 id、去重并按 TOOL_IDS 的稳定顺序返回。"""
    selected = set()
    for value in tools:
        tool = value.strip().lower()
        if tool not in TOOL_IDS:
            raise ValueError(f"不支持的工具：{value}（可选：{'、'.join(TOOL_IDS)}）")
        selected.add(tool)
    return [tool for tool in TOOL_IDS if tool in selected]


# ---------- 3. 列文件与 git ----------

def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8").stdout


def has_git(root: Path) -> bool:
    out = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return out.returncode == 0 and out.stdout.strip() == "true"


class Scan(NamedTuple):
    files: list[str]                      # 属于本项目的文件（相对路径）
    skipped: list[tuple[str, str]]        # (目录, 原因)：不属于本项目、整个跳过的子目录


def boundary_reason(path: Path) -> str | None:
    """子目录不属于本项目的原因；属于本项目返回 None。"""
    if path.name in VENDOR_DIRS:
        return THIRD_PARTY
    if path.name == "vendor" and any((path / marker).is_file() for marker in VENDOR_MARKERS):
        return THIRD_PARTY
    if (path / ".git").exists():
        return OTHER_REPO
    if has_manifest(path):
        return OTHER_PROJECT
    return None


def scan(root: Path) -> Scan:
    """先遍历目录定出边界（有没有 git 都一样），再取文件：有 git 用 git 的忽略规则，没有 git 用遍历结果。"""
    # 1. 遍历目录：固定忽略清单与 git 忽略的目录静默跳过；子仓库、子项目、第三方目录跳过并记下原因
    in_git = has_git(root)
    ignored = ignored_dirs(root) if in_git else set()
    excluded = ignored | {PLAN_DIR}
    skipped: list[tuple[str, str]] = []
    walked: list[str] = []
    for current, dirs, names in os.walk(root):
        rel = Path(current).relative_to(root)
        kept = []
        for name in sorted(d for d in dirs if d not in SKIP_DIRS and (rel / d).as_posix() not in excluded):
            reason = boundary_reason(Path(current) / name)
            if reason:
                skipped.append(((rel / name).as_posix(), reason))
            else:
                kept.append(name)
        dirs[:] = kept
        walked += [(rel / name).as_posix() for name in sorted(names)]
    if not in_git:
        return Scan(walked, skipped)

    # 2. 有 git：沿用 git 的忽略规则，再去掉落在跳过目录里的路径
    outside = (*(f"{d}/" for d, _ in skipped), f"{PLAN_DIR}/")
    listed = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    files = [f for f in listed if f and not f.startswith(outside) and (root / f).is_file()]   # 已删除但未提交的文件仍在索引里，跳过
    return Scan(files, skipped)


def ignored_dirs(root: Path) -> set[str]:
    """被 .gitignore 等规则整个忽略的目录（相对 root）；遍历时不进去，免得在 target/、.next/ 这类大目录里空转。"""
    listed = git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory").split("\0")
    return {entry.rstrip("/") for entry in listed if entry.endswith("/")}


def list_files(root: Path) -> list[str]:
    """属于本项目的文件（相对路径）。"""
    return scan(root).files


def shown_list(items: list[str]) -> str:
    """用「、」连起来；多于 SHOWN_DIRS 个只列前面的并写总数；没有返回空串。"""
    shown = "、".join(items[:SHOWN_DIRS])
    if len(items) > SHOWN_DIRS:
        return f"{shown} 等共 {len(items)} 个"
    return shown


def has_python(files: list[str]) -> bool:
    return any(f.endswith(".py") for f in files)


def languages(files: list[str]) -> list[str]:
    """识别出的语言：Python 看 .py 文件，JS/TS 看 package.json；都没有返回空列表。"""
    names = {Path(f).name for f in files}
    return [lang for lang, ok in (("Python", has_python(files)), ("JS/TS", "package.json" in names)) if ok]


def folder_hint(scanned: Scan) -> str | None:
    """项目根像放项目的文件夹时给 init 与 check 的提示；不像时返回 None。
    判断只看两条：识别不出语言，且有子目录是另一个仓库或另一个 rulemason 项目。"""
    projects = [d for d, reason in scanned.skipped if reason in (OTHER_REPO, OTHER_PROJECT)]
    if languages(scanned.files) or not projects:
        return None
    return (f"这里有独立项目 {shown_list(projects)}；如果这里只是放项目的文件夹，建议到各项目里分别运行 {NAME} init；"
            "同时改几个项目时，在主要改的项目里打开 AI 工具，再挂上相关项目（如 --add-dir）")


def ignored_files(root: Path, rels: list[str]) -> list[str]:
    """rels 中被 .gitignore 等忽略规则匹配的路径;由 git 判断,含多级 .gitignore 与全局 excludes。
    --no-index:已跟踪的文件也照规则判断,否则 update 新增的副本会被静默忽略。git 的输入输出都按 UTF-8,Windows 中文版默认 GBK。"""
    out = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin", "-z"],
        cwd=root, input="\0".join(rels), capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode not in (0, 1):
        # 0 有被忽略的、1 一个都没有;其他是 git 出错,不能当成「没有被忽略」放行
        raise ValueError(f"git check-ignore 失败：{out.stderr.strip()}")
    return [rel for rel in out.stdout.split("\0") if rel]


def dirty_files(root: Path) -> list[str] | None:
    """未提交改动的文件；没有 git 时返回 None（无法统计）。"""
    if not has_git(root):
        return None
    prefix = git(root, "rev-parse", "--show-prefix").strip()          # 项目根在仓库里的位置；仓库根时为空
    entries = git(root, "status", "--porcelain", "-z", "--untracked-files=all", "--", ".").split("\0")
    out = []
    skip = False
    for entry in entries:
        if skip or not entry:
            # 走到这里说明是改名记录后附带的原路径，或末尾空串
            skip = False
            continue
        out.append(entry[3:].removeprefix(prefix))                  # porcelain 的路径总是相对仓库根
        skip = entry[0] in "RC"
    return out


class ConfigError(ValueError):
    """项目配置文件读不出来（不是 UTF-8、不是合法 YAML、顶层类型不对、判断规则条目不是带 id 的映射）；命令行外层按 ValueError 给出可读提示。"""


def display_name(path: Path) -> str:
    """提示里用的文件名：上一级目录加文件名（如 openspec/config.yaml），不暴露本机绝对路径。"""
    if not path.parent.name:
        return path.name
    return f"{path.parent.name}/{path.name}"


def read_yaml(path: Path, default: Any) -> Any:
    """读 YAML；不存在或为空返回 default。读不出来时抛 ConfigError，写明文件与行号。"""
    if not path.exists():
        return default
    name = display_name(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{name} 不是 UTF-8 编码") from exc
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)                # 只有带位置的解析错误才有行号与原因
        where = f"第 {mark.line + 1} 行：" if mark else ""
        reason = getattr(exc, "problem", None) or exc
        raise ConfigError(f"{name} 不是合法的 YAML（{where}{reason}）") from exc
    if data is None:
        return default
    if not isinstance(data, type(default)):
        kind = "映射" if isinstance(default, dict) else "列表"
        raise ConfigError(f"{name} 的顶层应是{kind}")
    return data


def read_judgments(path: Path) -> list[dict]:
    """读判断规则列表；不存在或为空返回空列表。有一条不是带字符串 id 的映射时抛 ConfigError，写明第几条。"""
    items = read_yaml(path, [])
    for n, item in enumerate(items, 1):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ConfigError(f"{display_name(path)} 第 {n} 条不是带 id 的映射")
    return items


def dump_json(data: dict) -> str:
    """--json 输出的统一格式：中文原样输出、缩进 2。"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def bullets(items: list[str]) -> str:
    """每项一行「  - 项」，末尾带换行；没有项时为空串。配合 print(..., end="") 使用。"""
    return "".join(f"  - {item}\n" for item in items)
