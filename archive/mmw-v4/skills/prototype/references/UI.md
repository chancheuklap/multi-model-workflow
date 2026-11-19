# UI Prototype

Build or update the complete, interactive local prototype the caller requests, using the product's own code. Return runnable pages, candidate questions and the exact files. The Design a UI playbook owns the owner's selection, iterative feedback and design freeze; a request for candidates alone ends with the candidates. Keep the current effort, winner and settled choices.

For a recorded owner choice, update winner/ with only the selected parts and retain candidates/<n>/. Use the arena skill's Pick, Graft and Verify phases for its recorded selection and synthesis note; do not ask the owner to choose again. For later feedback, update that same winner rather than starting a new comparison. Production implementation copies its appearance and interaction and rewrites its code to production standards.

If the question is about logic/state rather than appearance, use [LOGIC.md](LOGIC.md).

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- Any time the user would otherwise spend a day picking between three vague mockups in their head.

## Two sub-shapes: strongly prefer sub-shape A

A UI prototype is easier to judge beside the real header, sidebar, data, and page density. Default to sub-shape A whenever an existing page can host the variants. Use sub-shape B when the prototype has no nearby home.

### Sub-shape A: adjustment to an existing page (preferred)

Mount the variants on the existing route, keeping the surrounding app, data fetching, params, and auth. Only the part being prototyped changes. A new section, card, or step inside an existing flow belongs here too.

### Sub-shape B: a new page (last resort)

Use this for a new top-level page or a flow that cannot fit inside an existing page. Mount it on its final route, following the project's routing convention, rather than inventing a prototype-only route.

In both sub-shapes, put the mount point on the feature file's final `Route:`. For a panel or dialog without its own route, put it in the module that renders it. For several pages, mount each page separately and share one switcher. Remove mount points page by page during implementation, so each removal reveals that page's product implementation.

### When there is no app yet

A brand-new product has no route to host the variants and no routing convention to follow, so neither sub-shape applies. The variants are standalone pages in the leaf directory `efforts/<effort>/prototypes/<issue>/UI/`, built with the stack the effort has decided, sharing one switcher. Nothing outside the leaf directory mounts them. The first implementation ticket is a smoke ticket that builds the product skeleton from the prototype; the other tickets depend on it.

### Separate repositories and Electron

For a frontend and backend in separate repositories, keep the prototype in the frontend repository. Run the backend spec first and merge it before the frontend spec's night, so frontend tests do not intercept unimplemented interfaces. For Electron, prototype the renderer and fake missing preload bridge methods. Native dialogs, menus, and tray behavior need separate decisions and product-target tests.

## Process

### 0. Prepare the local product

Keep the caller's preparation record and effort worktree. A direct UI-candidate request with no record or effort branch first uses the **to-tickets** skill's **Open the preparation record** entry, scoped to producing those candidates. Record the candidate question as the goal; include a Playbook line only for an actual calling playbook. Reuse an existing record and create only the branch it lacks. This opens a preparation record, not an implementation ticket, and does not authorize the rest of Design a UI or a worker. Return only the candidates the request asked for.

Read the product's existing environment instructions and the caller's preparation results. Reuse a runnable local environment. If the environment needed by this prototype is missing, call the **create-verification-skill** skill's **Prepare environment** entry with this product, checkout, chosen stack and current prototype scope. Continue here with its returned launch instructions and seed data. An unmet prerequisite returns to the caller.

This entry does not require a complete verify skill before it builds the UI. The ticket or specialist preparation step first needing missing reusable capability calls **create-verification-skill**, **Generate and prove**, directly. Independently requested generation returns its own result; candidate-only and design-only requests stop at their requested results.

Done when this checkout can run the product or standalone prototype needed by the current question, or the caller has its unmet prerequisite.

### 1. State the question and pick N

Apply **principle-experience-first** when choosing the UI direction and scope. When the structural direction is open, default to 3 variants, capped at 5. State the question and the directions to compare. When the direction is settled, continue the current UI instead of generating another set.

Done when the current question and the directions still open are explicit.

### 2. Wire them together

Keep one prototype in `efforts/<effort>/prototypes/<issue>/UI/`. If an earlier standalone prototype came from elsewhere, move it here and retire that copy. Do not keep synchronizing two copies. If prototype code cannot meet repository lint rules, exclude the prototype directory from lint rather than changing the rules. Implementation rewrites the code to meet them.

For a product without app code, use the standalone launch from Prepare the local product and register each candidate with its shared switcher. There is no product mount point or ordinary product launch to prove yet. The mount instructions below apply to an existing product.

The product's own launch command plus one environment variable starts the prototype, including Electron. The mount point renders prototype code only with that variable enabled. Render `winner/` by default, and the product's own page until `winner/` exists. Register one `?variant=` key per candidate directory before the candidates start, fixing the entry file and exports the mount point imports from each directory; a key whose code has not loaded shows a placeholder. The `?variant=` URL search param lets the owner browse the other variants, rather than enabling the prototype itself.

Keep the variants in the leaf directory. The product route or rendering module holds only the mount point importing them. Use a path alias, relative import, or a symlink beside the route when the project cannot import across that boundary. Keep the mount point and any symlink until implementation, not just until selection.

Done when an existing product's normal launch with the environment variable renders the prototype in its final location and its ordinary launch renders the product, or the new project's standalone launch renders the registered candidates.

### 3. Build the floating switcher

Put one shared switcher under `efforts/<effort>/prototypes/`, beside the leaf directories. Use a small fixed-position bar at the bottom-centre of the screen with:

- A left arrow that cycles to the previous variant and wraps around.
- A label showing the current variant key and name, when named.
- A right arrow that cycles forward and wraps around.

Update `?variant=` through the framework's router so links are shareable and reload-stable. Let the left and right arrow keys cycle too, except when an input, textarea, or contenteditable element has focus. Make the bar visually distinct from the page being judged, and show it only with the prototype environment variable enabled. The winner runs without a variant selection.

Done when the owner can switch variants on the real pages without interfering with text input.

### 4. Generate radically different variants

Write every variant, yours or a candidate's, as `references/ui-variant.md` says.

For competing directions, use the **arena** skill's **Frame** and **Fan out** phases to construct the candidates. Return the alternatives before picking; Design a UI or the recorded owner choice owns that decision. Each candidate writes one variant into `candidates/<n>/` within this checkout's leaf directory; its `## Task` names the **prototype** skill's `references/ui-variant.md`. The owner chooses the base, not the score. Each candidate's brief names under `## Known` its directory `candidates/<n>/`, the entry file and exports the mount point imports from that directory, the URL that renders its variant (`?variant=<n>`), and the grounding paths to the mount point and the environment tools' product-test seed data. Name the page's existing component and feature file when they exist. Give each its own running instance when Launch's isolation requires it. If the product has no backend stack and the page reads on every request, candidates can share the instance you started. For a simple page, draft the alternatives yourself without arena.

Return any candidate question that would change the UI alongside the variants, for the design caller to settle during selection rather than as a separate problem.

Done when every variant meets `references/ui-variant.md`'s Done criterion.

### 5. Return the runnable result

Open the product page or standalone prototype and verify the current construction against [ui-variant.md](ui-variant.md). Return its launch instructions, page and variant URLs, winner or candidate paths, the API fake and unresolved UI questions. Commit the construction and any arena synthesis note on the supplied effort branch. Candidate-only work stops here; the design caller resumes its owner interaction. Never start a worker or approve the design on the owner's behalf.

Done when the requested prototype is runnable, every relevant state and button meets the candidate criterion, and the caller has its files, URLs and remaining questions.
