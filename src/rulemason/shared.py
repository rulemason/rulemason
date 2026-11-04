"""共享数据定位、名字常量、生成副本清单、.rulemason.yaml 读写、校验值与列文件：init / update / check 共用这一份。"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
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
TOOL_IDS = ("opencode", "claude", "cursor", "codex")
TOOL_LABELS = {"opencode": "OpenCode", "claude": "Claude Code", "cursor": "Cursor", "codex": "Codex"}
AGENTS_SKILL_TOOLS = ("opencode", "cursor", "codex")         # 这三个工具都从 .agents/skills 发现 skill
COPIED_SHARED = (
    "rules/code-style.md",
    "rules/python.md",
    "rules/react.md",
    "rules/workflow-gates.md",
    "rules/copy-voice.md",
    "lint/ruff-base.toml",
    "lint/eslint-base.mjs",
)
SKILL_FILES = ("SKILL.md",)                                  # skill 副本只有正文；判断层模板随安装包提供
TEMPLATES = Path(__file__).parent / "templates"
VENDOR_DIRS = ("bower_components", "uni_modules", "third_party", "jspm_packages", "Pods")   # 第三方代码，不属于本项目
VENDOR_MARKERS = ("autoload.php", "modules.txt")            # vendor/ 有 Composer 或 Go 的标记才算第三方；项目也会用它放自己的资源
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", COPY_DIR, ".pytest_cache", ".ruff_cache", "dist", "build"}
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


def find_root(start: Path) -> Path:
    """项目根：从 start 往上找最近的有清单的目录，不越过所在 git 仓库的根。
    找不到清单时返回 git 仓库根，不在 git 里则返回 start。"""
    for current in (start, *start.parents):
        if has_manifest(current):
            return current
        if (current / ".git").exists():
            # 走到这里说明到了仓库根还没有清单：不再往上，上层目录属于别的项目或工作区
            return current
    return start


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
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ManifestError(f"无法读取 {MANIFEST}：{exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{MANIFEST} 必须是 YAML 对象")
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
    return data


def manifest_text(current: dict | None, tools: list[str], files: dict[str, str]) -> str:
    """新的 .rulemason.yaml 内容：只更新 rulemason 拥有的键，保留用户自加的键与顺序。"""
    data = dict(current or {})
    data["version"] = SCHEMA_VERSION
    data[NAME] = __version__
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
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout


def has_git(root: Path) -> bool:
    out = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True)
    return out.returncode == 0 and out.stdout.strip() == "true"


class Scan(NamedTuple):
    files: list[str]                      # 属于本项目的文件（相对路径）
    skipped: list[tuple[str, str]]        # (目录, 原因)：不属于本项目、整个跳过的子目录


def boundary_reason(path: Path) -> str | None:
    """子目录不属于本项目的原因；属于本项目返回 None。"""
    if path.name in VENDOR_DIRS:
        return "第三方目录"
    if path.name == "vendor" and any((path / marker).is_file() for marker in VENDOR_MARKERS):
        return "第三方目录"
    if (path / ".git").exists():
        return "另一个仓库"
    if has_manifest(path):
        return "另一个 rulemason 项目"
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


def ignored_files(root: Path, rels: list[str]) -> list[str]:
    """rels 中被 .gitignore 等忽略规则匹配的路径;由 git 判断,含多级 .gitignore 与全局 excludes。
    --no-index:已跟踪的文件也照规则判断,否则 update 新增的副本会被静默忽略。"""
    out = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin", "-z"], cwd=root, input="\0".join(rels), capture_output=True, text=True
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
