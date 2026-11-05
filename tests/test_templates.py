"""模板与 skill 测试：init 用的包内模板、skill 正文与阶段三模板、共享 workflow-gates 与 OpenCode 审查子代理。"""
from __future__ import annotations

import fnmatch
import json
import re
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
    assert 'extend = "$extend"' in ruff and "select" not in ruff


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
    for code in ("fix_manifest", "init", "fix_gitignore", "update", "fill_project_info", "upgrade_machine", "manual_lint", "none"):
        assert f"`{code}`" in table, code
    assert "rulemason init --plan" in skill and "rulemason --version" in skill
    assert "uv tool install rulemason" in skill and "github.com" not in skill
    assert "check.py" not in skill and "configure.py" not in skill


def test_skill_stage_order_and_guards():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    order = [skill.index(title) for title in ("## 2. 补项目信息", "## 3. 日常巡检", "## 4. 启用判断（可选", "## 5. 建立 ruff 基线", "## 6. 建立 ESLint 基线", "## 7. 汇报")]
    assert order == sorted(order)
    assert "不改 rulemason 标记块" in skill
    assert "项目没有 git 时，说明判断层需要 git" in skill
    assert "去掉「自动识别，请确认」" in skill
    assert "MUST NOT 复制共享检查点正文" in skill and "语义等价的 requirement" in skill
    assert "只读，不改文件（例外见「不可违反」）" in skill and "唯一的例外是用户确认的 ruff 基线计划" in skill and "不代填 key" in skill
    assert "rulemason judge --template judgments" in skill and "rulemason key" in skill
    assert "templates/judgments.yaml" not in skill                       # 模板不再随 skill 复制


def test_skill_ruff_baseline_section():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    section = skill[skill.index("## 5. 建立 ruff 基线"):skill.index("## 6. 建立 ESLint 基线")]

    assert "转到「5. 建立 ruff 基线」" in skill
    for text in ("--select I001,F401 --extend-exclude __init__.py --force-exclude --fix", "extend-immutable-calls", '"scripts/**" = ["T201"]',
                 "# 接入前遗留，改到该文件时清掉", "用户确认后才运行", "ruff 通过，无需建立基线"):
        assert text in section, text
    for name in ("fastapi.Depends", "fastapi.Query", "fastapi.Security", "typer.Option", "typer.Argument"):
        assert f'"{name}"' in section, name
    assert "不加 `--unsafe-fixes`" in section and "不用 `# noqa`" in section and "`--diff`" in section
    assert "「判断用的红线规则」一行（旧写法「红线规则：…」一行同理）改为列出用户确认的规则 id" in skill


def test_skill_eslint_baseline_section():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    section = skill[skill.index("## 6. 建立 ESLint 基线"):skill.index("## 7. 汇报")]

    assert "转到「6. 建立 ESLint 基线」" in skill
    for step in ("**统计**", "**列给用户确认**", "**确认后照做**"):            # 与 ruff 基线同样的步骤
        assert step in section, step
    for text in ("--format json", "// 接入前遗留，改到该文件时清掉", "不提高全局复杂度上限", "不整条关规则",
                 "`--rule` 会盖过配置里按文件写的豁免", "**旧口径的全局放宽**", "基础规则没有报错，无需建立 ESLint 基线", "参数前加 `--`"):
        assert text in section, text


def test_skill_common_red_line_candidates():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    step = skill[skill.index("2. **红线候选**"):skill.index("3. **样板与豁免**")]

    for trigger in ("有数据库访问", "有部署脚本或 CI 发布流程", "有区分生产环境的配置"):
        assert trigger in step, trigger
    for candidate in ("「线上数据库只读，迁移与改数据由人执行」", "「不代为发布到生产，发布由人触发」", "「生产凭据只给人用，AI 会话不使用生产写权限」"):
        assert candidate in step, candidate
    for text in ("「rulemason 常见红线（触发文件）」", "没有对应的东西就不提", "逐条请用户确认", "`.env.production`"):
        assert text in step, text
    assert "或「rulemason 常见红线」及触发它的文件" in skill


def test_skill_treats_fill_plan_as_part_of_the_upgrade():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for text in ("在终端里运行会询问是否补齐，由用户答 y；非交互环境（包括你代为运行）才加 `--yes`",
                 "补齐计划写进项目文件的内容", "不是项目自己加的规则", "升级产出，提交时与副本一起带上", "本 skill 不提交",
                 "补齐写进项目文件的内容属于这次升级，提交时与副本一起带上", "*_shared/openspec-base/*.yaml", "以 `rulemason update --dry-run` 列出的补齐计划为准",
                 "只查基础条目有没有缺，不能用来认定新增条目是基础版"):
        assert text in skill, text


# ---------- 3. 共享 workflow-gates 与审查子代理 ----------

def test_workflow_gates_fix_only_problems_this_change_introduced():
    text = (ROOT / "rules/workflow-gates.md").read_text(encoding="utf-8")

    assert "「红线规则」指命令表之后列出、供判断使用的实质类规则" in text
    assert "直到通过" not in text
    assert text.count("建议运行 `/rulemason` 建立基线") == 2
    assert "修掉本次改动引入的问题" in text and "改动前就有的问题不修" in text


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
    assert "\n## 提交与推送\n" in gates and "类型(范围): 中文说明（change 名）" in gates
    commit = _section(gates, "提交与推送")
    assert "commitlint" in commit and "不用 amend" in commit and "推送前单独列出" in commit
    assert "--only" not in commit and "--pathspec-from-file" not in commit       # 共享正文只写原则，不写具体选项
    tests = _section(gates, "改既有测试时")
    assert "不删除、不放宽" in tests and gates.count("按「改既有测试时」一节处理") == 2
    assert "只带本次计划内的文件" in commit and "git worktree" in commit
    front = next(line for line in gates.splitlines() if line.startswith("4. 改了前端时"))
    assert "修掉本次改动引入的问题" in front and "建立 ESLint 基线" in front      # 与 ruff 一步对称，不要求修既有问题
    python = (ROOT / "rules/python.md").read_text(encoding="utf-8")
    assert "logging" in python and "encoding=\"utf-8\"" in python
    for path in ROOT.glob("rules/*.md"):
        assert "不把正文抄进项目指令，不手改副本" in path.read_text(encoding="utf-8").splitlines()[0], path.name


def test_code_style_external_operations_and_secrets():
    code_style = (ROOT / "rules/code-style.md").read_text(encoding="utf-8")
    section = code_style[code_style.index("\n## 外部操作与凭据\n"):]

    assert code_style.index("\n## 九条之外\n") < code_style.index("\n## 外部操作与凭据\n")
    assert len(section.strip().splitlines()) <= 15
    for text in ("项目指令对某类操作另有写明的从项目指令", "有写权限不等于可以写",
                 "**读**（不含密钥值与个人数据）：直接做",
                 "**写**", "发布、发送消息、推送 tag", "等用户同意", "同意只管这一次",
                 "**删除或作废**", "强推覆盖共享分支", "说不清会不会销毁的也算", "不执行，给出操作入口"):
        assert text in section, text
    for text in ("不让用户把密钥值贴进对话", "确认不会被提交", "只引用变量名", "不把密钥值打印到命令输出", "只检查是否存在",
                 "按泄露处理", "一个用途一把", "预发与生产分开"):
        assert text in section, text
    eighth = next(line for line in code_style.splitlines() if line.startswith("8. "))
    assert "静默改走另一条路径" in eighth


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
    assert "Context 里的关键事实注明出处（文件与行，或可复现的命令），没有核实的标「未核实」" in base["design"]


def test_eslint_wording_per_file_and_react_equivalence():
    base = (ROOT / "lint/eslint-base.mjs").read_text(encoding="utf-8")
    assert "最复杂函数" not in base and "按文件追加条目" in base and "不提高全局上限" in base   # 旧口径教人全局取最大值
    react = (ROOT / "rules/react.md").read_text(encoding="utf-8")
    start = react.index("重构等价性")
    section = react[start:react.index("机械部分", start)]
    assert section.count("\n- ") == 6 and "`Map`" in section and "`useState(() => …)`" in section
    for name in ("antd", "Ant Design", "Space", "MUI", "Chakra"):          # 共享正文不写 UI 库名
        assert name not in section, name



# ---------- 不走 OpenSpec 的改动与归档（spec-guard） ----------

def _section(text: str, heading: str) -> str:
    start = text.index(f"## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def test_gates_cover_direct_edits_with_four_paths():
    text = (ROOT / "rules/workflow-gates.md").read_text(encoding="utf-8")
    assert "包住每一次改代码" in text
    direct = _section(text, "不走 OpenSpec 改代码时")
    for path in ("**改契约**", "**冲突**", "**未覆盖**", "**不改行为**"):
        assert path in direct, path
    assert "停下等用户确认" in direct and "不写 design" in direct and "不补写规格" in direct
    assert "用户要的就是改变主规格" in direct and "选改规格就按「改契约」走" in direct
    assert "openspec list --specs" in direct and "--no-scenarios" in direct
    assert "在 `openspec/specs/` 里检索" in direct and "命中主规格点名的测试按「冲突」处理" in direct
    assert "不跑自动精简与独立审查" in direct and "只做第 4 步" in direct


def test_gates_archive_merges_without_asking_and_hints_key_once():
    archive = _section((ROOT / "rules/workflow-gates.md").read_text(encoding="utf-8"), "归档")
    assert "`openspec archive <change 名> --yes`" in archive and "`openspec validate --specs --strict`" in archive
    assert "不就「是否同步主规格」询问用户" in archive and "verification.md" in archive
    assert "正好是 3" in archive and "rulemason key" in archive and "不代用户配置 key" in archive


def test_entry_blocks_say_read_before_direct_edits():
    gates = (TEMPLATES / "workflow-gates.block.md").read_text(encoding="utf-8")
    no_openspec = (TEMPLATES / "workflow-gates-no-openspec.block.md").read_text(encoding="utf-8")
    assert "不走 OpenSpec 改代码之前" in gates and "归档" in gates
    assert "ruff 与测试" in no_openspec and "改代码前读取该文件" in no_openspec


# ---------- 英文简版 README（docs-en） ----------

README_EN_URL = "https://github.com/rulemason/rulemason/blob/main/README.en.md"


def readme_commands(text: str, heading: str) -> list[str]:
    """README 命令表（heading 到下一个二级标题之间）里反引号中的命令；占位参数（「功能名」「<change-name>」）去掉，只留前面的部分。"""
    table = text[text.index(f"## {heading}\n"):]
    table = table[:table.index("\n## ", 1)]
    commands = re.findall(r"`([^`]+)`", table)
    return [re.split(r"\s+(?:[一-鿿]|<)", cmd)[0] for cmd in commands]


def test_english_readme_lists_every_common_command():
    zh = readme_commands((ROOT / "README.md").read_text(encoding="utf-8"), "常用命令")
    en = readme_commands((ROOT / "README.en.md").read_text(encoding="utf-8"), "Common commands")
    assert "rulemason init" in zh and "/rulemason" in zh and "rulemason judge --change" in zh
    missing = [cmd for cmd in zh if cmd not in en]                    # 比的是两张命令表，正文和网址里出现过不算
    extra = [cmd for cmd in en if cmd not in zh]                      # 中文删了命令、英文忘了删
    assert missing == [] and extra == [], f"README.en.md 的命令表缺少：{missing}，多出：{extra}"


def test_readme_links_use_full_urls_and_english_says_ui_is_chinese():
    zh = (ROOT / "README.md").read_text(encoding="utf-8")
    en = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert f"[English]({README_EN_URL})" in zh.split("\n## ", 1)[0]
    head = en.split("\n## ", 1)[0]
    assert "written in Chinese" in head and "(https://github.com/rulemason/rulemason/blob/main/README.md)" in head
