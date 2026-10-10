# Removed from verify-ticket

v4's verify-ticket started as a copy of v2's (`mmw-v2/skills/verify-ticket/`). Block 3 left UI acceptance out, as page 10 of the v4 design says: "验收界面全部 拿掉，记下", and kept two known bugs open. Each entry names what went, where it lives in v2 so it can be copied back, and when it returns. `scripts/` is under `mmw-v2/skills/verify-ticket/`, `tests/` under `mmw-v2/`; those files are unchanged and stay the source.

## Returns with the UI block

| What | Where in v2 | Returns |
| --- | --- | --- |
| The product slot a criterion that drives the app holds while it runs, its lease and its queue: `worker.queued`, the slot fields of an event, exit 3 | `scripts/verify-ticket.py`: `needs_product`, `hold_slot`, `give_slot_back`, `load_lease` | With the UI block |
| `--tools` and the check that each criterion's judge can be reached | `scripts/verify-ticket.py`: `tool`, `require_judges` | With the UI block |
| The screen-contract lint and the acceptance-journey rules it reads: critical flows, mounts, boundary tests, pipeline flags, a skipped baseline | `scripts/verify-ticket.py`: `lint_screen_contract`, `load_contract_doc`, `acceptance_journeys`, `critical_flows`, `page_mounts`, `story_mounts`, `row_mount`, `row_needs_boundary`, `boundary_test_paths`, `lint_pipeline_flags`, `segment_flags`, `flag_values`, `help_flags`, `run_values`, `script_segment`, `baseline_skipped`, `source_findings`, `load_yaml_file`, `_discover_paths` | With the UI block |
| The tests of all three | `tests/verify-ticket/` | With the UI block |

Without the product slot, two tickets that start the app at the same time can take the same port (inferred on page 10). A ticket whose criteria do not drive the app needs none of this.

## Known bugs, not fixed in block 3

| Bug | What it does |
| --- | --- |
| #786 | `--lint` does not report a `CHECK:` that reads a file another ticket of the same batch owns |
| #871 | After a pytest run over 60 seconds the success line carries its duration, and an `EXPECT:` copied from a shorter run no longer matches |
