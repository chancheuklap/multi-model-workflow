# design system — built here from running code, before any page is drawn

The design system exists before the first page is written. Its source is code that already runs, never a reverse extraction of a rendered product. It is a Claude Design design system in full, as **What Claude Design requires** lists, with the rules of **What MMW adds** on top. You build all of it here and upload it; nothing in this entry waits on the user.

## Which code

- **A new product, or a remake that changes the look** — the prototype's winning variant; on a wayfinder map, the winners the state list gathers (the `prototype` skill's `UI.md` step 6). After the product ships, later changes take the product code as the source.
- **An existing product that keeps its current look** — the style variables and shared components (button, badge, banner, dialog, and the like) already in the product. Extracted values are reviewed before they become the standard; current defects are not copied in as rules. Skip this entry when a design system already exists and those shared components have not changed.

A remake is a new interface that does **not** keep the old look. An interface that keeps the old look is the existing-product case, even if the rest of the product is being rewritten.

## What Claude Design requires

Taken from Claude Design's own design-system instructions and the built-in Classical system (checked 2026-09-21). A design system missing any of these shows gaps in Claude Design itself: an empty Design System tab, no components for pages to mount, nothing to start a page from.

- `styles.css` at the root, made of `@import` lines only. It reaches the token files (custom properties on `:root`: base values and semantic aliases), the `@font-face` rules, and the component stylesheets. The font files those rules name ship with it.
- `readme.md` with the headings `Sources`, `CONTENT FUNDAMENTALS` (how copy is written), `VISUAL FOUNDATIONS` (colour, type, spacing, backgrounds, motion, hover and press states, borders, shadows, radii, cards), `ICONOGRAPHY`, `Index` (the files, components and UI kits) and `Intentional additions` (every component the source does not define, with its reason, or "None").
- Foundation cards: small HTML files whose first line is `<!-- @dsCard group="…" viewport="700x<height>" name="…" subtitle="…" -->`, each linking `styles.css`. Twelve or more, split by sub-concept (primary, neutral and status colours apart; each type family apart; spacing, radius, elevation apart).
- Components: `<Name>.jsx` with `export function <Name>` (React only), `<Name>.d.ts` with the props, `<Name>.prompt.md` with what, when and a usage example; one `@dsCard` card in group `Components` per directory that mounts them from `_ds_bundle.js`. The inventory is the source's, complete: every family it defines, none it does not.
- UI kits: one directory per product surface under `ui_kits/`, an `index.html` tagged `@dsCard` recreating the real screens from the components. A screen that seeds new pages is its own HTML file whose first line is `<!-- @startingPoint section="…" subtitle="…" viewport="WxH" -->`.
- Assets copied from the source, never drawn; an icon set the source loads from a CDN is named, not redrawn.
- `SKILL.md`, the design system as an agent skill for download (frontmatter `name`, `description`).
- `_ds_bundle.js`, the components as one script that sets `window.<Namespace>.<Name>`. Claude Design's compiler writes it only inside its own design-system chat; from here, `build_ds_bundle.py` writes it, as the design-sync command does for React. `_ds_manifest.json` and `_adherence.oxlintrc.json` are Claude Design's own and never written here.

## What MMW adds

1. **A component renders the source's own DOM**: the same elements, class names and nesting the source code produces, styled by the source's own CSS rules in a stylesheet `styles.css` imports. A design page built from components and the product built from the same code then compare element to element under the story judge.
2. **A component takes a `data-ui` prop**, sets it on its root, and sets `<data-ui>.<part>` on each part a page's acceptance reads. A page gives each component its id; the component stamps its own parts.
3. **One `@startingPoint` screen per region of the state list**, in the UI kit, at the region's page size, so a `Component · ` page and the region it starts from agree.
4. **Values copied exactly** (pixels, colours, line heights), font files copied from the source, never substituted.

## Who does what

| | Reads | Writes | Cannot |
| --- | --- | --- | --- |
| This session | the repository; any Claude Design project through MCP (`list_files`, `read_file`, `get_conversation`, `list_comments`) | any project through MCP and the design-sync tool, by path or from disk (`localPath`) | talk to the agent inside Claude Design; switch a design system's "Published" toggle |
| The agent inside Claude Design | its own project and the bound design system; GitHub when the user connects it | its own project, when the user asks it in the browser | read this repository's working tree, MMW's state, or this session |
| The user | everything in the browser | edits, comments, sign-off | (nothing this entry needs) |

So every step below is this session's. The agent inside Claude Design first matters in [edit pages](edit-pages.md), when the user asks it to change a page, and it follows the project `CLAUDE.md` there.

## Steps

`<scripts>` is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**.

1. **Write the directory** `prototypes/<task>/design-system/` (`<task>` as the `prototype` skill's rule 1 defines it) from the code, meeting both lists above: `tokens/`, `fonts/`, `components/<group>/`, `guidelines/`, `ui_kits/<surface>/`, `assets/`, `readme.md`, `SKILL.md`. Enumerate the component inventory first, every shared piece of markup the code renders, with its source file; build all of it.
2. **Check it**: `<scripts>/check_design_system.py prototypes/<task>/design-system`. Done when it prints `design system complete`.
3. **Create or reuse the design system in Claude Design**: the design-sync tool's `create_project` for a new one (it returns `projectId`); read the namespace from the `window.` name in its placeholder `_ds_bundle.js` (`read_file`).
4. **Bundle**: `<scripts>/build_ds_bundle.py prototypes/<task>/design-system --namespace <Namespace>`.
5. **Upload** the directory with the design-sync tool: `finalize_plan` (writes: the directory's paths; `localDir`: the directory), then `write_files` by `localPath`. File bytes never pass through the model.
6. **See it**: `render_preview` of one component card and one starting-point screen in the design system; each renders with no console error. The `projectId` is the id [edit pages](edit-pages.md) binds; `list_design_systems` lists only published systems, so do not look for it there.

The directory in the repository is the design system's source; the copy in Claude Design is what pages use. Change the directory, check, bundle and upload again; nothing is edited in Claude Design by hand.

## After the values change

Change the source code, then the directory, and run steps 2, 4 and 5. A page project's `_ds/` copy does not follow: upload it again (edit pages, **Create the project** step 4), then [pull](pull.md).

`_adherence.oxlintrc.json` is not a check this skill runs: the agent inside Claude Design has no linter, and those rules do not reach CSS in a `.dc.html` `<style>` block.

## Next

[edit pages](edit-pages.md).
