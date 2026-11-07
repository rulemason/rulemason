# rulemason

[中文](https://github.com/rulemason/rulemason/blob/main/README.md) · English

Shared rules and checkpoints for AI coding tools (Claude Code, OpenCode, Cursor, Codex).

> **Language note:** the command-line output, the generated rules, and the AI skill are written in Chinese. This page is a short English overview; the [Chinese README](https://github.com/rulemason/rulemason/blob/main/README.md) is the full documentation. rulemason works best for teams who read Chinese, or who are happy to read the rules through a translator.

## What it does

- **Rules**: the conventions an AI must follow when it writes plans and code — nine general principles, per-language guides (Python, React), a copy-voice guide for UI text, plan-writing rules, and how to handle external platforms and secrets (reads go ahead, writes need approval each time, deletions are left to a person; secrets never pass through the chat). They are maintained once in this repository, and each project gets a read-only copy that is committed with the project, so teammates, cloud agents and CI can read them without installing rulemason.
- **Checkpoints**: after a plan is written, before code is written, and after code is written, the AI checks its own work automatically — judging the plan, simplifying the code, running an independent review, lint and tests. Small changes made without OpenSpec are checked against the project's main specs first: only a change to a behavior the specs already promise starts a minimal OpenSpec change and asks you once; everything else is edited directly and then linted and tested. Archiving merges spec changes without asking.
- **Judgment** (optional): the Jev model from TypeSafe judges whether a plan breaks a written rule and returns pass / review / block. Without a key, the rules are checked by hand.

Checkpoints that involve plans and specs need [OpenSpec](https://github.com/Fission-AI/OpenSpec); without it, rulemason installs the rules and lint configuration only.

## Install

Requires [uv](https://docs.astral.sh/uv/):

```bash
uv tool install rulemason
rulemason --version
```

## Common commands

| When | Command |
|---|---|
| First time in a project, or to add or remove AI tools | `rulemason init` |
| Any time later: upgrade, fill in missing configuration, restore edited copies | `rulemason update` |
| See the current state and the next step (also for CI) | `rulemason check` |
| Configure the Jev key once per machine (only for judgment) | `rulemason key` |
| Stop using rulemason in a project | `rulemason remove` |
| Judge one plan by hand | `rulemason judge --change <change-name>` |
| Inside your AI tool: fill in the project summary, red lines and command table, or enable judgment | `/rulemason` |
| Diagnose the whole repository, or clean up one module of existing code | `/rulemason cleanup` |

Run `rulemason init` in the directory you want to set up, the same way OpenSpec's own init works; in a monorepo, run it at the repository root, or run `rulemason init <repo-root>`, to cover the whole repository.

`rulemason check` exits non-zero when the setup is incomplete, so it can run in CI as is. When a lint setting cannot be fixed for you, the report names the file and line, quotes it, and says what to change. It also reports, without failing: main specs whose wording OpenSpec cannot read cleanly (placeholder purposes, delta-style headings, overlong requirements), lint scripts that are only placeholders (an echo or an empty script), and archived changes since the project was set up that lack a verification record.

In a project with a lot of existing code, ruff and ESLint often report many problems that were there before rulemason. Run `/rulemason` in your AI tool once to set up a baseline (with your confirmation): ruff gets per-file exemptions, and ESLint gets one entry per file with only the rules that file breaks and its own complexity cap — the global cap stays at 15 and no rule is switched off. After that, the checkpoints fix only the problems each change introduces. To clear what remains, run `/rulemason cleanup`. With no module name it only diagnoses the repository (baseline entries, a temporary soft-metric count, and a few files per module for how much they could shrink) and changes nothing. Before the last line it lists the modules still to do; the last line is the next cleanup command, or the paths to commit first. After one module is finished, the wrap-up names the next one and does not start editing it. With a module name it cleans just that module: it lists the plan first, and you can accept only some of it. Progress is not stored in a file. It is the baseline entries plus your own commits titled refactor(cleanup): <module>.

## Several projects in one folder

If one folder only holds several projects (say `products/` with `app/` and `api/`, each its own git repository), set up each project separately and leave the folder alone; `init` and `check` print a hint when run in such a folder. To change several projects in one session, open your AI tool in the main project and attach the others (for example `--add-dir`); the checkpoints then run once per project, each with its own command table. Claude Code does not read an attached directory's `CLAUDE.md` unless `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` is set.

## Upgrade

```bash
uv tool upgrade rulemason   # upgrade the rulemason program on this machine: once per machine
rulemason update            # refresh the copies committed in the project: once per project, commit the result
```

These are two steps because one machine may hold several projects, and the copies belong in each project's repository. One person runs `rulemason update` and commits; everyone else pulls and only upgrades their own machine. To do both at once: `uv tool upgrade rulemason && rulemason update`.

## License

Apache-2.0
