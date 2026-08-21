# Installing the skills

There are currently two canonical skills:

- [`skill/SKILL.md`](../skill/SKILL.md) — `multipath-reasoning`
- [`recursive-confidence-loop/SKILL.md`](../recursive-confidence-loop/SKILL.md) — `recursive-confidence-loop`

Do not fork divergent copies per host. Hosts that accept YAML-frontmatter `SKILL.md` should receive each skill tree unmodified. Only the per-host subsections differ; the rest of each process is host-neutral.

## Grok Build

User-level (all projects):

```bash
cp -a skill ~/.grok/skills/multipath-reasoning
cp -a recursive-confidence-loop ~/.grok/skills/recursive-confidence-loop
```

Then `/multipath-reasoning <task>` or `/skills multipath-reasoning`.

If the skill self-invokes rather than being explicitly requested, it must state N and the cost (15–25 path invocations at default settings) before spawning. There are no recorded task experiments.

Native independence: `spawn_subagent`. **Audit ownership:** the child writes `path-k.md`; the parent waits for a non-empty file. Generation paths therefore need write access (`read-write`, or omit `capability_mode` when a shell is required). Do not use `read-only` or `execute` for those children.

If `spawn_subagent` is unavailable, mark `independence: "reduced"` before G0. Cheap tasks may proceed; high-consequence tasks should tell the user and prefer a smaller N or stop.

## Claude Code

```bash
cp -a skill ~/.claude/skills/multipath-reasoning        # user-level
cp -a skill <repo>/.claude/skills/multipath-reasoning   # project-level
cp -a recursive-confidence-loop ~/.claude/skills/recursive-confidence-loop
```

Copy the tree **unmodified**. `when-to-use`, `argument-hint`, and `metadata` are Grok frontmatter keys that Claude Code ignores; leaving them in place keeps `scripts/validate_state.py` identical to this repository, so `--self-test` passes and no fix is stranded downstream. The skill registry is read at session start, so a new install registers on the next session.

Native independence: the `Agent` tool with `subagent_type: "general-purpose"` — a cold context per path, no sibling visibility. **Audit ownership:** the child writes `path-k.md`; the parent waits for a non-empty file and trusts the file over the child's report.

Two traps with no Grok equivalent:

- **Never `subagent_type: "fork"`.** A fork inherits the parent's entire conversation, which is the shared-ancestor correlation the method exists to prevent.
- **Never `subagent_type: "Explore"`** for generation paths — it has no write tool and cannot produce the audit file.

Nesting is **not** host-enforced: a `general-purpose` agent can spawn further agents, unlike Grok's depth-1 cap. The prohibition is prompt-only; record `host_guarantees.nesting: "prompt"`.

For software tasks, `isolation: "worktree"` gives each path its own git worktree and enforces the tree-fingerprint contract structurally. It does not carry uncommitted changes.

If only in-session branching is available, set `independence: "reduced"`.

**For `recursive-confidence-loop` the shape is different** — it is a chain, not a population.
Spawn iterations **one at a time, sequentially**: iteration N needs N−1's scores, so parallel
calls break it. `fork` is prohibited for the same reason as above and for one more — the
chain must carry forward only what the prompt declares (SOURCE, the fixed schema, the previous
answer and scores), and an inherited conversation smuggles in state the audit trail cannot
see. That is the equivalent of Codex's `fork_context: false`. Do **not** use
`isolation: "worktree"` for scoring iterations: they must not mutate the project, and a
worktree would mask an iteration that tried.

## Codex

Copy into Codex’s skill location (commonly `~/.codex/skills/` or the project `.codex/skills/` tree, depending on your Codex version).

```bash
cp -a skill ~/.codex/skills/multipath-reasoning
cp -a recursive-confidence-loop ~/.codex/skills/recursive-confidence-loop
```

Native independence: the host’s isolated child-agent primitive (`multi_agent_v1.spawn_agent` or current equivalent). **Audit ownership:** children return markdown; the **parent** writes `path-k.md`. Do not instruct Codex children to write audit files, and do not wait for them to create those files.

If only in-session branching exists, `independence: "reduced"`.

## Amazon Kiro

Copy into Kiro’s project or user skill/steering location if it loads `SKILL.md`. If Kiro has no skill loader, attach [`skill/SKILL.md`](../skill/SKILL.md) as standing instructions for hard tasks and still isolate paths as far as the host allows.

Kiro-specific directory names vary by version; do not invent a path. Prefer the host’s current skill docs.

## After install

```bash
python3 skill/scripts/validate_state.py --self-test
python3 skill/scripts/project_state_view.py --self-test
python3 recursive-confidence-loop/scripts/vector_stability.py --self-test
python3 recursive-confidence-loop/scripts/vector_stability.py path/to/state.json
```

These checks are **structural / install** checks. They do not prove either method works on a task.
