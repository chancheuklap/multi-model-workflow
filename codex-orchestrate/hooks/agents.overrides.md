# hooks override

- Hooks are Codex plugin hooks. Do not restore old-host hook matchers, `if` expressions, old plugin root environment variables, or old state paths.
- Root `codex-orchestrate/hooks.json` is the Codex hook manifest. Files under `hooks/` are executable handlers only.
- Multi-agent lifecycle hooks use Codex `SubagentStart` and `SubagentStop` payloads. Do not depend on legacy dispatch tool names or legacy payload fields.
- Hook scripts must fail closed for malformed workflow dispatch/review envelopes when they are on the production workflow path.
- Review gate and review budget hooks run on native `SubagentStart` events for baseline `codex_reviewer` dispatches. Targeted re-review, including Path A self-fix review, must use `send_input` to the baseline reviewer and must not create a new reviewer.
- SessionStart is responsible for exposing the concrete `MMW_PLUGIN_ROOT` value used by Skill command examples; do not use Claude-specific plugin root variables.
