# hooks override

- Hooks are Codex plugin hooks. Do not restore old-host hook matchers, `if` expressions, old plugin root environment variables, or old state paths.
- Root `codex-orchestrate/hooks.json` is the Codex hook manifest. Files under `hooks/` are executable handlers only.
- Multi-agent lifecycle hooks use Codex `SubagentStart` and `SubagentStop` payloads. Do not depend on legacy dispatch tool names or legacy payload fields.
- Hook comments and examples must describe Codex payloads and commands directly, without old-host tool-name labels.
- `SubagentStart` payloads do not include the original `spawn_agent` message, so hooks must not validate `DISPATCH_ENVELOPE` by reading `.prompt`.
- Review and worker dispatch gates belong in explicit Coordinator scripts before `spawn_agent` / `send_input`; hook handlers are only for events whose Codex payload contains the required data.
- SessionStart is responsible for exposing the concrete `MMW_PLUGIN_ROOT` value used by Skill command examples; do not use old-host plugin root variables.
