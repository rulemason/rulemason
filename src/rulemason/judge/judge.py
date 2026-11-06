"""判断层：按 openspec/judgments.yaml 检查 change 产物与界面文案是否违反既定规矩，各项目共用这一份。

在接入项目内任意目录运行（以所在 git 仓库的根为项目根）：
    rulemason judge --change <name>   审 openspec/changes/<name>（或 archive/<name>）下的 proposal / design / tasks / specs
    rulemason judge --copy            审 openspec/judge.yaml 配置的界面文案相对 main 分支新增或修改的条目
    rulemason judge --direct <文件>   审一份不走 OpenSpec 的直接改动说明（四段：要做什么、改哪些文件、主规格与检索命中、判路与理由）
    加 --lint-only 只跑正则检查（不需要 key 与网络）；加 --dry-run 打印将要发送的请求体而不发送。

规则 = 引擎自带的通用规则（base/judgments.yaml）+ 项目的 openspec/judgments.yaml，同 id 以项目为准。
裁判由 JUDGE_PROVIDER 决定：jev（需 TYPESAFE_API_KEY）或 manual（把问题打印给人填）；两项都先读环境变量，再读 ~/.config/rulemason/env（没有时读旧位置 ~/.config/jev-judge/env）。
只检查「有没有违反已定规矩」，不检查「方案好不好」。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from functools import cache
from pathlib import Path
from typing import Any, Literal

import json5
from pydantic import BaseModel, Field, ValidationError, model_validator

from rulemason.shared import (
    ConfigError,
    fail,
    find_root,
    git,
    has_git,
    read_judgments,
    read_yaml,
    repo_root,
)

BASE = Path(__file__).parent / "base"                       # 随引擎提供的通用规则与通用词表
KEY_NAME = "TYPESAFE_API_KEY"                               # Jev 的 key 在环境变量与 key 文件里的名字
TEMPLATES = Path(__file__).parent / "templates"             # 启用判断层时项目照着写的模板，随安装包提供，不复制进项目
TEMPLATE_NAMES = ("judgments", "judge", "judge_cases")
USER_ENV = Path.home() / ".config/rulemason/env"            # key 只放这一处，不读项目里的 .env
OLD_USER_ENV = Path.home() / ".config/jev-judge/env"        # 旧位置：新位置没有时只读兜底，已配置的机器不用重放 key
JEV_MODEL = "jev-1.14.0"                                    # 固定版本，不用 jev-latest；升级前先跑引擎测试与各项目回归
SHORT_LABEL = 4                                             # 不超过四个字的标签不送模型，查词表（rules/copy-voice.md）

Verdict = Literal["pass", "review", "block"]
Target = Literal["proposal", "design", "tasks", "specs", "copy", "chat", "direct"]   # chat：问答忠实度，由项目的评估测试调用；direct：不走 OpenSpec 的直接改动说明
Answer = tuple[float, float | None]                         # (模型数值, 置信度)；noul 没有置信度
Answers = dict[str, Answer]                                 # 规则 id → Answer


# ---------- 1. 项目 ----------

@cache
def root() -> Path:
    """项目根：最近的 .rulemason.yaml（不越过 git 仓库根），没有清单时用 git 仓库根，且必须在 git 里、有 openspec/。不满足就退出。
    与 init 不同：没有清单时不用当前目录，因为未接入 rulemason 的仓库也要能在子目录里找到 openspec/。"""
    if not has_git(Path.cwd()):
        sys.exit(fail("当前目录不在 git 仓库里：请在接入项目内运行 rulemason judge"))
    cwd = Path.cwd().resolve()
    path = find_root(cwd) or repo_root(cwd) or cwd             # 走到 or cwd 说明 git 认得仓库却找不到 .git（如 GIT_DIR 指向别处）
    if not (path / "openspec").is_dir():
        sys.exit(fail(f"{path} 下没有 openspec/：请在接入项目内运行 rulemason judge"))
    return path


@cache
def config() -> dict[str, Any]:
    """项目的 openspec/judge.yaml；没有这个文件当作空配置，只审 change 的项目用不到它。"""
    return read_yaml(root() / "openspec/judge.yaml", {})


def copy_config() -> tuple[str, str, str | None]:
    """返回 (文案文件, 格式, 语言)；语言只有 js-i18n 格式才有。缺项就退出并说明缺哪项，不猜默认值。"""
    copy = config().get("copy") or {}
    for key in ("file", "format"):
        if not copy.get(key):
            sys.exit(fail(f"openspec/judge.yaml 缺少 copy.{key}：--copy 需要知道审哪个文件、什么格式"))
    if copy["format"] not in ("json", "js-i18n"):
        sys.exit(fail(f"openspec/judge.yaml 的 copy.format={copy['format']!r} 无效，只支持 json 或 js-i18n"))
    if copy["format"] == "js-i18n" and not copy.get("lang"):
        sys.exit(fail("openspec/judge.yaml 缺少 copy.lang：js-i18n 格式需要知道审哪种语言"))
    return copy["file"], copy["format"], copy.get("lang")


def user_env() -> Path | None:
    """key 文件：新位置优先，没有时读旧位置；都没有返回 None。只读，不创建、不搬运。"""
    for path in (USER_ENV, OLD_USER_ENV):
        if path.exists():
            return path
    return None


def setting_with_source(name: str) -> tuple[str, str]:
    """先读环境变量，再读 key 文件（每行 KEY=VALUE）。返回 (值, 来源)：来源是「环境变量 NAME」或 key 文件路径；都没有返回 ("", "")。"""
    value = os.getenv(name, "").strip()
    if value:
        return value, f"环境变量 {name}"
    env_file = user_env()
    if env_file is None:
        return "", ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, sep, val = line.partition("=")
        if sep and key.strip() == name:
            return val.strip().strip("\"'"), str(env_file)
    return "", ""


def setting(name: str) -> str:
    return setting_with_source(name)[0]


def key_problem(value: str) -> str | None:
    """key 的字符是否合法（与 SDK 的校验一致：只许可打印 ASCII、不含空白）。不合法返回给人看的原因，合法返回 None。"""
    if "\x16" in value:
        return "含控制字符 0x16（按 Ctrl+V 没有粘贴进去）"
    if any(ch.isspace() for ch in value):
        return "含空白"
    if not (value.isascii() and value.isprintable()):
        return "含不可打印或非 ASCII 字符"
    return None


def paste_hint(value: str) -> str:
    """key 里有 0x16 时补一句粘贴方式，接在「重新运行 rulemason key」之后；没有返回空串。"""
    return "，用右键或 Ctrl+Shift+V 粘贴" if "\x16" in value else ""


# ---------- 2. 规则 ----------

class Thresholds(BaseModel):
    pass_: float = Field(alias="pass")                      # pass 是 Python 关键字，yaml 里仍写 pass
    block: float
    min_confidence: float = 0.5


class Rule(BaseModel):
    id: str
    target: Target
    enforces: str
    type: Literal["noul", "score"]
    question: str
    thresholds: Thresholds
    expect: bool | None = None                              # noul：期望陈述为真还是为假
    levels: list[Any] | None = None                         # score：2 到 10 档，由低到高

    @model_validator(mode="after")
    def _shape(self) -> Rule:
        if self.type == "noul" and self.expect is None:
            raise ValueError("noul 规则必须有 expect")
        if self.type == "score" and not (self.levels and 2 <= len(self.levels) <= 10):
            raise ValueError("score 规则必须有 2 到 10 档 levels")
        return self


def enforces_exists(ref: str) -> bool:
    """enforces 指向的上层规则在项目里是否存在。格式：L0/<项目指令标题>、L1/<产物或 context>、specs/<名>。"""
    kind, _, name = ref.partition("/")
    if kind == "L0":
        project = root()
        instructions = project / "AGENTS.md"
        if not instructions.is_file():
            instructions = project / "CLAUDE.md"
        if not instructions.is_file():
            return False
        heads = re.findall(r"^##\s+(.+)$", instructions.read_text(encoding="utf-8"), re.M)
        return any(h.startswith(name) for h in heads)
    if kind == "L1":
        cfg = read_yaml(root() / "openspec/config.yaml", {})
        # context 是单独一段，其余产物名都在 rules 下面
        if name == "context":
            return bool(cfg.get("context"))
        return name in (cfg.get("rules") or {})
    if kind == "specs":
        # 主规格或尚未归档的 change 里的规格都算
        main_spec = root() / f"openspec/specs/{name}/spec.md"
        return main_spec.exists() or any(root().glob(f"openspec/changes/*/specs/{name}/spec.md"))
    return False


def load_rules(path: Path | None = None) -> list[Rule]:
    """通用规则 + 项目规则（默认项目的 openspec/judgments.yaml），同 id 以项目为准。

    任何一条不合格就带着 id 退出，不让坏规则进入评估。项目规则文件可以不存在：只用通用规则的项目（如 rulemason 自己）也能跑。
    """
    # 1. 合并：先通用后项目，项目同 id 覆盖通用、位置不变
    project = path or root() / "openspec/judgments.yaml"
    items = {item["id"]: item for item in read_judgments(BASE / "judgments.yaml")}
    items.update({item["id"]: item for item in read_judgments(project)})       # 文件不存在时为空

    # 2. 逐条校验
    rules: list[Rule] = []
    for item in items.values():
        try:
            rule = Rule.model_validate(item)
        except ValidationError as e:
            sys.exit(fail(f"判断规则 {item.get('id')!r} 不合格：{e.errors()[0]['msg']}"))
        # 找不到上层规则说明规矩还没定，不许在判断层立法
        if not enforces_exists(rule.enforces):
            sys.exit(fail(f"规则 {rule.id} 的 enforces 指向不存在的上层规则：{rule.enforces}"))
        rules.append(rule)
    return rules


# ---------- 3. 三段判定 ----------

def verdict(rule: Rule, value: float, confidence: float | None) -> tuple[Verdict, str]:
    """把模型数值翻成 (结果, 一句原因)。

    p 达到 pass 阈值为 pass，低于 block 阈值为 block，其余为 review，原因写 p 值；
    score 规则置信度低于 min_confidence 时不看分数，一律 review，原因写「置信度不足」。
    """
    if rule.type == "noul":
        p = value if rule.expect else 1 - value             # expect=false 的违规检查：模型说「没有」才是好事
    else:
        p = value / (len(rule.levels) - 1)                  # 归一到 0 到 1，不同档数的规则才能共用阈值
        if confidence is not None and confidence < rule.thresholds.min_confidence:
            # 走到这里说明模型在几档之间拿不准，分数不可信
            return "review", f"置信度不足 {confidence:.2f}（分 {value:.2f}）"
    why = f"p={p:.2f}"
    if p >= rule.thresholds.pass_:
        return "pass", why
    if p < rule.thresholds.block:
        return "block", why
    return "review", why


def verdict_or_pending(rule: Rule, answers: Answers) -> tuple[Verdict, str]:
    """有模型答案就判定；没有（人工模式或 dry-run）就记 review 待人工。"""
    if rule.id not in answers:
        return "review", "待人工"
    return verdict(rule, *answers[rule.id])


# ---------- 4. 裁判 ----------

def api_key() -> str:
    return setting(KEY_NAME)


def pick_provider() -> str:
    """jev | manual。未指定时有 key 走 jev；指定 jev 却没 key 直接报错，不悄悄退化。"""
    key = api_key()
    name = setting("JUDGE_PROVIDER") or ("jev" if key else "manual")
    if name not in ("jev", "manual"):
        sys.exit(fail(f"JUDGE_PROVIDER={name!r} 无效，只支持 jev 或 manual"))
    if name == "jev" and not key:
        sys.exit(fail(f"JUDGE_PROVIDER=jev 但缺少 TYPESAFE_API_KEY：请设置环境变量，或写入 {USER_ENV}"))
    return name


def build_questions(rules: list[Rule]) -> dict[str, Any]:
    """规则 → SDK 问题对象，按规则 id 索引。"""
    from typesafe_sdk import Noul, Score  # 懒导入：manual / lint-only 不触发 SDK 加载
    return {
        r.id: Noul(instructions=r.question) if r.type == "noul" else Score(instructions=r.question, criteria=r.levels)
        for r in rules
    }


class Judge:
    """一次运行一个裁判。ask() 的输入输出与裁判无关，manual 返回空答案，让所有问题落 review。

    jev 裁判在首次 ask() 时建连接并复用（--copy 一条一请求，每次新建连接就是每条一次握手），用完 close()。
    """

    def __init__(self, provider: str, dry_run: bool = False):
        self.provider = provider
        self.dry_run = dry_run
        self._client = None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _jev(self):
        """懒建 SDK 客户端。trust_env=False 绕过 shell 代理：大陆直连稳定，走代理偶发断连。"""
        if self._client is None:
            import httpx2
            from typesafe_sdk import TypeSafeClient
            key, source = setting_with_source(KEY_NAME)
            problem = key_problem(key)
            if problem:
                # 走到这里说明 key 写坏了（常见是 Windows 上按 Ctrl+V 只写进 0x16）：一句话说清来源与修法，不让 SDK 抛堆栈。
                # 环境变量优先于 key 文件，来自环境变量时重写文件没用，要改环境变量
                from_env = bool(os.getenv(KEY_NAME, "").strip())   # 与 setting_with_source 同一优先级：环境变量有值就用它
                fix = f"请修正或删除环境变量 {KEY_NAME}" if from_env else f"运行 rulemason key 重新输入{paste_hint(key)}"
                sys.exit(fail(f"{KEY_NAME}（来自{source}）{problem}：{fix}"))
            self._client = TypeSafeClient(api_key=key, model=JEV_MODEL,
                                          http_client=httpx2.Client(trust_env=False))
        return self._client

    def ask(self, state: str, rules: list[Rule]) -> Answers:
        # 1. 人工模式：打印清单给人勾，不发请求；带 --dry-run 时不走这里，让没有 key 的人也能核对请求
        if self.provider == "manual" and not self.dry_run:
            print(f"  （人工模式，待审文本 {len(state)} 字；逐条填 pass / review / block）")
            for r in rules:
                print(f"  [ ] {r.id}：{r.question}")
            return {}

        # 2. dry-run：原样打印请求体，state 与 questions 分字段，不发送
        questions = build_questions(rules)
        if self.dry_run:
            payload = {
                "model": JEV_MODEL,
                "state": state,
                "questions": {k: q.model_dump(exclude_none=True) for k, q in questions.items()},
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return {}

        # 3. 问 Jev
        resp = self._jev().system_one(state=state, questions=questions)

        answers: Answers = {}
        for r in rules:
            a = resp.answers[r.id]
            answers[r.id] = (a.noul, None) if r.type == "noul" else (a.score, a.confidence)
        return answers


# ---------- 5. lint：能用正则或词表判死的，不进 judgments.yaml ----------

BANNED = (("！", "感叹号"), ("!", "感叹号"), (":(", "颜文字"), (":)", "颜文字"), ("Oops", "英文感叹词"), ("Whoops", "英文感叹词"))
# Risks 行：产物写法规定「- [风险] → 对策」，同时接受早期 design 的「- **风险** → 对策」
RISK_LINE = re.compile(r"^- (\[.+?\]|\*\*.+?\*\*)\s*→\s*\S")
REJECTED = re.compile(r"否决|备选|未采用|不采用|alternative|rejected", re.I)   # 决策写了被否决的备选方案


def lint_copy(text: str) -> str | None:
    """面向用户的文案不得含感叹号、颜文字、英文感叹词，也不得含项目在 judge.yaml 配置的禁词。命中返回原因，没命中返回 None。"""
    for needle, why in BANNED:
        if needle in text:
            return f"含{why}「{needle}」"
    for word in config().get("banned") or []:
        if word in text:
            return f"含项目禁词「{word}」"
    return None


def _section(md: str, title: str) -> str | None:
    """取 markdown 里以 title 开头的二级小节正文；没有这一节返回 None。"""
    m = re.search(rf"^##\s+{re.escape(title)}.*?$(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    return m.group(1) if m else None


def _decision_problems(decisions: str) -> list[str]:
    """Decisions 里没写否决或备选理由的决策。按 ### 分条，只查标题以下的正文（标题里的「备选」不算理由），
    第一个 ### 之前的引导文字不归入任何一条；没有 ### 时整节当作一条，整节为空时不查。
    返回「决策缺否决理由：<标题前 30 字>」的列表，空列表表示全部写了理由。"""
    if not decisions.strip():
        return []
    parts = re.split(r"^###[ \t]+", decisions, flags=re.M)
    if len(parts) == 1:
        # 走到这里说明没有 ### 子小节：整节就是一条决策，没有标题行
        if REJECTED.search(decisions):
            return []
        return [f"决策缺否决理由：{decisions.strip().splitlines()[0][:30]}"]
    problems = []
    for item in parts[1:]:
        title, _, body = item.partition("\n")
        if not REJECTED.search(body):
            problems.append(f"决策缺否决理由：{title.strip()[:30]}")
    return problems


def lint_design(md: str) -> list[str]:
    """Decisions 每个 ### 决策须写否决或备选理由；Risks 每行须为「- [风险] → 对策」或「- **风险** → 对策」；
    Migration Plan 须含「回滚」。返回问题清单，空表示通过。"""
    problems = []
    decisions = _section(md, "Decisions")
    if decisions is not None:
        problems += _decision_problems(decisions)
    risks = _section(md, "Risks")
    if risks is not None:
        for line in risks.splitlines():
            if line.startswith("- ") and not RISK_LINE.match(line):
                problems.append(f"Risks 行不符合「[风险] → 对策」格式：{line[:40]}")
    plan = _section(md, "Migration Plan")
    if plan is None or "回滚" not in plan:
        problems.append("Migration Plan 缺少回滚说明")
    return problems


DIRECT_SECTIONS = ("要做什么", "改哪些文件", "主规格与检索命中", "判路与理由")      # 直接改动说明必须有的四段，标题固定


def lint_direct(md: str) -> list[str]:
    """直接改动说明缺哪几段（二级标题）或哪几段是空的；返回问题清单，空表示四段齐全且都有正文。"""
    problems = []
    for title in DIRECT_SECTIONS:
        body = _section(md, title)
        if body is None:
            problems.append(f"缺少「{title}」一段")
        elif not body.strip():
            problems.append(f"「{title}」一段是空的")
    return problems


def label_len(text: str) -> int:
    """短标签长度：去掉 {占位符} 与空白后数字符。「前 {y}」算一个字。"""
    return len(re.sub(r"\{[^}]*\}|\s", "", text))


def _labels(path: Path) -> set[str]:
    return set(read_yaml(path, {}).get("labels") or [])


def lexicon() -> set[str]:
    """通用词表 + 项目的 openspec/copy-lexicon.yaml；项目没有词表文件时只用通用词表。"""
    labels = _labels(BASE / "copy-lexicon.yaml")
    return labels | _labels(root() / "openspec/copy-lexicon.yaml")      # 文件不存在时为空集


# ---------- 6. 审查目标 ----------

def change_dir(name: str) -> Path:
    """依次找 changes/<name>、archive/<name>、archive 下唯一的 YYYY-MM-DD-<name>（openspec 归档时加的日期前缀）。"""
    changes = root() / "openspec/changes"
    for d in (changes / name, changes / "archive" / name):
        if d.is_dir():
            return d
    pattern = re.compile(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(name)}")
    archive = changes / "archive"
    candidates = sorted(archive.iterdir()) if archive.is_dir() and "/" not in name else []
    dated = [d for d in candidates if d.is_dir() and pattern.fullmatch(d.name)]
    if len(dated) > 1:
        # 走到这里说明有多个同名归档，不替用户挑
        listed = "、".join(f"archive/{d.name}" for d in dated)
        sys.exit(fail(f"有多个归档的 change 匹配 {name}：{listed}，请写全目录名"))
    if not dated:
        sys.exit(fail(f"change 不存在：{changes / name}（也不在 archive/ 下）"))
    return dated[0]


def change_files(name: str) -> list[tuple[str, Target, str]]:
    """返回 (显示名, target, 文本) 列表。不存在的文件打印一行「跳过」，不报错也不计违规。"""
    d = change_dir(name)
    out: list[tuple[str, Target, str]] = []
    targets: tuple[Target, ...] = ("proposal", "design", "tasks")
    for target in targets:
        path = d / f"{target}.md"
        if path.exists():
            out.append((path.name, target, path.read_text(encoding="utf-8")))
        else:
            # 走到这里说明这份产物被省略了（小 change 常省 design）
            print(f"  跳过 {path.name}：不存在")
    for p in sorted(d.glob("specs/*/spec.md")):
        out.append((p.relative_to(d).as_posix(), "specs", p.read_text(encoding="utf-8")))   # Windows 上 str(Path) 是反斜杠
    return out


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    """嵌套 dict 拉平成 {"a.b.c": 文案}。"""
    out: dict[str, str] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def extract_i18n(html: str, lang: str) -> dict[str, str]:
    """从 HTML 内联脚本的 const I18N 里取某一语言块的 {key: 文案}。

    整个 I18N 对象字面量是合法 JSON5（裸键、双引号字符串、数组、尾逗号），整体交给 json5 解析，
    不用正则模拟 JS 词法；数组值是术语表，不审。解析失败带位置退出，不静默漏审。
    """
    start = html.index("{", html.index("const I18N ="))
    end = html.index("\n};", start) + 2
    try:
        i18n = json5.loads(html[start:end])
    except ValueError as e:
        sys.exit(fail(f"文案文件的 I18N 不是合法 JSON5，无法审查：{e}"))
    return {k: v for k, v in i18n[lang].items() if isinstance(v, str)}


def parse_copy(text: str, fmt: str, lang: str | None) -> dict[str, str]:
    """按 judge.yaml 配置的格式把文案文件内容解析成 {key: 文案}。"""
    if fmt == "json":
        return _flatten(json.loads(text))
    return extract_i18n(text, lang)


def changed_copy(file: str, fmt: str, lang: str | None) -> dict[str, str]:
    """文案相对 main 新增或修改的条目（参数取自 copy_config()）。main 上没有这个文件时，全部算新增。"""
    base = git(root(), "show", f"main:{file}")                # shared.git 按 UTF-8 读：Windows 中文版默认 GBK，读不出 UTF-8 中文
    old = parse_copy(base, fmt, lang) if base else {}
    new = parse_copy((root() / file).read_text(encoding="utf-8"), fmt, lang)
    return {k: v for k, v in new.items() if old.get(k) != v}


# ---------- 7. 跑 ----------

def report(results: list[Verdict], v: Verdict, qid: str, why: str) -> None:
    """打印一行结果并计入合计。"""
    print(f"  {v:6s} {qid:42s} {why}")
    results.append(v)


def ask_and_report(text: str, matched: list[Rule], judge: Judge, results: list[Verdict]) -> None:
    """把 text 交给裁判回答 matched 里的规则，逐条判定并报告。"""
    answers = judge.ask(text, matched)
    for r in matched:
        v, why = verdict_or_pending(r, answers)
        report(results, v, r.id, why)


def run_change(name: str, rules: list[Rule], judge: Judge | None) -> list[Verdict]:
    results: list[Verdict] = []
    for label, target, text in change_files(name):
        print(f"\n## {label}")

        # 1. design 先过 lint；命中就记 block，跳过这份文件的模型评估
        if target == "design":
            problems = lint_design(text)
            if problems:
                for p in problems:
                    report(results, "block", "lint/design", p)
                continue
            report(results, "pass", "lint/design", "决策否决理由、Risks 格式与回滚说明齐全")

        if judge is None:
            continue

        # 2. 问裁判
        matched = [r for r in rules if r.target == target]
        if not matched:
            print("  （无适用规则）")
            continue
        ask_and_report(text, matched, judge, results)
    return results


def run_direct(path: str, rules: list[Rule], judge: Judge | None) -> list[Verdict]:
    """审一份直接改动说明：四段齐全才问裁判，缺段直接记 block，不调模型。说明文件可以在项目之外。"""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:                # 文件不存在等 OSError 由命令行最外层接住；这里把编码错误也转成带路径的说明
        raise ConfigError(f"{path} 不是 UTF-8 编码：{exc}") from exc
    print(f"\n## {Path(path).name}")
    results: list[Verdict] = []
    problems = lint_direct(text)
    if problems:
        for p in problems:
            report(results, "block", "lint/direct", p)
        return results
    report(results, "pass", "lint/direct", "四段齐全")
    if judge is None:
        return results
    ask_and_report(text, [r for r in rules if r.target == "direct"], judge, results)
    return results


def run_copy(rules: list[Rule], judge: Judge | None) -> list[Verdict]:
    # 1. 取相对 main 的新增与修改
    file, fmt, lang = copy_config()
    entries = changed_copy(file, fmt, lang)
    if not entries:
        print("无待审文案")
        return []
    where = file if fmt == "json" else f"{file} I18N[{lang}]"
    print(f"\n## {where}（相对 main 新增或修改 {len(entries)} 条）")

    # 2. lint 与短标签先过，剩下的长文案才送模型
    known = lexicon()
    results: list[Verdict] = []
    pending: dict[str, str] = {}
    for key, text in entries.items():
        if why := lint_copy(text):
            report(results, "block", key, f"{why}：{text}")
        elif label_len(text) > SHORT_LABEL:
            pending[key] = text
        elif text in known:
            report(results, "pass", key, f"短标签，词表内：{text}")
        else:
            report(results, "review", key, f"短标签，未入词表：{text}")

    # 3. 长文案一条一请求，不打包：实测打包会把分数抬高最多 0.67、置信度压到 0.2
    if not pending or judge is None:
        return results
    rule = next((r for r in rules if r.target == "copy"), None)
    if rule is None:
        # 走到这里说明项目还没有可用作例句的文案，没启用文案打分（rules/copy-voice.md）
        for key, text in pending.items():
            report(results, "review", key, f"未启用文案打分规则：{text}")
        return results
    for key, text in pending.items():
        v, why = verdict_or_pending(rule, judge.ask(text, [rule]))
        report(results, v, key, f"{why}：{text}")
    return results


def judge_line(provider: str, dry_run: bool) -> str:
    """开头一行：用哪个裁判。人工模式不提模型；没有 key 时告诉用户怎么配。"""
    mode = "（dry-run，不发送）" if dry_run else ""
    if provider == "jev":
        return f"裁判：jev{mode}，模型 {JEV_MODEL}"
    if setting("JUDGE_PROVIDER") == "manual":
        return f"裁判：人工{mode}（已指定人工）"
    return f"裁判：人工{mode}（没有 key；运行 rulemason key 配置后自动用 Jev 判断）"


def print_template(name: str) -> int:
    """打印一份判断层模板；名称不认识时列出可选名称，返回 1。不需要在项目里运行。"""
    if name not in TEMPLATE_NAMES:
        print(fail(f"没有模板 {name!r}，可选：{'、'.join(TEMPLATE_NAMES)}"))
        return 1
    print((TEMPLATES / f"{name}.yaml").read_text(encoding="utf-8"), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="rulemason judge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--change", metavar="NAME", help="审 openspec/changes/NAME 下的产物")
    ap.add_argument("--copy", action="store_true", help="审 openspec/judge.yaml 配置的文案相对 main 的新增或修改")
    ap.add_argument("--direct", metavar="FILE", help="审一份直接改动说明（四段：要做什么、改哪些文件、主规格与检索命中、判路与理由），文件可以在项目之外")
    ap.add_argument("--lint-only", action="store_true", help="只跑正则检查，不需要 key 与网络")
    ap.add_argument("--dry-run", action="store_true", help="打印将要发送的请求体，不发送")
    ap.add_argument("--template", metavar="NAME", help=f"打印判断层模板（{'、'.join(TEMPLATE_NAMES)}），启用判断时用")
    args = ap.parse_args(argv)
    if args.template is not None:
        return print_template(args.template)
    if not (args.change or args.copy or args.direct):
        ap.error("请指定 --change NAME、--copy、--direct FILE 或 --template NAME")

    # 1. 规则与裁判；--lint-only 不需要裁判
    rules = load_rules()
    judge = None if args.lint_only else Judge(pick_provider(), dry_run=args.dry_run)
    if judge is not None:
        print(judge_line(judge.provider, args.dry_run))

    results: list[Verdict] = []
    if args.change:
        results += run_change(args.change, rules, judge)
    if args.copy:
        results += run_copy(rules, judge)
    if args.direct:
        results += run_direct(args.direct, rules, judge)
    if judge is not None:
        judge.close()

    # 2. 有 block 退出码非 0
    print(f"\n合计：pass {results.count('pass')} / review {results.count('review')} / block {results.count('block')}")
    return 1 if "block" in results else 0


def cli(argv: list[str] | None = None) -> None:
    """命令行入口 rulemason judge：argv 是 judge 之后的参数。"""
    from typesafe_sdk import TypeSafeAuthenticationError

    try:
        sys.exit(main(argv))
    except TypeSafeAuthenticationError:
        # 命令行最外层：key 被拒是配置问题，给一句能照做的说明，不打印堆栈
        sys.exit(fail(f"Jev 拒绝了 key（已作废或填错）：请检查 {USER_ENV} 或环境变量 TYPESAFE_API_KEY"))
    except ConfigError as exc:
        # 命令行最外层：项目配置写错，给出文件与位置，不打印堆栈
        sys.exit(fail(str(exc)))
    except OSError as exc:
        # 命令行最外层：文件读不了（权限、路径是目录等），网络或连接失败也可能走到这里；与 rulemason 其他命令一样给一句说明
        sys.exit(fail(f"rulemason judge 失败：{exc}"))
