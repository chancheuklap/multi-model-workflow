---
name: design-pages
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Design pages

The owner designs a UI in Claude Design, with the agent inside it. This skill says what the repository needs from that work: a **Claude Design project** whose pages carry the conventions the repository reads back, and the **design package**, the signed-off project written into the repository by `scripts/pull_design.py`. Three playbooks do the work, each naming this skill: Design in Claude Design sets the project up and takes the owner's sign-off, Pull a design brings the project into the repository, Build a design system builds the look the pages are drawn from.

What the pull writes is copied exactly by implementation and compared element by element by the `ui-acceptance` skill's story oracle, and only a session with the Claude Design tools can correct it: a page that is wrong in the repository becomes a wrong product, or a night ticket stalled on a `contract` child. So hold the pages to the conventions in the project `CLAUDE.md`; how they look is the owner's call.

## Who can do this work

Only a session whose host has the Claude Design MCP tools, and a dispatched worker never does it. In a session without them, tell the owner the work needs a session whose host has those tools, and stop before writing anything.

## The project

A Claude Design project holds the pages of one effort. The agent inside it sees only its own project, and reads the project-root `CLAUDE.md` on every conversation; it reads this repository only through Claude Design's GitHub connection, from a branch that has been pushed. So what it must always do is a file in the project, written by this session:

- `CLAUDE.md`: the block of [references/template-project-claude-md.md](references/template-project-claude-md.md), unchanged. It defines page names, `scene`, page data, `$preview` and `data-ui`, which is everything the pull reads back.
- `state-list.md`: the state list, when there is one (**The state list** below).
- `ui-ids.md`: when the product already carries `data-ui` ids, one `## Component · <region>` heading per region and one list item per id, collected by opening the product's story page for each scene of the last design package's `scenes.json` and reading every `[data-ui]` it renders. Ids read from `scenes.json` alone miss elements that carry no text.
- `_ds/<folder>/`: a copy of the bound design system, when the project is bound to one (**After the design system changes** below).
- `task.md`: the work to do now (**Talking to the agent inside Claude Design** below).

### Talking to the agent inside Claude Design

That agent sees only its project, and reads its `CLAUDE.md` on every conversation. Rules that always hold are files in the project (`CLAUDE.md`, `state-list.md`, `ui-ids.md`); the work to do now is `task.md` at the project root: one checkbox item per piece of work, each naming the pages, files or repository paths it needs (a repository path with its branch, pushed before `task.md` is written) and what done looks like. The project's `CLAUDE.md` tells that agent to do `task.md` when the owner says to start or continue, and to tick items as it finishes them. So the owner never composes instructions: write or replace `task.md` (`finalize_plan` naming it, then `write_files` with its etag, or `if_match: "0"` when new), and tell the owner to say `开始` in that project, or `继续` when it already started.

A change the owner thinks of while looking at a page, they say to that agent directly, or edit in the editor. When the owner says the work is done, read `task.md` back: an unticked item is what to ask about.

### After the design system changes

Changes to a design system are made in Claude Design, by the owner or by its agent. A bound page project's `_ds/<folder>/` copy does not follow by itself; refresh it from here before the page project's agent draws again: `list_files` both projects, `delete_files` every file under `_ds/<folder>/` that the design system no longer has, and `copy_files` (with `src_project_id` set to the design system) of `styles.css`, `readme.md` and the variable, part, font and icon directories into `_ds/<folder>/`. Pull again after the copy changes.

## The state list

The state list names the regions and states to draw: one `### <region>` heading per region (the region name is the later `Component · <region>` page) and one list item per state, starting with the state name (the later `scene` value). It is the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names, or, for an existing product, of `prototypes/<effort>/README.md`, written as Build a design system's **An existing product** says. A UI has one state list. The pull report and any decision ticket that will change a page's states match against its names.

## The design package

The pull writes the design package to `prototypes/<effort>/claude-design/`, where `prototypes/<effort>/` is the directory that holds this effort's prototype leaves, or its `README.md` with the state list for an existing product; when neither exists, `<effort>` is as the `prototype` skill's rule 1 **Lives in `prototypes/`** defines it. The pull also writes `pull-report.md` beside the pages. Every pull of the project writes the same directory, and the package holds exactly the files the pages load: the bound design system's `readme.md` comes with it, for the `Unifications` table the product's code follows, and example data lives beside it, never inside it.

The design package is written only by `pull_design.py`, never by Claude Design's "Handoff to Claude Code" export, and a local edit is overwritten by the next pull. Git is the design's version history; Claude Design keeps none.

`pull-report.md` is also the convention check: when you doubt the pages hold the conventions, pull and read the report rather than reading pages by hand. Its sections:

| Section | What it says |
| --- | --- |
| `设计检查` | Defects in the pages. `编辑器点不中的选择器` (a selector the editor cannot reach) and `未核对` (a check that did not run) are information for the next edit in Claude Design; every other line is a design fix. |
| `覆盖` | A state the state list names that no page draws, a page with no `scene`, a page root with no `data-ui`: design fixes, since nothing can be checked that the pages do not declare. |
| `改动分类` | What changed since the last committed package: `首次` (no earlier package to compare), `增删控件或改流转` (controls added or removed, or a transition changed) or `只改外观或文案` (only look or copy). Pull a design routes by it. |
| `本地改过的说明` | The package had local edits, which this pull has overwritten. |

## A design system

A Claude Design design system is a separate project holding a product's variables, fonts, icons and reusable parts, each part one class name with its variants and one card showing every state. A page project bound to it gets a copy under `_ds/<folder>/`, and its pages are drawn from it. What it holds and does not hold is the block of [references/template-design-system-claude-md.md](references/template-design-system-claude-md.md), which becomes its project `CLAUDE.md`.

It gives every page one look: the agent inside Claude Design composes named parts and steps instead of guessing values, so a page drawn next month matches one drawn today. Built from an existing product, it is also where the product's inconsistencies are settled: each unified value is a row of `Unifications`, and the product follows once pages drawn with it are pulled. Only Claude Design's own agent compiles a design system, so this session never writes its parts; it writes the `CLAUDE.md` and `task.md` that agent reads, and checks what it made. No oracle compares against the design system: the pull brings in only its `readme.md`, for the `Unifications` table the product's code follows, and the story oracle works from the pulled pages. It is not a step every design must pass through.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/pull_design.py <package dir> --pages <page.dc.html>... [--state-list <README.md>] [--contract <screen-contract.yaml>]` | Downloads the named pages and every file they load from the address in `MMW_DESIGN_PREVIEW_URL`, renders each scene offline in Chromium, writes the design package and `pull-report.md`. Exits 0 whatever the report finds; exit 2 leaves the package as it was, and stderr says why. File bytes do not pass through the model. |
| `scripts/check_editable_selectors.py` | Run by the pull: finds the stylesheet selectors the Claude Design editor cannot reach, for the `编辑器点不中的选择器` line. |

Both render with the `ui-acceptance` skill's `scripts/design_render.py`, found beside this skill. A machine without Chromium installs it once with `uv run --with playwright python -m playwright install chromium`.
