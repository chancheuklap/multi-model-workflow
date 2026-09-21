# design system — a product's look, built in Claude Design by its own agent

A Claude Design design system is a separate project holding a product's visual vocabulary: variables (colour, type scale, weights, spacing, radius, shadow, borders), the fonts and icons, and the reusable parts (a button, a lamp, a pill, a list row, a card shell), each part one class name with its variants and one card in the Design System tab that shows every state. A page project bound to it gets a copy under `_ds/<folder>/`, and the pages are drawn from those variables and parts.

It holds no page regions (a whole title bar, a sidebar, a settings dialog: those are `Component · ` pages in the design project), no example data and no product logic. A part is a class name and its stylesheet, not a React component, unless the product itself is a React component library.

## What it is for

- **For Claude Design**: every page drawn in the product's project uses one look, and the agent inside Claude Design has named parts to compose instead of guessing values.
- **For the product**: when it is built from an existing product, inconsistent values in the code (three sizes for one kind of heading, two close buttons) are unified into one scale, and each unification is recorded; the product follows through element parity once pages drawn with it are pulled.
- **Not for acceptance**: nothing in the repository reads the design system. Pull, the screen contract and the story judge work from the pulled pages.

## When, and from what

A design system is built from a look that already exists. There are three sources, and a new product has none of them at its start:

| The product is | Build it from | When |
| --- | --- | --- |
| an existing product | its production code | before its first page is drawn in Claude Design; once |
| new, with a prototype | the winning variant's code | after the user picks the winner, before the page project is opened |
| new, its look explored in Claude Design | the pages the user signed off | after sign-off, before more pages are drawn |

Skip it for a one-page change, or when the page project is already bound to a design system that matches the code.

## Who builds it

The agent inside Claude Design builds it; this session prepares what it reads and checks what it made. That agent cannot see this repository or this conversation. What it reads is the files in its own project, and it reads the project-root `CLAUDE.md` on every conversation.

1. **The project**: the user creates the design system in Claude Design and gives its link; its id is the UUID in that link. `list_design_systems` does not list it.
2. **Its `CLAUDE.md`**: `finalize_plan` naming `CLAUDE.md` in `writes` (the user approves), then `write_files` with `if_match: "0"`. The content is the fenced block of [template-design-system-claude-md.md](template-design-system-claude-md.md) with its three fields filled: the product, the source (the repository URL, branch and directory of the front end), and the example data.
3. **The source code**: the agent inside Claude Design reads it through Claude Design's GitHub connection, from the repository, branch and directory `CLAUDE.md` names.
4. **Hand over**: the `CLAUDE.md` is itself the task. Tell the user to open the design system in Claude Design and say `开始`; they answer its questions about unifications in that conversation and tell you when it is done.
5. **Check it** when the user says it is done: `list_files` and `read_file` its `readme.md`; `render_preview` each card and look at it. It is done when every card renders with no console error, no card is a page region, and `readme.md` ends with the `Unifications` table. Write what fails into the project's `task.md`, one checkbox item per defect naming the card or file and what is wrong (`finalize_plan` and `write_files` as for `CLAUDE.md`), and tell the user to say `继续` there.

## After the design system changes

Changes are made in Claude Design, by the user or by its agent. A bound page project's `_ds/<folder>/` copy does not follow by itself; refresh it from here before the page project's agent draws again: `list_files` both projects, `delete_files` every file under `_ds/<folder>/` that the design system no longer has, and `copy_files` (with `src_project_id` set to the design system) of `styles.css`, `readme.md` and the variable, part, font and icon directories into `_ds/<folder>/`. Pull again after the copy changes.
