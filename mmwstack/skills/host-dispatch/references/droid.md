# Factory Droid dispatch

Read `## droid` in `~/.agents/mmwstack-models.md` (or the supplied model rule file) before spawning.

| Role | Dispatch target | Notes |
| --- | --- | --- |
| `mmw-agent` (playbook delegates) | `subagent_type` set to `mmw-agent-<tier>` (`light`, `medium`, or `heavy`) | Take `<tier>` from the step's entry in `## droid`. |
| `advisor` and `comment-sicko` | Native `advisor` or `comment-sicko` in `.factory/droids/` | Bound to its tier in `.factory/droids/`. `comment-sicko` runs read-only. |
| General-purpose delegates (readers, reviewers, runners, judges) | Built-in `worker` when writes are needed, or `explorer` for read-only work | Pass the role or seat tier as `Task.complexity`. Report a seat unavailable if neither built-in honors both tools and tier. |

Sync `.factory/droids/` before launch whenever a Factory tier binding changes or a model rule changes the `advisor` or `judgment and prose` tier.
