# build override

- The build system processes both Skill Markdown files and Codex agent TOML files because agent instructions now live in `developer_instructions` strings.
- Do not restore Markdown agent definitions as the runtime source. Keep `agents/*.toml` as the Codex agent source of truth.
- Build tests should verify template injection against the current source files, not deleted old-host agent files.
- Review dispatch templates must use Codex native `codex_reviewer` subagents through `spawn_agent`, `send_input`, and `wait_agent`; do not add script or companion CLI review runners.
- Review dispatch templates may call explicit validation scripts before `spawn_agent` / `send_input`; those scripts are gates, not review executors.
- Script command templates must use `${MMW_PLUGIN_ROOT}` for plugin helper scripts; never restore old-host plugin root variables.
- Resume templates must use Codex `send_input` plus `wait_agent`; do not describe old message-resume APIs.
- Build tests must assert current Codex-native structure directly and must not preserve removed runner strings only to prove their absence.
