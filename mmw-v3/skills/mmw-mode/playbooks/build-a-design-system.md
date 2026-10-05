### Build a design system

**You own one design system: whether it is worth building and from what, its project's `CLAUDE.md`, the build handed to the agent inside Claude Design, and what that agent made checked.** That agent builds it, since only it compiles a design system; this session prepares what it reads and checks what it made. It cannot see this conversation, reads the repository only through Claude Design's GitHub connection, and reads its project-root `CLAUDE.md` on every conversation. What a design system is and holds is the `design-pages` skill's `## A design system`; read it before step 1. Distinct from Design in Claude Design, which draws the pages a design system is used for.

1. **Check the tools,** as the `design-pages` skill's `## Who can do this work` says.
   Done when the Claude Design tools answer, or the owner has been told this session cannot do the work.
2. **Decide whether to build one, and from what.** A design system is built from a look that already exists, and a new product has none of these sources at its start:

   | The product is | Build it from | When |
   | --- | --- | --- |
   | an existing product | its production code | before its first page is drawn in Claude Design; once |
   | new, with a prototype | the winning variant's code | after the owner picks the winner, before the page project is opened |
   | new, its look explored in Claude Design | the pages the owner signed off | after sign-off, before more pages are drawn |

   Skip it for a one-page change, or when the page project is already bound to a design system that matches the code; tell the owner, and this playbook ends here.
   Done when you know the source, or that none is built now.
3. **Get the project.** The owner creates the design system in Claude Design and gives its link; its id is the UUID in that link. `list_design_systems` does not list it.
   Done when you hold its id.
4. **Write its `CLAUDE.md`.** The fenced block of the `design-pages` skill's `references/template-design-system-claude-md.md`, with its three fields filled: the product, the source (the repository URL, branch and directory of the front end, with that branch pushed), and the example data. `finalize_plan` naming `CLAUDE.md` in `writes`, which the owner approves, then `write_files` with `if_match: "0"`.
   Done when `CLAUDE.md` is written with every field filled.
5. **Hand it over.** The `CLAUDE.md` is itself the task. Tell the owner to open the design system in Claude Design and say `开始`; they answer its questions about unifications in that conversation and tell you when it is done.
   Done when the owner has said it is done.
6. **Check it.** `list_files` and `read_file` its `readme.md`; `render_preview` each card and look at it. It is done when every card renders with no console error, no card is a page region, and `readme.md` ends with the `Unifications` table. Write what fails into the project's `task.md`, one checkbox item per defect naming the card or file and what is wrong (`finalize_plan` and `write_files` as in step 4, and as the `design-pages` skill's `### Talking to the agent inside Claude Design` says), tell the owner to say `继续` there, and check again when they say it is done.
   Done when every card passes.
7. **Refresh the page projects bound to it,** as the `design-pages` skill's `### After the design system changes` says, whenever it changed after a page project was bound to it.
   Done when every bound page project's `_ds/<folder>/` matches the design system, or none is bound.

**An existing product.** Its screens are brought into Claude Design once, redrawn with its design system, and from then on they are designed there. This playbook builds the design system from the production code, unifying what the code does inconsistently. Then **Design in Claude Design** runs with the project bound to it: the state list written first under `## State list` in `prototypes/<effort>/README.md`; `task.md` asking for one `Component · ` page per region drawn from the design system, an `App · ` page when regions' states are checked together, and one region first; and each region's data file derived from the product's real data for those states, which the agent inside Claude Design reads from the repository, with `task.md` naming the directory. The real data lives in its own directory beside the design package (`prototypes/<effort>/example-data/`), never inside it. Sign-off and **Pull a design** follow as for any design. On the first pull the pages differ from the product wherever the design system unified a value, and the tickets cut from the screen contract bring the product to the design.

**Reply:** the design system's link; the source it was built from; the `Unifications` rows the owner settled; the cards that failed a check and whether they now pass; the page projects refreshed; and, for an existing product, that Design in Claude Design comes next.
