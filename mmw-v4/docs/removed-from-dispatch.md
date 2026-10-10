# Removed from dispatch

v4's dispatch started as a copy of v2's (`mmw-v2/skills/dispatch/`). Block 4 took these out, as page 8 of the v4 design says: "retro、Memory、看板 拿掉，逐条记下". Each entry names what went, where it lives in v2 so it can be copied back, and when it returns. `scripts/` and `references/` are under `mmw-v2/skills/dispatch/`, `tests/` under `mmw-v2/`; those files are unchanged and stay the source.

## Returns with its own block

| What | Where in v2 | Returns |
| --- | --- | --- |
| The retro gate: `finish` refused while the night's retro was not done, and the scenario that tested it (`finishrefusesretro`) | `scripts/dispatch.sh`, `finish_preflight`; `tests/dispatch/test_dispatch.sh` | With the retro block |
| Memory: the worker's Memory packet in its start prompt, the repository Memory check, `memory-list`, closing a spec's Memory records, the `--memory-decisions` argument of `summary`, the suite's fake `nmem` | `scripts/dispatch.sh`: `worker_memory_packet`, `ensure_repository_memory`, `memory_list_spec`, `close_spec_memories`; `tests/dispatch/test_dispatch.sh` | With the Memory block |
| The reviewer's Rules packet, read from Memory | `scripts/dispatch.sh`, `reviewer_rules_packet` | With the Memory block |
| The task board: `open` and `open-ticket` registered and opened it | `scripts/dispatch.sh`: `ensure_board`, `open_board`; the board scenarios and their fakes in `tests/dispatch/test_dispatch.sh` | With the board block, before v4 is installed |
| The install scenarios (`install*`, `uses*`), the Orca folder test, the `models.json` import | `tests/dispatch/test_dispatch.sh`, `tests/dispatch/test_install_orca_folder.py` | With v4's `install.sh` |

## Removed for good

| What | Where in v2 | Why |
| --- | --- | --- |
| `adopt` and its reference | `scripts/dispatch.sh`, `adopt_ticket`; `references/inside-a-ticket.md` | A ticket with criteria is worked only by a worker dispatch started (page 8) |
| Pi as a host | `scripts/models.py`, `hosts.json` | Decided in v3 (ADR 0032) |
| Product slots | `scripts/dispatch.sh`: `lease_worktree_for`, `give_slot_back`, `give_ticket_slot_back`; the slot field of `status.py`; `mmw-v2/skills/ui-acceptance/`'s `lease.py`; the scenarios `slotatclaim`, `stopproduct`, `suspendbusy`, `landedworktreekept`, `archiveremovesinstance`, `bouncekeepsinstance`; `slotwake` in `tests/relay/test_relay.sh` | The acceptance screens are out of v4 (page 10); 0 of 715 wakes used the slot queue (page 5) |
| `--tools` passed on to verify-ticket, and every ui-acceptance path | `scripts/dispatch.sh` | The acceptance screens are out of v4 (page 10) |
| `advise` | `scripts/dispatch.sh`, `advise_one` | `send advisor <brief>` replaces it (page 8) |
| Creating labels | `scripts/dispatch.sh`, `ensure_label` | verify-ticket creates a label the first time it uses one (page 10) |
