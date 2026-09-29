# pull — a signed-off project into the repository

## When

Pull when the user has signed the design off, and again whenever the user has changed a signed-off design in Claude Design: on their own, or to answer a `contract` child whose body names the `design-pages` skill's `references/pull.md`. Do not replace the design package while a worker is running a ticket; a ticket held at night on a `contract` question is not running, and its worker takes the new package when it is resumed.

## Steps

1. Two MCP calls. `list_files` on the project root: note the names of the `.dc.html` pages there. `render_preview`; set `MMW_DESIGN_PREVIEW_URL` to its `serve_url`. That address carries a project token and lasts about one hour; do not print it or write it to a file.
2. `scripts/pull_design.py <package dir> --pages <page.dc.html>... [--state-list <README.md>] [--contract <screen-contract.yaml>]`, the package directory first and each page name quoted (names hold spaces and `·`). `<package dir>` is `prototypes/<effort>/claude-design/`, where `prototypes/<effort>/` is the directory that holds this effort's prototype leaves, or its `README.md` with the state list for an existing product; when neither exists, `<effort>` is as the `prototype` skill's rule 1 **Lives in `prototypes/`** defines it. Every pull of the project writes the same directory. File bytes do not pass through the model.

   Pass `--state-list` pointing at the `README.md` that holds the state list, when there is one.

   Pass `--contract` pointing at the screen contract when one already exists, so `改动分类` can compare the text those rows cite. Skip it on a first pull.
3. Read `pull-report.md` in the package directory; the command exits 0 whatever the report finds. Under `设计检查`, an `编辑器点不中的选择器` line, and a line saying `未核对` (a check that did not run), are information for the next edit in Claude Design, not a defect; every other `设计检查` line is a design fix, handled as **Design problems in the report** says. `改动分类` decides **Reached from here**.
4. Commit the design package and `pull-report.md` together.

Done when: `pull-report.md` is in the package directory, the package and the report are committed, and `改动分类` has been read so **Reached from here** can name the following skill.

## After the first pull

Take down the scaffolding the `prototype` skill's UI prototype put up so its winner rendered inside the real app: the mount point or prototype route that renders the variants, the floating switcher, the import of the leaf directory, and any symlink beside the route. A prototype built with no app yet has none.

Done when nothing outside the leaf directories imports them: each can be deleted without breaking the build; the variants stay there as reference.

## Design problems in the report

- While the design ticket is still open: return to [edit pages](edit-pages.md), fix the pages in Claude Design, and pull again. The design ticket closes after the first pull whose `设计检查` and `覆盖` have nothing left to fix, with a comment naming that commit and the package directory.

  Under `覆盖`, a state the state list names that no page draws, a page with no `scene`, and a page root with no `data-ui` are design fixes like the `设计检查` lines: acceptance cannot check what the pages do not declare, and the `write-screen-contract` lint refuses them after the design ticket has closed. When `本地改过的说明` says the package had local edits, those edits are gone now: tell the user, because a change they wanted has to be made again in Claude Design.
- During implementation: open a `contract` child under the page ticket whose page it is, with the `verify-ticket` skill's `--sub-issue contract` on that ticket, naming the Claude Design page, the problem, and the `design-pages` skill's `references/pull.md`.

MCP tools cannot create a comment on a design page, so this does not go through comments.

## Reached from here

A pull made for a wayfinder map's design ticket ends at that ticket: once **Design problems in the report** lets it close, return to the `wayfinder` skill to record the resolution. The screen contract is the alignment ticket's.

For any other pull, whether the effort's screen contract `docs/specs/<effort>/screen-contract.yaml` exists, and then `改动分类` in the pull report, decide which skill this run hands to; there is no default:

- **No screen contract yet**, whatever `改动分类` says — the `write-screen-contract` skill, for the whole screen contract.
- **增删控件或改流转** — the `write-screen-contract` skill at its **Re-runs** section, which edits only the rows those controls belong to.
- **只改外观或文案** — the screen contract does not change, because no `data-ui` id did. An open ticket picks up the new package on its next run. Landed tickets are re-run by the `dispatch` skill's `reverify <spec>` on `origin/<base branch>`, which reopens a red one into triage with `ticket.regressed`; that reopened ticket is the correction. Until the night's `finish`, push the commit to `origin/<base branch>`: while the night is open, its closing pass runs `reverify`; after its `summary`, run `reverify <spec>` from this session. After `finish` the base branch is gone: push to the project branch the night merged into, and tell the user that the spec's landed tickets were not re-run against the new package.

## A `contract` child answered by this pull

When the pull answered a `contract` child, finish it after the package is committed and pushed to `origin/<base branch>` and the skill **Reached from here** names has run, with the `dispatch` skill's `dispatch.sh`: comment on the child with the commit; `dispatch.sh route <n> <child> fixed`; move the not-yet-started tickets the night moved to `needs-triage` back to `ready-for-agent`; `dispatch.sh resume <n> "<the commit to integrate from>, then: continue"`. The worker then runs its criteria on the new package.

Git is the design's version history; Claude Design keeps none.
