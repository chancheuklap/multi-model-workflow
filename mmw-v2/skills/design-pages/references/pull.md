# pull — a signed-off project into the repository

`<scripts>` below is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**. Confirm the tools below as `SKILL.md` says.

## When

Pull when the user has signed the design off. After that, pull only in a session that is handling a design-class `contract` child. Do not replace the handoff package while a worker is mid-run.

## MCP tools

- `mcp__claude-design__list_files`
- `mcp__claude-design__render_preview`
- `mcp__claude-design__read_file` — only when `pull_design.py` names text files for `--reread`

## Steps

1. Two MCP calls. `list_files` with `depth: -1` (sizes are in that response); save the unchanged JSON. `render_preview`; set `MMW_DESIGN_PREVIEW_URL` to its `serve_url`. That address carries a project token and lasts about one hour; do not print it or write it to a file.
2. `<scripts>/pull_design.py <manifest.json> <handoff dir> [--reread <dir>] [--tools <dir>] [--state-list <README.md>] [--contract <screen-contract.yaml>]`. File bytes do not pass through the model. Exit 1 lists text files whose downloaded size does not match the manifest: `read_file` those paths into one directory (256 KiB per file) and rerun with `--reread <dir>`. Exit 2 leaves the target unchanged.

   Pass `--state-list` pointing at the prototype leaf `README.md` — the file whose `## State list` the `覆盖` section matches against. Without it the report writes `state list 未给出，未核对` and the name-by-name comparison does not run.

   Pass `--contract` pointing at the screen contract when one already exists, so `改动分类` can compare the text those rows cite. Skip it on a first pull. Without it the report writes `screen contract 未给出，合同行文字未核对`.
3. Read `pull-report.md` in the handoff directory. Its sections are `设计检查`, `覆盖`, `改动分类`, and `本地改过的说明`. A first pull records `分类：首次`. Later pulls record `增删控件或改流转` or `只改外观或文案`. Problems in the report do not fail the command. The command runs `check_editable_selectors.py` as a module on the downloaded stylesheets; those findings land under `设计检查`. Do not invoke that script as a separate command.
4. Commit the handoff package and `pull-report.md` together.

Done when: `pull-report.md` is in the handoff directory, the package and the report are committed, and `改动分类` has been read so **Next** can name the following skill.

## After the first pull

Go to the prototype skill's `UI.md` step 7, **Take the scaffolding down**. How to take it down is written only there.

## Design problems in the report

- While the handoff ticket is still open: return to [edit pages](edit-pages.md), fix the pages in Claude Design, and pull again.
- During implementation (including a night): open a `contract` child naming the Claude Design page and the problem, for daytime handling.

MCP tools cannot create a comment on a design page, so this does not go through comments.

## Next

Read `改动分类` in the pull report, then:

- **首次**, or **增删控件或改流转** — the `align-screens` skill (full contract on a first pull; later, only the rows its **Re-runs** section names). Then the `to-spec` skill's step 5, to revise the published spec. Tickets already cut are corrected against the new text.
- **只改外观或文案** — the screen contract does not change. Open tickets pick up the new package on their next run. Closed tickets are re-run by the main agent with the `verify-ticket` skill as `references/running-criteria.md` describes in **The two runs that execute a `CHECK:`**. A criterion that then fails is cut as a fix ticket whose acceptance criterion is the same as the original.

Git is the design's version history. Claude Design has none (help centre, **Known limitations**).
