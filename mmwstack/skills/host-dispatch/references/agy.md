# Antigravity (AGY) dispatch

Dispatch local delegates through `~/.agents/scripts/agy-delegate --role <role>` on the `1.00x` default agent.

```sh
~/.agents/scripts/agy-delegate --role coder --add-dir <worktree> <<'EOF'
<brief starting with worker.md>
EOF
~/.agents/scripts/agy-delegate --resume <conversation_id> <<'EOF'
<follow-up prompt>
EOF
~/.agents/scripts/agy-delegate close <terminal-or-conversation-id>   # or --all-mine | --force
```

Pass repeatable `--add-dir <worktree>` for managed repos, `--prompt-file <path>` for file briefs, `--prompt <text>` for one-liners, and `--issue <repo>#<N>` only for unbound runs (`--issue` auto-infers from worktree branch or prompt URL). Launch independent calls as concurrent background shell tasks without polling.

| `--role` | Prompt body | `## agy` model role | Lifecycle | `PreToolUse` hook policy |
| --- | --- | --- | --- | --- |
| `coder` | `mmw-agent` | `coder` | `session` | `mmw-agent` (repo gates) |
| `feature`, `refactoring`, `feature, refactoring`, `bug-fix`, `perf-issue`, `hillclimb` | `mmw-agent` | same as `--role` | `gated` | `mmw-agent` (repo gates) |
| `mmw-agent` | `mmw-agent` | none (parent or `--model`) | `gated` | `mmw-agent` (repo gates) |
| `advisor` | `advisor` | `advisor` | `gated` | `advisor` (denies writes, mutating shell/git/`gh`) |
| `comment-sicko` | `comment-sicko` | `judgment and prose` | `ephemeral` | `comment-sicko` (denies `write_file`; allows `edit_file`) |
| `verifier`, `code review` | `none` | same as `--role` | `ephemeral` | `none` |
| `reader`, `judgment and prose`, `arena runners`, `arena cross-judge pool` | `none` | same as `--role` | `ephemeral` | `none` |
| `none` | `none` | none | `ephemeral` | `none` |

## Rare overrides

- `--seat <n>` picks the 1-based seat from comma-separated panel entries (`arena runners`, `arena cross-judge pool`).
- `--lifecycle <auto|ephemeral|gated|session>` overrides the role default (`session` for multi-phase owners; `ephemeral` for one-shot `mmw-agent`).
- `--model <id>` or `--model-role <role>` overrides model selection (`inherit-parent`, `auto`, or an exact AGY ID with optional `--effort`).
- `--prompt-role <mmw-agent|advisor|comment-sicko|none>` overrides the injected `agents/*.md` prompt independently of model role.

## Hard 4x quota and isolation rules

- Never pass `--agent` to `agy`, never create or use `.agents/agents/` or `~/.gemini/config/agents/`, never install AGY plugin `agents/`, and never call `define_subagent`.
- Keep `--cwd` rooted in the Home Repo (never pass a managed repo or worktree), and use `scripts/agy-delegate` instead of `swarm` for isolated conversations.

## Cloud or no-CLI fallback

When `agy` is unavailable, call `invoke_subagent(TypeName="self")` (or `research` for read-only roles such as `advisor`, `reader`, or `verifier`), prepend `Read <Home Repo>/agents/<role>.md and follow it in full.` when the role has a file, use the closest tier (`pro`, `flash`, `flash_lite`, `inherit`), and record the fallback in your report.

Read [agy-lifecycle.md](agy-lifecycle.md) only when debugging failures, lock or `Stop` hook sweep behavior, live-terminal `--resume` reuse, or `--force` close.
