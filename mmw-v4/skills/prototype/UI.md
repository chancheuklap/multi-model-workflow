# UI Prototype

Build a complete, interactive local prototype in the product's own code. The owner tries it in the real app and iterates with you. When the direction is open, compare structurally different variants with a floating bottom bar. Keep the winner and the other variants as reference for implementation.

If the question is about logic/state rather than what something looks like, this is the wrong branch. Use [LOGIC.md](LOGIC.md).

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

Check for both the product's environment tools and its `verify-<product>` skill here, once for the workflow. The environment tools belong in the product repository's development scripts, with an operating skill. They start the whole local product with a backend and database per checkout and create test accounts. The verification skill's Launch calls those tools rather than carrying its own environment scripts.

For a supported surface, use the **create-verification-skill** skill alongside this authorized prototype to supply missing environment and verification tools, then return here. Keep the original effort branch and authority. A prerequisite requiring credentials or a product decision returns that specific need to the caller; an unsupported surface is reported before generation.

Work on the effort's branch and worktree from the project branch. On the map route, this is the night's branch, reused across the effort's specs. Outside a map, keep the caller's effort branch; an independent ticket uses `fix-<n>`. Commit the environment tools, verification skill, prototype, feature files, and tests there, to enter the project branch with the effort's accepted PR.

Done when the effort checkout is ready and, for an existing product, its local environment and verification tools are available.

### 1. State the question and pick N

Apply **principle-experience-first** when choosing the UI direction and scope. When the structural direction is open, default to 3 variants, capped at 5. State the question and the directions to compare. When the direction is settled, continue the current UI instead of generating another set.

Done when the current question and the directions still open are explicit.

### 2. Wire them together

Keep one prototype in `efforts/<effort>/prototypes/<issue>/UI/`. If an earlier standalone prototype came from elsewhere, move it here and retire that copy. Do not keep synchronizing two copies. If prototype code cannot meet repository lint rules, exclude the prototype directory from lint rather than changing the rules. Implementation rewrites the code to meet them.

The product's own launch command plus one environment variable starts the prototype, including Electron. The mount point renders prototype code only with that variable enabled. Render `winner/` by default, and the product's own page until `winner/` exists. Register one `?variant=` key per candidate directory before the candidates start, fixing the entry file and exports the mount point imports from each directory; a key whose code has not loaded shows a placeholder. The `?variant=` URL search param lets the owner browse the other variants, rather than enabling the prototype itself.

Keep the variants in the leaf directory. The product route or rendering module holds only the mount point importing them. Use a path alias, relative import, or a symlink beside the route when the project cannot import across that boundary. Keep the mount point and any symlink until implementation, not just until selection.

Done when the normal launch command with the environment variable renders the prototype in its final location and the ordinary launch renders the product.

### 3. Build the floating switcher

Put one shared switcher under `efforts/<effort>/prototypes/`, beside the leaf directories. Use a small fixed-position bar at the bottom-centre of the screen with:

- A left arrow that cycles to the previous variant and wraps around.
- A label showing the current variant key and name, when named.
- A right arrow that cycles forward and wraps around.

Update `?variant=` through the framework's router so links are shareable and reload-stable. Let the left and right arrow keys cycle too, except when an input, textarea, or contenteditable element has focus. Make the bar visually distinct from the page being judged, and show it only with the prototype environment variable enabled. The winner runs without a variant selection.

Done when the owner can switch variants on the real pages without interfering with text input.

### 4. Generate radically different variants

Write every variant, yours or a candidate's, as `references/ui-variant.md` says.

For competing directions, run the **arena** skill. Each candidate writes one variant into `candidates/<n>/` within this checkout's leaf directory; its `## Task` names the **prototype** skill's `references/ui-variant.md`. The owner chooses the base, not the score. Each candidate's brief names under `## Known` its directory `candidates/<n>/`, the entry file and exports the mount point imports from that directory, the URL that renders its variant (`?variant=<n>`), and the grounding paths to the mount point and the environment tools' product-test seed data. Name the page's existing component and feature file when they exist. Give each its own running instance when Launch's isolation requires it. If the product has no backend stack and the page reads on every request, candidates can share the instance you started. For a simple page, draft the alternatives yourself without arena.

Bring questions from the candidates' rationales that would change the UI alongside the variants for the owner to settle during selection, rather than registering them as separate problems.

Done when every variant meets `references/ui-variant.md`'s Done criterion.

### 5. Hand it over and iterate

Give the owner the URL and variant keys. The owner operates the page, chooses a direction or combination, and gives feedback. Do not choose or accept it for them. Fuse the selected parts into `winner/` and retain the other variants in `candidates/<n>/` for later reference. Post arena's synthesis note as a comment on the ticket that asked the question; with no ticket, the reply carries it.

Once the direction is settled, work one to one with the owner. Ask one question per round, edit the same prototype in place, and commit each round. Do not send a worker or reviewer. Do not generate a whole new set of designs. If one component remains uncertain, use a small arena just for it.

Go through every API fake call and list where each button connects. Identify what the prototype cannot answer behind that interface: data and storage, interface fields and errors, business rules, permissions and security, failure and recovery, external systems, scale and performance, account or key preparation, and Electron native behavior. Settle these through the relevant grilling, domain-modeling, research, LOGIC, or EXP work, not from the UI alone.

Settle questions that change the UI during iteration and update the prototype with the answers. On the map route, open decision tickets under the map. Outside a map, record the owner's answers on the existing ticket, then make each an item under **What to build** when writing the ticket. Record owner decisions in those tickets, not a separate design-decision log. Questions that do not affect the UI can wait until after design freeze.

Done when the owner has chosen the direction, the winner reflects the iteration's answers, and every button's connection and UI-affecting decision is accounted for.

### 6. Capture the answer at design freeze

1. Merge the latest project-branch code so the prototype runs on the current product.
2. Read every closed decision and compare its visible rules with the prototype. On the map route, read the map's closed child tickets. Outside a map, read the owner's answers on the ticket and its cited specification sections. List what is displayed or marked, who sees each button, and what errors say. Find each rule in the prototype and add missing ones. Give states that actions cannot create, such as concurrent-save conflicts, a state URL. Leave invisible storage and computation rules for the spec.
3. Write the feature file's account of what the product can do with the **create-verification-skill** skill's `## 3. Seed the feature map`. Every sentence has a source in the winner, closed decisions, or glossary `CONTEXT.md`, and describes behavior the prototype demonstrates. Use the product UI's language, retaining the format's English headings.
4. When the sources disagree, decisions govern rules, the glossary governs names, and the prototype governs appearance and interaction. Fix a prototype that lags behind decisions or the glossary. Settle unrecorded questions that change the UI by the iteration rules above, then update the prototype. Do not ask the owner to reconcile the written sources.
5. The owner says "That's it" on the real page. This is design freeze, the single approval of the prototype. Do not ask them to approve the feature file's sentences too.
6. Commit that part of the feature file before writing tests. Only the environment tools, mount point, and prototype precede it on the effort branch.

The UI conclusion lives in the feature file. Hand back the winner's exact path and the feature file. The interface contract starts from the API fake and is finalized during spec or independent-ticket preparation. Once finalized, update the API fake to match it before writing tests.

Keep the mount points until implementation. The final ticket removes them after all slice tickets. For a single ticket, removal is its last commit. In an effort with multiple specs, a later spec's mount points may enter the project branch with an earlier PR and stay until that spec lands. Tests use the same steps and assertions for the normal launch and the launch with the prototype variable. Removing a mount point reveals the product page without changing tests.

Done when the owner has approved the running winner, the feature file's account is committed before tests, and the winner remains runnable for implementation to follow.

## Anti-patterns

- **Promoting the prototype directly to production.** Copy the winner's appearance and interaction, and rewrite its code to production standards.
