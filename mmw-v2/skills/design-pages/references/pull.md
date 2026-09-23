# pull — a signed-off project into the repository

`<scripts>` below is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**. Confirm the tools below as `SKILL.md` says.

## When

Pull when the user has signed the design off, and again whenever the user has changed a signed-off design in Claude Design: on their own, or to answer a `contract` child whose body names the `design-pages` skill's `references/pull.md`. Do not replace the design package while a worker is running a ticket; a ticket held at night on a `contract` question is not running, and its worker takes the new package when it is resumed.

## MCP tools

Tools of the `claude-design` MCP server:

- `list_files`
- `render_preview`

## Steps

1. Two MCP calls. `list_files` on the project root: note the names of the `.dc.html` pages there. `render_preview`; set `MMW_DESIGN_PREVIEW_URL` to its `serve_url`. That address carries a project token and lasts about one hour; do not print it or write it to a file.
2. `<scripts>/pull_design.py <package dir> --pages <page.dc.html>... [--tools <dir>] [--state-list <README.md>] [--contract <screen-contract.yaml>]`, the package directory first and each page name quoted (names hold spaces and `·`). `<package dir>` is `prototypes/<effort>/claude-design/`, with `<effort>` as the `prototype` skill's rule 1 defines it, beside that effort's prototype leaves; every pull of the project writes the same directory. A saved `list_files` result may stand in for `--pages`, as `<scripts>/pull_design.py <list_files.json> <package dir> …`: only its root `.dc.html` paths are read. File bytes do not pass through the model. The command renders in Chromium through Playwright; a machine without that browser installs it once with `uv run --with playwright python -m playwright install chromium`. Exit 2 names the files concerned one per line above the refusal and leaves the target unchanged.

   The command finds every other file from the pages. It downloads each page, then every project file a downloaded page or stylesheet loads — `src`, `srcset`, `<link href>`, the page each `dc-import` or `x-import` names, and each stylesheet's `@import` and `url()` — and so on outward. It then renders every scene offline; a project file the render asks for that is not pulled yet is downloaded and the scenes are rendered again, up to five renders, after which a set that still grows is refused. A file nothing loads in any rendered scene — `CLAUDE.md`, `state-list.md`, notes, a design system's component sources behind its bundle, a file only a click would fetch — is not pulled. The one exception is each bound design system's `_ds/<folder>/readme.md`: it ends with the `Unifications` table the product's code follows, so it is pulled with the pages. A referenced file the project does not have is not a refusal; it is listed under `设计检查` in the report. The preview server adds a `<style>`/`<script>` pair marked `data-omelette-injected` after each HTML page's `<head>`; the command removes it, and a page that still holds that marker is refused. `design-manifest.json` records the pages given, every project file pulled and every missing reference; the next pull removes the files it lists before downloading again, so a file the project no longer loads leaves the package.

   Pass `--state-list` pointing at the `README.md` that holds the state list, when there is one: the leaf `README.md` of the `prototype` skill's `UI.md` step 6, or `prototypes/<effort>/README.md` for an existing product brought in as [edit pages](edit-pages.md) **An existing product** says. It is the file whose `## State list` the `覆盖` section matches against. Without it the report writes `state list 未给出，未核对` and the name-by-name comparison does not run.

   Pass `--contract` pointing at the screen contract when one already exists, so `改动分类` can compare the text those rows cite. Skip it on a first pull. Without it the report writes `screen contract 未给出，合同行文字未核对`.
3. Read `pull-report.md` in the package directory. Its sections are `设计检查`, `覆盖`, `改动分类`, and `本地改过的说明`. A first pull records `分类：首次`. Later pulls record `增删控件或改流转` or `只改外观或文案`. Problems in the report do not fail the command. The command runs `check_editable_selectors.py` as a module on the CSS the pages own (each `.css` outside `_ds/` and each page's `<style>` blocks); those findings land under `设计检查` as information for the next edit, not as a defect. Do not invoke that script as a separate command. `设计检查` also lists two departures from the bound design system: each class a rendered page uses that no loaded stylesheet defines, and each hand-written length in a static `style` attribute (type size, spacing, offset) that no `--variable` under `_ds/` holds. Each one is a design fix to make in Claude Design before the design ticket closes, as **Design problems in the report** says.
4. Commit the design package and `pull-report.md` together.

Done when: `pull-report.md` is in the package directory, the package and the report are committed, and `改动分类` has been read so **Reached from here** can name the following skill.

## After the first pull

Go to the prototype skill's `UI.md` step 7, **Take the scaffolding down**. How to take it down is written only there.

## Design problems in the report

- While the design ticket is still open: return to [edit pages](edit-pages.md), fix the pages in Claude Design, and pull again. The design ticket closes after the first pull whose `设计检查` has nothing left to fix, with a comment naming that commit and the package directory.
- During implementation: open a `contract` child under the interface ticket whose page it is, with the `verify-ticket` skill's `--sub-issue contract` on that ticket, naming the Claude Design page, the problem, and the `design-pages` skill's `references/pull.md`.

MCP tools cannot create a comment on a design page, so this does not go through comments.

## Reached from here

A pull made for a wayfinder map's design ticket ends at that ticket: once **Design problems in the report** lets it close, return to the `wayfinder` skill to record the resolution. The screen contract is the alignment ticket's.

For any other pull, whether the effort's screen contract `docs/specs/<effort>/screen-contract.yaml` exists, and then `改动分类` in the pull report, decide which skill this run hands to; there is no default:

- **No screen contract yet**, whatever `改动分类` says — the `write-screen-contract` skill, for the whole contract. Then the `to-spec` skill, which writes the spec this effort does not have yet.
- **增删控件或改流转** — the `write-screen-contract` skill at its **Re-runs** section, which edits only the rows those controls belong to. Then the `to-spec` skill's step for revising a published spec; tickets already cut are corrected against the new text, the way the `to-tickets` skill's `references/cutting-interface-tickets.md` describes under **When the rows change**.
- **只改外观或文案** — the screen contract does not change, because no `data-ui` id did. An open ticket picks up the new package on its next run. Landed tickets are re-run by the `dispatch` skill's `reverify <spec>` on `origin/<base branch>`, which reopens a red one into triage with `ticket.regressed`; that reopened ticket is the correction. Push the commit to `origin/<base branch>`. While the spec's night is open, its closing pass runs `reverify`; after its `summary` and before its `finish`, run `reverify <spec>` from this session. After `finish` the base branch is gone and `reverify` has nothing to run on: tell the user that the spec's landed tickets were not re-run against the new package.

## A `contract` child answered by this pull

When the pull answered a `contract` child, finish it after the package is committed and pushed to `origin/<base branch>` and the skill **Reached from here** names has run. Do it the way the `dispatch` skill's `references/night.md` finishes a corrected `contract` child: comment on the child with the commit, route it `fixed`, move the not-yet-started tickets the night moved to `needs-triage` back to `ready-for-agent`, and resume the held worker with that commit to integrate from and `continue`. The worker then runs its criteria on the new package.

Git is the design's version history; Claude Design keeps none.
