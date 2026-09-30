# Testing

The rules for this repository's tests. The reviewer's Tests axis applies them; a ticket carries the ones that shape its work. The commands that run the tests are in `AGENTS.md` `## Commands`.

## What a test proves

A test proves what a script does, never what a piece of text says. Pinning the wording of a skill's `SKILL.md`, a reference, a refusal, or a start prompt's standing sentences forces a test edit every time that text improves, and the passing test still proves nothing about behaviour. Assert exit codes, the strings a program reads (event names and fields, labels, output tokens), the facts the behaviour produces (a number, a path, an issue number, the data rows of a prompt), and the effect on files, the tracker fake, or git.

## Layout

- A skill's tests live in `mmw-v2/tests/<name>/`, which exists only in a checkout and climbs two levels to `mmw-v2/` and down into `skills/<name>/scripts/` to reach the script under test. The one exception is `mmw-v2/skills/verify-ticket/scripts/gate-check/`: it holds only relative symlinks to `gate-check.mjs`, `gate-lint.mjs` and `lib` in `mmw-v2/upstream-unlazy/scripts/`, and gate-check's tests are unlazy's own, in that subtree.
- `MMW_V2_HOME` is a test seam for `install.sh` only: it moves the whole install target to a throwaway directory and skips `launchctl` and `paseo reload`. Runtime configuration goes through `MMW_HOME`.
- Every suite's `run.sh` calls `mmw-v2/tests/lib/run_shared_lints.sh` before its own tests. That entry runs the three shared lints, the structure lint and the wiring check, and it is the one place that lists them.

## Which suites a change needs

- The task board imports verify-ticket's `events.py` and `issue_tree.py` and dispatch's `ghlist.py` and `models.py` by file path (`mmw-v2/board/board_data.py`, `settings_api.py`), and `retro.py` loads `events.py` and `issue_tree.py` the same way; a change to them is a change to the board and the retro. Run `mmw-v2/tests/board/run.sh` together with the `relay` and `retro` suites.
- A change to `locations.py` or `roles.json` runs the `dispatch`, `liveness` and `skill-text` suites. When the change is to a path the task board reads, also run the `board`, `relay` and `retro` suites.
- A change to the format of `skills.txt`, to the part of `install.sh` that reads it, to an install copy, or to `check_own_skill_frontmatter.py` runs the cases in `mmw-v2/tests/dispatch/test_install_skill_list.py` (`test_every_marked_line_installs_its_skill`, `test_a_pstack_line_installs_from_the_pstack_subtree`, `test_an_unknown_token_after_a_skill_stops_the_install_before_any_host_is_touched`, `test_a_marker_on_an_own_skill_stops_the_install`), the cases in `mmw-v2/tests/dispatch/test_install_skill_copies.py` (`test_a_marked_skill_s_copy_has_no_invocation_switch`, `test_a_copy_s_openai_yaml_has_no_policy`, `test_every_other_entry_of_a_copy_links_back_to_the_source`, `test_host_links_of_a_marked_skill_point_at_its_copy`, `test_a_second_install_restores_a_changed_copy`, `test_only_top_level_invocation_controls_are_removed`, `test_invalid_source_names_the_file_without_destroying_the_copy`), the `test_dispatch.sh` scenarios `installcheckstalecopy`, `installcopyretired`, `installcheckwiringfails` and `installcheckwiringunchecked`, and the cases in `mmw-v2/tests/skill-text/test_skills_txt.py` (`test_frontmatter_lint_resolves_a_pstack_line_under_the_pstack_subtree`, `test_frontmatter_lint_reads_a_marked_line_as_its_skill`, `test_frontmatter_lint_rejects_a_line_install_would_refuse`, `test_installed_skills_maps_a_pstack_line_to_the_pstack_subtree`): a dispatch Python case as `python3 -u mmw-v2/tests/lib/run_unittests.py mmw-v2/tests/dispatch <case>`, a skill-text case as `bash mmw-v2/tests/skill-text/run.sh -k <case>`, and a scenario as `bash mmw-v2/tests/dispatch/test_dispatch.sh <scenario>`.
- A change to `mmw-v2/import/import_component.py` or `mmw-v2/skills/mmw/scripts/mode-hook.py` runs `bash mmw-v2/tests/mmw/run.sh`.
