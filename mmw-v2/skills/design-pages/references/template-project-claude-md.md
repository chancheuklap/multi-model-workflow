# Design project `CLAUDE.md`

Write the block below, unchanged, into the Claude Design project root as `CLAUDE.md`. It instructs the agent inside that project, not you: that agent reads it on every conversation and sees nothing of this repository.

```markdown
# Page conventions

These conventions are what the repository reads back from this project when the design is pulled. Everything else about how pages are designed is open. Keep `scene` and `$preview` on every page below even where general guidance says to drop props nothing reads.

## Page names

A page's title, its file name (without `.dc.html`) and its `dc-import` name are the same string.

- `Component · <name>`: one region of the screen (title bar, list, form, sidebar, a group of dialogs). This is the unit acceptance checks.
- `App · <name>`: a whole screen made of `Component · ` pages. Needed only when the regions' states have to be checked together. On it each region fills the slot the page gives it, whatever height the region page takes on its own, and a region drawn over others (a dialog, a sheet) keeps no background of its own there, so what it covers shows through: the `App · ` page's own style sets both.

` · ` is space, U+00B7, space. Other pages (notes, overviews, explorations) may use any name without these prefixes; they are not pulled into acceptance.

## `scene`

Every `Component · ` and `App · ` page exposes one enum prop named `scene` in `data-props`. Its values are the states that will be checked: on a `Component · ` page every state of that region, combined states included; on an `App · ` page each whole-screen combination. A value contains no `/`.

A state that is not shipping may stay in `options` if it is also listed under `out_of_scope` inside the `scene` prop: `"scene": {"editor": "enum", "options": ["ready", "empty", "future"], "out_of_scope": ["future"]}`.

`state-list.md` at the project root, when present, is the list of regions and states to draw. Read it before drawing or changing a page: each `### <region>` heading in it is one `Component · <region>` page, and each list item's leading name is one `scene` value of that page. When a page and the list disagree, ask the user which one changes; do not edit `state-list.md` yourself.

## Example data

Each `Component · ` page draws its scenes from one data file under `data/` that holds one entry per `scene` value, written `window.<NAME> = { "<scene>": { ... }, ... };`. The page's own `renderVals()` turns the entry into what it shows. Whatever decides the look but is not visible text (a lamp's colour, which row is selected, which option is chosen) is a field of the entry, so the repository can hand the product the same values. A page whose controls change what it shows or send a request also loads, from `data/`, the backend-shaped data its entries were computed from, one entry per `scene` value under the same names: the product's own logic runs on that data when its controls are checked. An `App · ` page passes its `scene` down to the pages it shows.

## `$preview`

Every `Component · ` and `App · ` page declares `$preview` in `data-props` with `width` and `height` as positive integers: the size each scene is rendered and checked at. A `Component · ` page shown on an `App · ` page takes the size its region occupies there, so the region is checked at the size the product shows it.

## `data-ui`

Every control that can be clicked or typed into, and every element whose look will be checked, carries `data-ui="<region>.<part>"`, where `<region>` is the name of the `Component · ` page it belongs to. The page's root element (the first element inside `<x-dc>`, outside `<helmet>`) carries `data-ui="<region>.root"`, and an `App · ` page's root `data-ui="<name>.root"` with its own name: the product's region is compared from that element down. Repeated parts of a list share one id. An `App · ` page repeats the ids of the `Component · ` pages it shows (a `dc-import` of those pages does this by itself); no two `Component · ` pages use the same `<region>`.

`ui-ids.md` at the project root, when present, lists the ids the product already carries. When a page is drawn for such a product, each of those ids goes on the element that means that part.

When a page is edited, an existing `data-ui` stays with the element that still means that part; it goes only when that element is deleted. The ids are how the repository recognises a control across edits.

When a page passes `scene` down to a `dc-import`ed child, the child's `renderVals()` does not return a key named `scene`.

## `task.md`

`task.md` at the project root, when present, is the work the repository's agent has set for this project now. When the user says to start or continue, do what it says, tick each item in it as you finish it, and ask the user where a choice is unclear. It never overrides the conventions in this file.

## Files

A page loads only files inside this project (the bound design system is under `_ds/`), so it renders the same after it is pulled. It loads no product code: its look comes from the design system and its own markup.
```
