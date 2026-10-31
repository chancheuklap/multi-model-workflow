## Answer
An individual researcher report saves its answer but does not directly wake the parent; the report command only calls the brief recorder, which writes `result.md` before `reported.json` [dispatch.sh:1677-1684; briefs.py:252-288]. The relay queues one `brief <batch> done` wake only when every brief in that watched batch is `reported` or `lost`, so one report suffices only for a single-brief batch or when it completes the remaining outstanding brief [briefs.py:122-152; relay.py:1142-1174]. The wake addresses the watch's parent runner/session and goes through delivery after polling; queued-key and `woken.json` checks suppress another completion wake for that batch [relay.py:939-945, 1155-1172, 1252-1263, 1287-1325].

Primary sources are in `/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/`:

- [dispatch.sh:1677](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/dispatch.sh:1677) identifies the reporting session and invokes `briefs.py report`.
- [briefs.py:252](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/briefs.py:252) validates the reporter and stores the answer, then its completion marker. [briefs.py:149](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/briefs.py:149) requires every recorded brief to be reported or lost; a starting or open brief prevents completion.
- [relay.py:1142](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:1142) detects complete watched batches and persists one parent-addressed queue row before marking the batch woken. [relay.py:353](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:353) formats the notification.
- [relay.py:1287](/Users/cheuklapchan/.codex/worktrees/631c/multi-model-workflow/mmw-v4/skills/dispatch/scripts/relay.py:1287) calls the runner to send the queued notification. Queueing is not proof of receipt: a busy runner defers delivery, failed sends remain pending, and stale recipients are dropped. The relay permits only one accepted wake per recipient per delivery pass.

This is a source reading, not an observed delivery test.

## Problems
None
