"""rulemason 命令行测试的共用工具：临时项目里写文件、git 初始化与提交。"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from rulemason import cli
from rulemason.init import OPERATIONS_COMMENT

REACT_PACKAGE = '{"name": "web", "dependencies": {"react": "19.0.0"}}\n'   # 依赖 react 的 package.json


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")


def project_folder(root: Path) -> None:
    """放项目的文件夹：自己只有说明文件，下面 b 是有 Python 代码的 git 仓库，c 是另一个 rulemason 项目。"""
    write(root, "README.md", "# 产品目录\n")
    git_init(root / "b")
    write(root / "b", "main.py", "x = 1\n")
    write(root, "c/.rulemason.yaml", "version: 1\ntools: []\n")


def snapshot(root: Path) -> dict[str, str]:
    """项目里全部文件（不含 .git/）的内容，用来断言「没有任何改动」。"""
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def write_manifest(root: Path, manifest: dict) -> None:
    write(root, ".rulemason.yaml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))


def commit(root: Path, subject: str = "x") -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", subject)


def drop_operations(root: Path) -> None:
    """去掉 init 追加的 operations 段，伪造成 0.7.1 接入的项目。"""
    config = root / "openspec/config.yaml"
    config.write_text(config.read_text(encoding="utf-8").split(f"\n{OPERATIONS_COMMENT}")[0] + "\n", encoding="utf-8")


def run_cli(*argv: str) -> int | str:
    """同进程运行 rulemason 命令行，返回退出码；外层把错误转成可读提示时是那条提示字符串。"""
    with pytest.raises(SystemExit) as e:
        cli.main(list(argv))
    return e.value.code


@pytest.fixture
def gbk_default(monkeypatch):
    """复现 Windows 中文版：text=True 而没写 encoding 的子进程调用按 GBK 编解码。"""
    real_run = subprocess.run

    def run(*args, **kwargs):
        if kwargs.get("text") and "encoding" not in kwargs:
            kwargs["encoding"] = "gbk"
        return real_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
