# Host probes

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

Herdr uses the product adapter's `probe-server` and `probe-workspace` verbs to
bootstrap a separate named server with private socket and configuration paths.
Its `start`, `send` and `stop` verbs then reach a Grok pane. The UserPromptSubmit
hook records the two-line probe payload, so a reply containing both markers
alone cannot conceal two separate submissions. The bootstrap verbs refuse an
unnamed session or missing private paths; the running night's frozen adapter
is not changed or replaced.

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

U-17 first asks Orca to open `path:<temporary repository>`. A refusal causes
no user configuration write: its original refusal, a `CANNOT-RUN-UNATTENDED`
row and equal checksum groups are posted to the ticket. It registers nothing
in Orca. Spec #593 `Implementation Decisions` section 10, `Orca 拒绝时`, and
#611 `What to build` point 5 define this outcome; #612 holds the owner's decision
about a location where the measurement could actually run.

After a successful U-17 terminal start, or directly for U-2, this mode adds
project trust and hook `trusted_hash` entries to
`~/.codex/config.toml`, restores its bytes and permissions on completion or a
handled interruption, and posts the measurement and both checksum groups to
the named ticket. It neither copies authentication files nor changes
`results.md`. Run it after the night, as the reach ticket requests. Like any
process, it cannot restore state after SIGKILL or power loss.

The owner-only real Codex runs are not part of unattended acceptance. Restoration
is checked separately against an isolated temporary configuration. Codex 0.159.2
app-server turns and compaction were measured with the existing login and
read-only ephemeral threads without editing user configuration. An empty
`CODEX_HOME` separately verified hook-trust discovery before authentication
failed; no authentication file was copied. Neither proves the unrun owner-only
three-event probe.

## U-7: which entry a typed sentence reaches

Ticket #702 measures which skills and playbooks a fresh Claude Code, Codex or
Grok session actually loads for eleven requests a person would type. It compares
the installed skill set of `6d9cf01c` with the clean `mmw-v2/` tree at the measured
`HEAD`. `u7-sentences.md` fixes the requests and expected entries from N10 section
3.2; `mmw:<slug>` requires both the `mmw` skill and that playbook.

```sh
bash docs/research/workflow-compare/probes/run_probes.sh --u7
python3 docs/research/workflow-compare/probes/check_u7.py
python3 docs/research/workflow-compare/probes/test_u7.py
```

The driver exports each commit and runs that export's installer in distinct
temporary `HOME` and `MMW_V2_HOME` directories, with external programs replaced
by stubs. It checks every installed skill and marked copy, then copies the skill
directories into one project-level location per host and set. Internal symlinks
remain links to their original absolute targets, including cyclic links.

Each host first reports its catalog in an empty temporary repository. A measured
name outside the version-pinned built-in list makes that host's 22 cells
`NEEDS-USER-CONFIG`; a different version from the recorded list also blocks the
group. A catalog containing only measured built-in names at the recorded version
permits routing sessions, which still check every tool call for user-level paths.
An absent binary or unreadable catalog makes the cells
`CANNOT-RUN-UNATTENDED`. Neither outcome starts routing sessions. The unattended
driver does not change user-level skills or configuration. Its seven before and
after checksums cover five configuration files and both user-level skill directories.

`results-u7.md` contains 66 versioned cells. `PASS` means the expected entry was
observed in tool calls; `FAIL` means it was not. The evidence starts with
`skills` and `playbooks` in first-observed order, followed by `tool-calls`,
`expected` and `exit`. `tool-calls=0` on a `FAIL` is not a routing conclusion:
no tool event was parsed. User-level paths read by a session are recorded as
`NEEDS-USER-CONFIG`. A nonzero session exit without the entry, or a timeout, is
`CANNOT-RUN-UNATTENDED`. Assistant claims such as `LOADED:` do not establish a pass.

`check_u7.py` is read-only and never starts a host. `--results <path>` checks a
copy. `U7 OK 66 cells` confirms complete, consistent records, their commits and
unchanged user-level checksums, not successful routing in all cells. The next
line reports how many cells carry routing results and each status count. A
name-only Claude catalog collision does not establish user-level provenance:
Claude Code 2.1.286 includes a built-in `code-review`. `run_u7.py` records the
version, same-name user symlink count and observed catalog names that establish
whether `--setting-sources project` excludes user-level skills. `test_u7.py`
uses isolated files and event streams, never hosts or installers; captured and
synthetic host fixtures are identified in `run_u7.py`'s measurement header.

Ticket #703 uses the owner-only command after the unattended run:

```sh
bash docs/research/workflow-compare/probes/run_probes.sh --u7 --owner --ticket <reach-ticket-number>
```

It selects hosts with unverified cells, temporarily moves MMW symlinks out of
`~/.agents/skills` and `~/.claude/skills`, measures their two sets, restores the
links and posts the cells plus checksums to that ticket. It does not change
`results-u7.md`. If no host needs remeasurement it creates nothing and posts
nothing. While the links are moved, other local agent sessions cannot discover
the user-level MMW skills. Normal completion, exceptions and SIGINT/SIGTERM
restore the links. SIGKILL or power loss cannot: move the entries from the printed
staging directory's `.agents/skills` and `.claude/skills` subdirectories back into
the corresponding user-level directories before starting more sessions.

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
- [Herdr CLI reference](https://raw.githubusercontent.com/herdrdev/herdr/v0.9.0/docs/next/website/src/content/docs/cli-reference.mdx),
  `Environment variables` and `Agent commands`: named server/socket selection
  and multiline `agent prompt`. The installed Herdr 0.9.0 binary is the command
  authority used for the measurement.
- `results-isolation-failure.md`: a rejected measurement. Codex 0.159.2 with
  `--dangerously-bypass-approvals-and-sandbox` persisted a trust entry for the
  temporary repository in `~/.codex/config.toml`. Removing only that entry
  reproduced the exact before hash. The unattended Codex commands use
  `--sandbox read-only` and `approval_policy="never"`.
