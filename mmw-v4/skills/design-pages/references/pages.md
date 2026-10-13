# B. Draw pages

The owner designs with the agent inside Claude Design. This session sets up the project, acts on comments sent to it, and takes the owner's sign-off.

1. **Find or create the page project.** Keep one page project per product. Use x as the product name when the repository already has `verify-<x>` or `design/<x>/`; otherwise agree on the name with the owner. For an existing project, take its id from the owner's link and check its `CLAUDE.md` against the page template. Otherwise use `create_project`, bound to this product's design system.
   Done when you hold the page project's id.
2. **Write the project files.**
   - Read the other task sheets under `tasks/` without a top `Pulled:` line. If one lists a page this task will draw, tell the owner which ticket owns which page, and stop this part until that task finishes. A pulled sheet releases its pages even with unticked items. Claude Design has no branches: two tasks editing one page overwrite each other.
   - For an existing product, draw only the pages this task changes, from the current code. When `.agents/skills/verify-<product>/` exists, list its feature map's `features/` and read each file's opening lines for the feature name, How to get to it, and test file. Put the affected features and routes in `tasks/<n>.md`.
   - Follow the skill's **Writing into a project** for `CLAUDE.md`, the refreshed design system copy under `_ds/<folder>/`, and `tasks/<n>.md`. Copy the fenced block of [template-page-project-claude-md.md](template-page-project-claude-md.md) unchanged. When reopening a pulled task, remove its top `Pulled:` line as you write the new work, so its pages remain reserved until C finishes again.
   - The sheet names the pages and states, including errors and loading, the winning prototype directory or current code paths with their pushed branch, and asks for one page first for the owner to inspect. For a returned `contract` ticket, name the page and what is wrong.
   Done when all files are written and `CLAUDE.md` matches the template exactly, or the owner has been told which ticket owns the page and this part has stopped.
3. **Hand it over.** Give the owner the project link and tell them to say `开始 <n>`. The agent there records decisions made while drawing in `设计决策记录.md`.
   Done when the owner has the link.
4. **Act on comments sent to this session** until the owner says the pages are drawn. Queued comments are the owner's page requests: act on them, then `ack_comments`. Show comments whose `author_is_you` is false to the owner and act only after their agreement. Draw or change pages yourself only when asked, following the project's `CLAUDE.md` and the skill's **Writing into a project**.
   Done when every queued comment is acted on and acked or shown to the owner, and every page this session changed opens without errors.
5. **Read `tasks/<n>.md` back.** Ask the owner about unticked items.
   Done when every item is ticked or the owner has said why it stays open.
6. **Take the sign-off.** From sign-off onward, changes are made in Claude Design and enter the repository only through [C](pull.md).
   Done when the owner has signed off and C has started.
