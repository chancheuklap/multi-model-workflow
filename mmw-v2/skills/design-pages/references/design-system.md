# design system — optional: the product's look as parts Claude Design builds pages from

A Claude Design design system is a separate project holding a product's colours, type, spacing, icons and components, each shown as a card in Claude Design's Design System tab. A page project bound to it gets a copy under `_ds/<folder>/`, and the user and the agent inside Claude Design draw pages from those parts instead of redrawing the look each time.

## What it is for, and what it is not

- **For Claude Design**: new pages come out in the product's real look, and the agent inside Claude Design has the components to mount rather than guessing at colours and spacing.
- **Not for acceptance**: nothing in the repository reads the design system. [pull](pull.md), the screen contract and the story judge work from the pulled pages and the running product, however the pages were built. The one link: a component a page mounts must set on its elements the `data-ui` ids the page gives it, because the ids on the rendered page are what acceptance reads.

## When

- **Build one** when the look already exists in code (a live product, or a prototype's winning variant) and more than a page or two will be drawn against it.
- **Skip it** for a one-page change, while the look is still being explored (draw first; build it from the winner afterwards), or when the project is already bound to a design system that matches the code.

It is not a gate: pages can be drawn and pulled with no design system. When one is built, build it before the page project is first opened in the browser, because that first opening is when Claude Design copies it in.

## Two ways to build it

1. **In Claude Design, by the user**: create a design system there and give its agent the code (a GitHub connection or uploaded files). Claude Design builds and compiles it itself, and MMW has no step in it. Not yet run end to end on one of this toolbox's products.
2. **From here, when the user asks this session**: the steps below. The directory in the repository is then the design system's source, and the copy in Claude Design is what pages use.

## Building it from here

`<scripts>` is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**. The code it is built from: a prototype's winning variant, or the style variables and shared components of the running product. Extracted values are reviewed before they become the standard; current defects are not copied in as rules.

Claude Design's shape for a design system (its own design-system instructions and the built-in Classical system, checked 2026-09-21), which `check_design_system.py` checks:

- `styles.css` at the root, made of `@import` lines only, reaching the token files (custom properties on `:root`), the `@font-face` rules with their font files, and the component stylesheets.
- `readme.md` with the headings `Sources`, `CONTENT FUNDAMENTALS`, `VISUAL FOUNDATIONS`, `ICONOGRAPHY`, `Index` and `Intentional additions`.
- Twelve or more foundation cards: HTML files whose first line is `<!-- @dsCard group="…" viewport="700x<height>" name="…" subtitle="…" -->`, split by sub-concept.
- Components: `<Name>.jsx` exporting `function <Name>` (React), `<Name>.d.ts` with the props, `<Name>.prompt.md` with what, when and an example; one `@dsCard` card in group `Components` per component directory.
- One directory per product surface under `ui_kits/`, with an `index.html` tagged `@dsCard`. A screen tagged `<!-- @startingPoint section="…" subtitle="…" viewport="WxH" -->` seeds new pages; it is optional.
- `SKILL.md` with `name` and `description` frontmatter. Assets copied from the source, never drawn.

Built from code for this toolbox, the components also follow the source closely: the same elements, class names and nesting the source renders, styled by the source's own CSS, values and font files copied exactly; and each takes a `data-ui` prop, sets it on its root, and sets `<data-ui>.<part>` on the parts a page's acceptance reads (the `.d.ts` declares it; the check requires that).

1. **Write the directory** `prototypes/<task>/design-system/` (`<task>` as the `prototype` skill's rule 1 defines it). List every shared piece of markup the code renders, with its source file, before writing any of it; the inventory is the source's, none added and none left out.
2. **Check it**: `<scripts>/check_design_system.py prototypes/<task>/design-system`. Done when it prints `design system complete`.
3. **Create the design system in Claude Design**: the design-sync tool's `create_project` (it returns `projectId`); read the namespace from the `window.` name in the first lines of its placeholder `_ds_bundle.js` (`read_file`).
4. **Bundle**: `<scripts>/build_ds_bundle.py prototypes/<task>/design-system --namespace <Namespace>`, so pages can mount the components before Claude Design compiles its own bundle in step 6.
5. **Upload** with the design-sync tool: `finalize_plan` (writes: the directory's paths; deletes: `_ds_manifest.json` when the new project has one; `localDir`: the directory), `write_files` by `localPath`, then `delete_files` for the manifest. File bytes never pass through the model.
6. **Compile**: ask the user to open the design system once in the browser. With no `_ds_manifest.json` present, Claude Design compiles on that opening: it fills the Design System tab and writes its own `_ds_bundle.js` and `_ds_manifest.json` (observed 2026-09-21; writing files from outside, reading the design prompt or creating a bound project did not trigger it).
7. **See it**: `render_preview` of one component card; it renders with no console error. The `projectId` is what [edit pages](edit-pages.md) binds a page project to; `list_design_systems` lists only published systems, so it will not appear there.

## After the design system changes

From here: change the code, then the directory, and run steps 2 to 6 again (step 5 deletes the manifest Claude Design wrote, so step 6 compiles again).

A page project's `_ds/<folder>/` copy does not follow the design system. `copy_files` with `src_project_id` set to the design system can copy its files over that folder; not yet run against a live project. Pull again after the copy changes.
