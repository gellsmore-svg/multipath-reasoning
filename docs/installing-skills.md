# Installing the skill

There is **one** canonical skill: [`skill/SKILL.md`](../skill/SKILL.md) plus `references/`, `scripts/`, and `developer-guide.md`.

Do not fork four divergent copies. Hosts that accept YAML-frontmatter `SKILL.md` should receive this tree. Only the **host mechanism** section is Grok-native; other hosts substitute their isolated child-session API and keep the process.

## Grok Build

User-level (all projects):

```bash
cp -a skill ~/.grok/skills/multipath-reasoning
```

Then `/multipath-reasoning <task>` or `/skills multipath-reasoning`.

Grok also auto-invokes from `description` / `when-to-use` unless `disable-model-invocation` is set (it is not).

Native independence: `spawn_subagent`. Generation paths need write access for `path-k.md` (`read-write`, or omit `capability_mode` when a shell is required). Do not use `read-only` or `execute` for those children.

## Claude Code

Copy the same tree into the user or project skill directory Claude Code scans (commonly `~/.claude/skills/multipath-reasoning/` or `<repo>/.claude/skills/multipath-reasoning/`).

Use Claude’s isolated subagent / Task tool analogously: separate contexts, same SOURCE, no sibling answers. If only in-session branching is available, set `independence: reduced`.

## Codex

Copy into Codex’s skill location (commonly `~/.codex/skills/` or the project `.codex/skills/` tree, depending on your Codex version). Same substitution rule: strongest isolated child session.

## Amazon Kiro

Copy into Kiro’s project or user skill/steering location if it loads `SKILL.md`. If Kiro has no skill loader, attach [`skill/SKILL.md`](../skill/SKILL.md) as standing instructions for hard tasks and still isolate paths as far as the host allows.

Kiro-specific directory names vary by version; do not invent a path. Prefer the host’s current skill docs.

## After install

```bash
python3 skill/scripts/validate_state.py --self-test
python3 skill/scripts/project_state_view.py --self-test
```

Both checks are **structural / install** checks. They do not prove the method works on a task.
