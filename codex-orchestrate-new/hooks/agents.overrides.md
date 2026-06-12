# hooks override

- Hooks are Codex plugin hooks. Do not restore old-host hook matchers, old plugin root environment variables, or old state paths.
- Root `codex-orchestrate-new/hooks.json` is the Codex hook manifest and must be referenced by `.codex-plugin/plugin.json` through `"hooks": "./hooks.json"`. Files under `hooks/` are executable handlers only.
- Plugin hook commands must use `${PLUGIN_ROOT}` paths because installed plugin hooks must not depend on the caller's current working directory.
- Hook handlers must tolerate Codex payload fields arriving as either structured objects or strings. Use `hooks/lib/payload.sh` instead of direct jq indexing for common payload fields.
- Review and worker dispatch gates belong in explicit Coordinator scripts before `spawn_agent` / `send_input`; hook handlers are only for events whose Codex payload contains the required data.
- SessionStart is responsible for exposing the concrete `MMW_PLUGIN_ROOT` value used by Skill command examples.
- SessionStart must return valid JSON with `hookSpecificOutput.hookEventName = "SessionStart"` and `additionalContext`.
