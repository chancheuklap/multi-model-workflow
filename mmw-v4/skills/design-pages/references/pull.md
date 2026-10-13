# C. Pull into the repository

Pull signed-off pages, or pull again after the owner changes a signed-off design. The design package is written only by `scripts/pull_design.py`; edit the design in Claude Design.

1. **Register decisions.** When this direct pull has no `tasks/<n>.md`, use `list_files` and the owner's sign-off to identify its pages. Write those page names into a task sheet following the skill's **Writing into a project**, before continuing; this task pulls pages rather than drawing them. Use `read_file` on the project's `设计决策记录.md`, under `## <n>`. For each `待确认` line without a ticket number at its end, open a ticket asking the owner, then append its number following **Writing into a project**. Keep `已确认` lines unchanged as part of the design baseline.
   - When the calling ticket is under a wayfinder map, open a `wayfinder:grilling` child of that map, as the `mmw-mode` skill's `references/github-issues.md` says.
   - Without a map, use the `mmw-mode` skill's `references/ticket.md` `## Opening a ticket` to open a ticket with only `## Problem`, whose first line is `Playbook: Grill with docs`, labelled `needs-triage`.
   - Write the ticket number back before pulling: readers can find the answer, and the next pull will not open the same question again. A pending line remains unsettled until its ticket answers it.
   Done when every `待确认` line under `## <n>` ends with its ticket number.
2. **Check for local edits.** Use the checkout of the project branch for this pull and its commit, even when the calling session is in `fix-<n>`. Run `git status` there on the pages that `tasks/<n>.md` lists under `design/<product>/`. Tell the owner about uncommitted edits that the pull will overwrite; wanted changes belong in Claude Design.
   Done when there are no local edits, or the owner knows about them.
3. **Get the pages and preview address.** Use `list_files` on the project root for the page names. Use `render_preview` and put its `serve_url` in `MMW_DESIGN_PREVIEW_URL`. The address lasts about an hour and carries a token; never print it or write it to a file.
   Done when you hold the page names and the environment variable is set.
4. **Run the pull.** Run `scripts/pull_design.py design/<product>/ --pages "<page>" …`, quoting every page name. List only this task sheet's pages, or the eligible pages A selected for a repull. On exit 2 the design package is unchanged: fix what stderr names and run again.
   Done when the command exits 0.
5. **Read the changes.** Use `git diff --stat design/<product>/` and `git status --short --untracked-files=all design/<product>/` to list the changed pages in the reply. The status output includes new pages that the diff omits.
   Done when you know which pages changed.
6. **Commit straight to the project branch.** Make and push one commit containing only `design/<product>/`, as the `mmw-mode` skill's `references/owning-a-task.md` `## Playbooks` allows. A running night does not receive it; the next `dispatch.sh open` brings the project branch into that night's branch, fast-forwarding or merging, and refuses on conflict. This is the `dispatch` skill's `scripts/dispatch.sh` `sync_base_with_project`. Tickets' Owns exclude `design/`. When called from a `fix-<n>`, Feature's or One ticket's, merge the project branch into `fix-<n>` after the design commit, and push it.
   Done when the design-only commit is pushed to the project branch and any calling `fix-<n>` contains it.
7. **Hand back to the caller.** First write `Pulled: <commit>` at the top of `tasks/<n>.md`, following the skill's **Writing into a project**. Use the design package commit pushed in step 6. This sheet releases its pages even when items remain unticked.
   - For a map's `wayfinder:prototype` ticket, return to the `mmw-mode` skill's Work through the map step 4. Its resolution names the design commit; that step closes the ticket and adds the map pointer.
   - For Feature step 5 or To tickets step 4, return to that step to write e2e tests against the design package.
   - For a `contract` from One ticket's **Each wake**, whose worker still holds the ticket, return to that step: it edits the e2e tests on `fix-<n>`, resumes the worker and routes the child.
   - For a `contract` a night returned to the day, update the e2e tests against the corrected design and commit them to that night's branch before its next `open`. Comment on the child with the commit and run the `dispatch` skill's `dispatch.sh route <n> <child> fixed`. Move the returned ticket and the not-yet-started tickets that night put in `needs-triage` for the same cause back to `ready-for-agent`.
   - For a direct design request, tell the owner the design package is updated. Leave e2e tests and `verify-<product>` untouched: they follow the current product. A product change goes through the `mmw-mode` skill's Feature or To spec playbook. Close the ticket opened for this direct request with a comment naming the design commit.
   - A design package update does not require rerunning the `setup-mmw` skill.
   Done when `tasks/<n>.md` has its `Pulled:` line and the next step has started, or the owner knows what was left untouched.
