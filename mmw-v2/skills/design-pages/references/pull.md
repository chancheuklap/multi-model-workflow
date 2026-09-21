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
2. `<scripts>/pull_design.py <manifest.json> <handoff dir> [--reread <dir>] [--tools <dir>] [--state-list <README.md>] [--contract <screen-contract.yaml>]`. `<handoff dir>` is `prototypes/<task>/claude-design/`, with `<task>` as the `prototype` skill's rule 1 defines it, beside that effort's prototype leaves; every pull of the project writes the same directory. File bytes do not pass through the model. Exit 1 lists text files whose downloaded size does not match the manifest: `read_file` those paths into one directory (256 KiB per file) and rerun with `--reread <dir>`. Exit 2 leaves the target unchanged.

   Pass `--state-list` pointing at the leaf `README.md` that holds the state list ([edit pages](edit-pages.md), **Write pages**): the file whose `## State list` the `覆盖` section matches against. Without it the report writes `state list 未给出，未核对` and the name-by-name comparison does not run.

   Pass `--contract` pointing at the screen contract when one already exists, so `改动分类` can compare the text those rows cite. Skip it on a first pull. Without it the report writes `screen contract 未给出，合同行文字未核对`.
3. Read `pull-report.md` in the handoff directory. Its sections are `设计检查`, `覆盖`, `改动分类`, and `本地改过的说明`. A first pull records `分类：首次`. Later pulls record `增删控件或改流转` or `只改外观或文案`. Problems in the report do not fail the command. The command runs `check_editable_selectors.py` as a module on the downloaded stylesheets; those findings land under `设计检查`. Do not invoke that script as a separate command.
4. Commit the handoff package and `pull-report.md` together.

Done when: `pull-report.md` is in the handoff directory, the package and the report are committed, and `改动分类` has been read so **Reached from here** can name the following skill.

## After the first pull

Go to the prototype skill's `UI.md` step 7, **Take the scaffolding down**. How to take it down is written only there.

## Design problems in the report

- While the handoff ticket is still open: return to [edit pages](edit-pages.md), fix the pages in Claude Design, and pull again.
- During implementation (including a night): open a `contract` child naming the Claude Design page and the problem, for daytime handling.

MCP tools cannot create a comment on a design page, so this does not go through comments.

## Reached from here

Read `改动分类` in the pull report. It decides which skill this run hands to, and there is no default:

- **首次** — the `write-screen-contract` skill, for the whole contract: this is the first time each control is bound to what it calls. Then the `to-spec` skill from its **Process** step 1, which writes the spec this effort does not have yet.
- **增删控件或改流转** — the `write-screen-contract` skill at its **Re-runs** section, which edits only the rows those controls belong to. Then the `to-spec` skill at its **Process** step 5, revising the published spec; tickets already cut are corrected against the new text, the way the `to-tickets` skill's `references/cutting-interface-tickets.md` describes under **When the rows change**.
- **只改外观或文案** — the screen contract does not change, because no `data-ui` id did. An open ticket picks up the new package on its next run. A landed ticket is re-run by the main agent with `--reverify --actor main`, which the `verify-ticket` skill's `references/running-criteria.md` gives in **The two runs that execute a `CHECK:`**, in the paragraph that adds the main agent's run to the worker's two. A criterion that then fails is cut as a correction ticket whose criterion is the same as the original's.

Git is the design's version history. Claude Design has none (help centre, **Known limitations**).
