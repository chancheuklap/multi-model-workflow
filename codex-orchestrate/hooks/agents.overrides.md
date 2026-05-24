# hooks override

- Hooks are Codex plugin hooks. Do not restore old-host hook matchers, `if` expressions, old plugin root environment variables, or old state paths.
- Root `codex-orchestrate/hooks.json` is the Codex hook manifest. Files under `hooks/` are executable handlers only.
- Multi-agent lifecycle hooks use Codex `SubagentStart` and `SubagentStop` payloads. Do not depend on legacy dispatch tool names or legacy payload fields.
- Hook scripts must fail closed for malformed workflow dispatch/review envelopes when they are on the production workflow path.
