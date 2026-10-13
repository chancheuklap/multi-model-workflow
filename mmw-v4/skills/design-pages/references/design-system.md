# A. Build a design system

Claude Design's own agent builds and compiles the design system. This session prepares its instructions and checks its result. Each product has its own design system.

1. **Choose the source.** Use an existing product's production code, a new product's winning prototype code, or the pages the owner signed off while exploring in Claude Design. When the page project is already bound to a design system that matches the code, tell the owner and end this part.
   Done when you know the source, or have told the owner that no design system is built this time.
2. **Get the project.** The owner creates the design system in Claude Design and gives its link; its id is the UUID in that link. `list_design_systems` does not list it.
   Done when you hold its id.
3. **Write its `CLAUDE.md`.** Copy the fenced block of [template-design-system-claude-md.md](template-design-system-claude-md.md), filling only the product, source, and example data fields. Name the source repository, pushed branch, and front-end directory. Use the skill's shared project-write procedure.
   Done when `CLAUDE.md` is written with all three fields filled and the rest unchanged.
4. **Hand it over.** Tell the owner to open that project and say `开始`. Its agent extracts colours, fonts, and parts, unifies inconsistencies, and records each unification in the `Unifications` table at the end of `readme.md`. The owner answers its questions there.
   Done when the owner says the work is done.
5. **Check it.** Read `readme.md` and use `render_preview` to inspect every card. Every card must open without errors, none may be a whole page region, and `readme.md` must end with `Unifications`. Put defects into `task.md`, one checkbox per defect, using the shared project-write procedure. Tell the owner to say `继续`, then check again when they say it is done.
   Done when every card passes and `readme.md` ends with the table.
6. **Have the product follow the table.** Each `Unifications` row is a product change. Run the `mmw-mode` skill's To spec and To tickets playbooks to send those changes through a night.
   Done when the spec is open, or the table is empty.
7. **Refresh after a design system change.** A bound page project's copy under `_ds/<folder>/` does not follow by itself. Use `list_files` on both projects, `delete_files` for files the design system no longer has, and `copy_files` with `src_project_id` set to the design system. Refresh its styles, readme, variables, parts, fonts, and icons. Then open [C](pull.md) to repull pages already in the design package, excluding pages listed in other `tasks/` sheets without a top `Pulled:` line. Pulled sheets do not reserve pages, even with unticked items.
   Done when every bound project's copy matches the design system and C has finished for the eligible pages.
