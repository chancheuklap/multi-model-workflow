# Host subagent dispatch

Single reference for host-specific subagent dispatch mechanics. Every playbook and skill reads the current host's section in `~/.agents/mmwstack-models.md` (or the supplied rule file) and dispatches through that host's row below.

## Dispatch table

| Host | `mmw-agent` (playbook delegates) | `advisor` & `comment-sicko` | Generic runners / judges (`arena`, `eval`, `reader`) | Notes |
| --- | --- | --- | --- | --- |
| **Codex / Claude Code / Cursor** | Spawn native `mmw-agent` with the step's model and settings. | Spawn native `advisor` or `comment-sicko` with its configured model and settings. | Spawn a fresh subagent with the seat's model and settings. | Native role registration lives in `.codex/agents/`, `.claude/agents/`, or `.cursor/agents/`. |
| **Factory Droid** | Set `subagent_type` to `mmw-agent-<tier>`, replacing `<tier>` with the tier (`light`, `medium`, or `heavy`) from the step's entry in `## droid`. | Spawn native `advisor` or `comment-sicko` (bound to its tier in `.factory/droids/`). `comment-sicko` runs read-only. | Choose built-in `worker` (needs writes) or `explorer` (read-only, including cross-judge) and pass the seat's tier as `Task.complexity`. Report a seat unavailable if neither built-in can honor both tools and tier. | Sync `.factory/droids/` before launch after any tier or specialist binding changes. |
| **Antigravity (AGY)** | Run `~/.agents/scripts/agy-delegate --agent mmw-agent --model-role "<role>"` (or `--model <id>`) in local sessions. | Run `~/.agents/scripts/agy-delegate --agent advisor --model-role advisor` or `--agent comment-sicko --model-role "judgment and prose"`. | Run `~/.agents/scripts/agy-delegate --agent none --model-role "<panel>" --seat <n>` (or `--model <id>`). Pass `--agent none` for blinded `eval` candidates so no mmwstack role prompt leaks. | Resume only when required via `--resume <conversation_id>`. Sync `.agents/agents/` after role changes. |

## Antigravity (AGY) rules

- **Why `scripts/agy-delegate`:** AGY's built-in `invoke_subagent` and `.agents/agents/*.md` frontmatter accept only four coarse model tiers (`inherit`, `pro`, `flash`, `flash_lite`) and reject exact model IDs. Running `agy --agent <role> --model <id> --output-format json -p` through `scripts/agy-delegate` enforces custom role instructions and `tools:` allowlists while selecting any exact model and reasoning level in `agy models` (`## agy`), with isolated conversations and Home Repo hooks intact.
- **Do not use `swarm` for mmwstack delegations:** `swarm` shares a public message board across members, which breaks `arena` and `eval` blind isolation and conflicts with mmwstack's role and review contracts.
- **Parallelism:** launch independent `scripts/agy-delegate` calls as concurrent background shell tasks; wait for completion notifications rather than polling.
- **Fallback without `agy` CLI:** if `agy` is unavailable in the current environment (for example, a cloud sandbox without the CLI), fall back to `invoke_subagent` using the closest tier (`pro`, `flash`, `flash_lite`, or `inherit`) and record the fallback in the report.
- **Managed repository isolation:** when the session starts in a shared Home Repo checkout, never pass AGY `Workspace: "branch"` or `"share"` to isolate work in another repository—that clones or shares the Home Repo itself. Isolate each concurrent writer in a sibling worktree of the target repository and pass that worktree's absolute path in the brief.
