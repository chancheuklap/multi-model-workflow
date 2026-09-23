# design system — a product's look, built in Claude Design by its own agent

A Claude Design design system is a separate project holding a product's variables, fonts, icons and reusable parts, each part one class name with its variants and one card showing every state. A page project bound to it gets a copy under `_ds/<folder>/`, and its pages are drawn from it. What it holds and does not hold is the block of [template-design-system-claude-md.md](template-design-system-claude-md.md).

## What it is for

No judge compares against the design system: pull brings in only its `readme.md`, for the `Unifications` table the product's code follows, and the story judge works from the pulled pages. It is not a step every design must pass through.

## When, and from what

A design system is built from a look that already exists. There are three sources, and a new product has none of them at its start:

| The product is | Build it from | When |
| --- | --- | --- |
| an existing product | its production code | before its first page is drawn in Claude Design; once |
| new, with a prototype | the winning variant's code | after the user picks the winner, before the page project is opened |
| new, its look explored in Claude Design | the pages the user signed off | after sign-off, before more pages are drawn |

Skip it for a one-page change, or when the page project is already bound to a design system that matches the code.

## Who builds it

The agent inside Claude Design builds it; this session prepares what it reads and checks what it made. That agent cannot see this conversation, and it reads the repository only through Claude Design's GitHub connection (step 3). Otherwise what it reads is the files in its own project, and it reads the project-root `CLAUDE.md` on every conversation.

1. **The project**: the user creates the design system in Claude Design and gives its link; its id is the UUID in that link. `list_design_systems` does not list it.
2. **Its `CLAUDE.md`**: `finalize_plan` naming `CLAUDE.md` in `writes` (the user approves), then `write_files` with `if_match: "0"`. The content is the fenced block of [template-design-system-claude-md.md](template-design-system-claude-md.md) with its three fields filled: the product, the source (the repository URL, branch and directory of the front end), and the example data.
3. **The source code**: the agent inside Claude Design reads it through Claude Design's GitHub connection, from the repository, branch and directory `CLAUDE.md` names.
4. **Hand over**: the `CLAUDE.md` is itself the task. Tell the user to open the design system in Claude Design and say `开始`; they answer its questions about unifications in that conversation and tell you when it is done.
5. **Check it** when the user says it is done: `list_files` and `read_file` its `readme.md`; `render_preview` each card and look at it. It is done when every card renders with no console error, no card is a page region, and `readme.md` ends with the `Unifications` table. Write what fails into the project's `task.md`, one checkbox item per defect naming the card or file and what is wrong (`finalize_plan` and `write_files` as for `CLAUDE.md`), and tell the user to say `继续` there.

## After the design system changes

Changes are made in Claude Design, by the user or by its agent. After a change, refresh each bound page project as [edit pages](edit-pages.md) **After the design system changes** says.

## An existing product

An existing product's screens are brought into Claude Design once, redrawn with its design system, and from then on they are designed there.

1. **Design system**: built from the production code as **Who builds it** above says, unifying what the code does inconsistently.
2. **Project**: [edit pages](edit-pages.md) **Create the project**, bound to that design system, with `state-list.md` (one `### <region>` per region, one item per state the product shows). Write the state list first under `## State list` in `prototypes/<effort>/README.md`, with `<effort>` as the `prototype` skill's rule 1 defines it; that file is the `--state-list` of [pull](pull.md). The agent inside Claude Design derives each region's data file from the product's real data for those states, which it reads from the repository through Claude Design's GitHub connection; `task.md` names that directory. The real data lives in its own directory beside the design package (`prototypes/<effort>/example-data/`), never inside it: each pull rewrites the design package to exactly the files the pages load.
3. **Redraw**: `task.md` asks the agent inside Claude Design to draw one `Component · ` page per region from the design system, and an `App · ` page when regions' states are checked together, first one region for the user to look at; see [edit pages](edit-pages.md) **Talking to the agent inside Claude Design**.
4. **Sign-off and pull**: as for any design. On the first pull the pages differ from the product wherever the design system unified a value; element parity names each of those elements, and the tickets cut from the contract bring the product to the design.

Done when the user has signed off the redrawn pages and [pull](pull.md) has run.
