"""模板与 skill 测试：init 用的包内模板、skill 正文与阶段三模板、共享 workflow-gates 与 OpenCode 审查子代理。"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import yaml

from rulemason import check, shared

ROOT = shared.SOURCE_ROOT
TEMPLATES = shared.TEMPLATES
SKILL = ROOT / "skills/rulemason"


def _frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    head, body = text.removeprefix("---\n").split("\n---\n", 1)
    return yaml.safe_load(head), body


def _effect(meta: dict, action: str, resource: str) -> str | None:
    """按 OpenCode 的 last-match 规则求值；这里静态模拟 Wildcard.match，不含运行时默认规则。"""
    effect = None
    for rule in meta["permissions"]:
        if fnmatch.fnmatchcase(action, rule["action"]) and fnmatch.fnmatchcase(resource, rule["resource"]):
            effect = rule["effect"]
    return effect


# ---------- 1. init 用的包内模板 ----------

def test_no_template_references_sibling_rulemason():
    for path in [*TEMPLATES.iterdir(), *SKILL.rglob("*")]:
        if path.is_file() and not path.name.startswith("."):      # 跳过 .DS_Store 等本机文件
            assert "../rulekit/" not in path.read_text(encoding="utf-8"), path


def test_skill_is_one_file_and_templates_ship_with_engine():
    assert sorted(p.name for p in SKILL.iterdir() if not p.name.startswith(".")) == ["SKILL.md"]
    engine_templates = ROOT / "src/rulemason/judge/templates"
    assert sorted(p.name for p in engine_templates.iterdir()) == ["judge.yaml", "judge_cases.yaml", "judgments.yaml"]


def test_agents_template_has_headings_blocks_and_pending_marks():
    text = (TEMPLATES / "AGENTS.md.tmpl").read_text(encoding="utf-8")

    for heading, name in (("Code style", "code-style"), ("Workflow gates", "workflow-gates")):
        assert f"## {heading}\n\n<!-- rulemason:{name} -->\n<!-- /rulemason:{name} -->" in text
    assert "## 红线（不可违反）" in text and "待 /rulemason 补充" in text
    assert "每个文件第一行用一句话写它是干什么的" not in text            # 不展开共享正文


def test_blocks_reference_generated_copies():
    code_style = (TEMPLATES / "code-style.block.md").read_text(encoding="utf-8")
    gates = (TEMPLATES / "workflow-gates.block.md").read_text(encoding="utf-8")

    assert ".rulemason/rules/code-style.md" in code_style and ".rulemason/rules/python.md" in code_style
    assert ".rulemason/rules/workflow-gates.md" in gates


def test_claude_block_imports_rules_and_maps_simplify_step():
    claude = (TEMPLATES / "claude.block.md").read_text(encoding="utf-8")
    imports, mapping = claude.split("\n\n", 1)

    assert imports.splitlines() == ["@AGENTS.md", "@.rulemason/rules/code-style.md", "@.rulemason/rules/python.md", "@.rulemason/rules/react.md", "@.rulemason/rules/workflow-gates.md"]
    assert "/simplify" in mapping and "代码逻辑" in mapping and "行为保持" in mapping
    assert ".rulemason/rules/workflow-gates.md" in mapping           # 不可用时的退路指向项目内副本
    assert "rules/python.md" not in mapping and "rules/react.md" not in mapping   # 没有该语言的项目会删掉含这些路径的行
    # 本仓库的 CLAUDE.md 手写：模板按本仓库的语言（有 Python、没有 React）过滤，直接引用 rules/
    own = check.for_languages(claude, ROOT, shared.list_files(ROOT))
    assert (ROOT / "CLAUDE.md").read_text(encoding="utf-8") == own.replace(".rulemason/", "")
    # 其余模板（其他工具的入口、共用标记块）都不出现 /simplify；共享正文的同类检查在 test_workflow_gate_uses_automatic_review_not_simplify
    for path in TEMPLATES.iterdir():
        if path.name != "claude.block.md" and not path.name.startswith("."):      # 跳过 .DS_Store 等本机文件
            assert "/simplify" not in path.read_text(encoding="utf-8"), path.name


def test_opencode_and_ruff_templates_point_to_copies():
    opencode = json.loads((TEMPLATES / "opencode.jsonc.tmpl").read_text(encoding="utf-8"))
    ruff = (TEMPLATES / "ruff.toml.tmpl").read_text(encoding="utf-8")

    assert opencode["instructions"] == [".rulemason/rules/code-style.md", ".rulemason/rules/python.md", ".rulemason/rules/react.md", ".rulemason/rules/workflow-gates.md"]
    assert 'extend = ".rulemason/lint/ruff-base.toml"' in ruff and "select" not in ruff


def test_workflow_spec_template_is_project_specific_and_references_copy():
    text = (TEMPLATES / "workflow-gates-spec.md.tmpl").read_text(encoding="utf-8")

    assert text.startswith("# workflow-gates Specification")
    assert "## Purpose" in text
    assert "### Requirement: Apply 后自动精简并审查" in text
    assert ".rulemason/rules/workflow-gates.md" in text
    assert "MUST NOT 复制共享检查点正文" in text
    assert "## 自动精简与代码审查（apply 后）" not in text


# ---------- 2. skill 正文 ----------

def test_skill_reads_check_json_and_lists_every_code():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "运行 `rulemason check --json`" in skill and "`next.code`" in skill and "`text`" in skill
    table = skill[skill.index("## 1. 识别"):skill.index("## 2. 补项目信息")]
    for code in ("fix_manifest", "init", "fix_gitignore", "update", "fill_project_info", "upgrade_machine", "upgrade_copies", "none"):
        assert f"`{code}`" in table, code
    assert "rulemason init --plan" in skill and "rulemason --version" in skill
    assert "uv tool install rulemason" in skill and "github.com" not in skill
    assert "check.py" not in skill and "configure.py" not in skill


def test_skill_stage_order_and_guards():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    order = [skill.index(title) for title in ("## 2. 补项目信息", "## 3. 日常巡检", "## 4. 启用判断（可选", "## 5. 汇报")]
    assert order == sorted(order)
    assert "不改 rulemason 标记块" in skill
    assert "项目没有 git 时，说明判断层需要 git" in skill
    assert "去掉「自动识别，请确认」" in skill
    assert "MUST NOT 复制共享检查点正文" in skill and "语义等价的 requirement" in skill
    assert "只读，不改文件" in skill and "不代填 key" in skill
    assert "rulemason judge --template judgments" in skill and "rulemason key" in skill
    assert "templates/judgments.yaml" not in skill                       # 模板不再随 skill 复制


# ---------- 3. 共享 workflow-gates 与审查子代理 ----------

def test_workflow_gate_uses_automatic_review_not_simplify():
    text = (ROOT / "rules/workflow-gates.md").read_text(encoding="utf-8")

    assert "自动代码审查" in text
    assert "自动精简与代码审查" in text
    assert "行为保持的自动精简" in text
    assert "先对本次 diff 执行行为保持的自动精简，再执行独立代码审查" in text
    assert "只处理本次变更中的重复、死代码、冗余抽象或过复杂逻辑" in text
    assert "必须保持需求、外部可观察行为与 API 不变" in text
    assert "不得为减少行数重写无关代码" in text
    assert "MUST" not in text                                            # 规矩正文用中文的「必须 / 不得」
    # 接入项目的 operations 提示与 rulemason remove 按原文引用这个小节标题
    assert "\n## apply 最后一个任务做完、汇报完成之前\n" in text
    assert "/simplify" not in text
    assert "简化检查" not in text
    assert "不等待人工逐条审核" in text
    phrases = (
        "独立于实现者",
        "所有工具权限均拒绝的审查子代理",
        "单独复审轮次",
        "只分析实现者提供的材料",
        "不读仓库其他文件、不运行命令",
        "最多两轮",
        "第二轮后仍有 block",
        "不再审第三轮",
        "verification.md",
        "估计行数",
        "判断回归",
        "停止实现",
        "block",
        "review",
        "pass",
        "自动修复",
        "新增行为有覆盖",
        "改变方案、规格或扩大范围",
        "不把逐条代码审核转交用户",
    )
    for phrase in phrases:
        assert phrase in text
    no_judge_steps = text.split("\n## 没有判断层的项目\n", 1)[1].split("\n## ", 1)[0]
    assert "自动精简" in no_judge_steps
    assert "自动代码审查" in no_judge_steps
    assert "文案检查依赖 Jev" in no_judge_steps
    assert "并跳过" in no_judge_steps


def test_opencode_reviewer_is_read_only_and_uses_max_variant():
    meta, body = _frontmatter(ROOT / ".opencode/agents/code-reviewer.md")

    assert meta["mode"] == "subagent"
    assert meta["model"] == "opencode-go/deepseek-v4.1-flash#max"
    assert "只读代码审查者" in body
    assert "没有任何工具权限" in body
    assert "本次 diff" in body
    assert "只凭任务消息提供的内容审查" in body
    assert "不调用任何工具" in body


def test_opencode_reviewer_permissions_deny_writes_shell_and_secrets():
    meta, _ = _frontmatter(ROOT / ".opencode/agents/code-reviewer.md")

    assert meta["permissions"] == [{"action": "*", "resource": "*", "effect": "deny"}]
    denied_actions = (
        ("edit", "rules/workflow-gates.md"),
        ("shell", "git diff --output=/tmp/review.diff"),
        ("bash", "git diff --output=/tmp/review.diff"),
        ("read", "rules/workflow-gates.md"),
        ("webfetch", "https://example.com"),
        ("websearch", "search"),
        ("question", "需要人工确认吗"),
        ("subagent", "*"),
        ("task", "*"),
        ("execute", "*"),
        ("skill", "*"),
        ("glob", "*"),
        ("grep", "*"),
        ("list", "*"),
        ("external_directory", "*"),
    )
    for action, resource in denied_actions:
        assert _effect(meta, action, resource) == "deny"

    secrets = (
        ".env", "app/.env", ".env.local", "app/.env.local", "prod.env", "secrets.env", ".envrc",
        "server.key", "certs/server.key", "id_rsa", "id_ed25519", "~/.ssh/id_rsa", ".npmrc", "app/.npmrc",
        ".netrc", ".pypirc", ".git/config", "nested/.git/config", "~/.config/jev-judge/env", "~/.config/rulemason/env",
        "~/.aws/credentials", "~/.docker/config.json", "~/.kube/config", "~/.config/opencode/auth.json",
        "~/.config/gh/hosts.yml", "~/.azure/token.json", "~/.config/gcloud/credentials.db",
        "credentials.json", "service-account-prod.json", "cert.p12", "cert.jks", "cert.keystore",
        ".git-credentials", "server.pem",
    )
    for secret in secrets:
        assert _effect(meta, "read", secret) == "deny"

    for example in (".env.example", "app/.env.example", ".env.sample", ".env.template"):
        assert _effect(meta, "read", example) == "deny"


# ---------- 4. 旧名不留遗漏 ----------

OLD_NAMES = ("rulekit", "jev-judge", "jev_judge")
OLD_KEY_PATH = ".config/jev-judge"                              # 唯一允许出现旧名的地方：judge 读旧 key 位置的兜底
TEXT_SUFFIXES = (".md", ".mjs", ".py", ".tmpl", ".toml", ".yaml")


def test_no_old_names_outside_judge_key_fallback():
    leftovers = []
    for top in ("src", "skills", "rules", "lint", "openspec-base"):
        for path in sorted((ROOT / top).rglob("*")):
            if path.suffix not in TEXT_SUFFIXES or "__pycache__" in path.parts:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if any(name in line.replace(OLD_KEY_PATH, "") for name in OLD_NAMES):
                    leftovers.append(f"{path.relative_to(ROOT).as_posix()}:{n}")
    assert leftovers == []


def test_skill_handles_check_failure():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "命令以非 0 退出且输出不是 JSON 时" in skill and "原样转述这条提示" in skill


def test_react_rules_are_shared_and_project_neutral():
    text = (ROOT / "rules/react.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- ") and "**React / TSX：**" in text
    for word in ("Next", "next-intl", "notFound", "gallery", "src/lib"):     # 项目名由 pre-commit 按本机私有词表拦截
        assert word not in text, word
    assert "react-hooks/exhaustive-deps" in text and "eslint-disable" in text


def test_rules_wording_key_sections():
    code_style = (ROOT / "rules/code-style.md").read_text(encoding="utf-8")
    assert "\n## 九条之外\n" in code_style and "不提交密钥、凭证与本机绝对路径" in code_style
    assert [line[:2] for line in code_style.splitlines() if line[:1].isdigit()] == [f"{n}." for n in range(1, 10)]
    gates = (ROOT / "rules/workflow-gates.md").read_text(encoding="utf-8")
    assert "只能读一份文件的子代理" in gates and "命令表没有这一行时跳过" in gates
    assert "\n## 提交信息\n" in gates and "类型(范围): 中文说明（change 名）" in gates
    python = (ROOT / "rules/python.md").read_text(encoding="utf-8")
    assert "logging" in python and "encoding=\"utf-8\"" in python
    for path in ROOT.glob("rules/*.md"):
        assert "不把正文抄进项目指令，不手改副本" in path.read_text(encoding="utf-8").splitlines()[0], path.name


def test_copy_voice_levels_unchanged():
    """项目判断规则照抄这三行，改一个字各项目就对不上。"""
    text = (ROOT / "rules/copy-voice.md").read_text(encoding="utf-8")
    levels = [line for line in text.splitlines() if line.startswith(("- 0 档", "- 1 档", "- 2 档"))]
    assert levels == [
        "- 0 档：模板：英文报错、占位符、翻译腔、框架自带没改过的文案，读者需要猜它在说什么",
        "- 1 档：生硬或做作：意思对，但有开发术语、公文腔、省略成分、标签式缩略；或者反过来文气、做作、堆修辞，不像平时说话",
        "- 2 档：自然：用词日常，直接说清楚发生了什么或要用户做什么，一遍读懂；正常的中文状态短句（加载中、提交失败请稍后再试）也算这一档；可以有本站固定用语，但不为了文气加字",
    ]


def test_artifact_base_limits():
    base = yaml.safe_load((ROOT / "openspec-base/artifact-rules.yaml").read_text(encoding="utf-8"))["rules"]
    assert any("60 行以内" in item for item in base["proposal"])
    assert any("500 个字符" in item for item in base["specs"])
