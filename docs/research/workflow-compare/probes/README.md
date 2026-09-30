# Host probes for #611

## Readers

The B1 `mode-hook.py` implementation reads `results.md` U-2 subitems to choose
events that actually inject context. B2 reads U-17 for `MMW_ROLE` inheritance.
U-1 and U-3 establish the playbook and installation-copy paths; U-9 measures
Herdr multiline submission. A result is specific to the recorded versions and
date, not a claim about every release of a host.

## Running and verifying

`bash docs/research/workflow-compare/probes/run_probes.sh` drives real host
processes and uses the existing login. Its project skills and hooks live in
temporary git repositories; MMW state lives in another `mktemp -d` directory.
`probe_hook.py` is copied into that private state and reached through this
checkout's `mmw-v2/hook-launcher.py`. The installed Orca adapter starts only
probe sessions, not tickets. An unknown `path:` selector is recorded without
registering a repository in Orca.

`python3 docs/research/workflow-compare/probes/check_results.py` is the
read-only acceptance command. `--results <path>` checks another measurement.
It never imports the real-host driver. These research probes are not part of
any test suite.

`PASS` means the capability was observed. `FAIL` means the measurement
completed but a required capability did not hold. `NEEDS-USER-CONFIG` and
`CANNOT-RUN-UNATTENDED` leave the capability unverified. `PROBES OK 13 cells`
means that all measurement records and unchanged configuration hashes are
present and consistent; it does not turn an unverified capability into a pass.

## Owner-only Codex measurements

The two explicit commands are:

```sh
bash docs/research/workflow-compare/probes/run_probes.sh --user-config U-2 codex --ticket <reach-ticket-number>
bash docs/research/workflow-compare/probes/run_probes.sh --user-config U-17 codex --ticket <reach-ticket-number>
```

This mode temporarily adds project trust and hook `trusted_hash` entries to
`~/.codex/config.toml`, restores its bytes and permissions on completion or a
handled interruption, and posts the measurement and both checksum groups to
the named ticket. It neither copies authentication files nor changes
`results.md`. Run it after the night, as the reach ticket requests. Like any
process, it cannot restore state after SIGKILL or power loss.

The owner-only real Codex runs are not part of unattended acceptance. Restoration
is checked separately against an isolated temporary configuration.

## Sources and evidence

- `docs/research/workflow-compare/reports/R18-mmw-architecture-v2.md` `11.1 实测`
  and `17. 用户的决定`: the five questions and the current host/runner selection.
- `docs/adr/0006-skills-install-to-neutral-dir.md`, second paragraph: random
  markers, fresh noninteractive processes, and `grok inspect --json`.
- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks): project
  settings and event-specific context output.
- [Codex hook discovery implementation](https://github.com/openai/codex/blob/main/codex-rs/hooks/src/engine/discovery.rs):
  hook discovery and trust. `mmw-v2/install.sh` `codex_trust_hash` supplies the
  repository's measured hash normalization.
- [Grok hooks guide](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md),
  `Hook Locations`: project folder trust; also consulted in the installed
  `~/.grok/docs/user-guide/10-hooks.md` and `08-skills.md`.
- `results-isolation-failure.md`: a rejected measurement. Codex 0.159.2 with
  `--dangerously-bypass-approvals-and-sandbox` persisted a trust entry for the
  temporary repository in `~/.codex/config.toml`. Removing only that entry
  reproduced the exact before hash. The unattended Codex commands use
  `--sandbox read-only` and `approval_policy="never"`.
