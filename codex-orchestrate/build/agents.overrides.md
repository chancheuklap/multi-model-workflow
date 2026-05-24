# build override

- The build system processes both Skill Markdown files and Codex agent TOML files because agent instructions now live in `developer_instructions` strings.
- Do not restore Markdown agent definitions as the runtime source. Keep `agents/*.toml` as the Codex agent source of truth.
- Build tests should verify template injection against the current source files, not deleted old-host agent files.
