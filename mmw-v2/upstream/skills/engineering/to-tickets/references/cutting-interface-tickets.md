# Cutting interface tickets

The five kinds of ticket below are what a screen contract produces. An **interface ticket** is one whose **Read first** carries a `screen-contract.yaml rows:` line, as `verify-ticket.py --lint` reads it: the **component page ticket** and the **app page ticket**.

Copy each criterion from the named section of the `ui-acceptance` skill; the shape lives only there:

- A story criterion: `references/story-parity.md` § **The criterion, in one shape**.
- A boundary criterion: `references/boundary-check.md` § **The criterion, in one shape** and § **Selecting one row's test**. The product's test asserts the four columns of that row.
- A journey criterion: `references/journey.md` § **The criterion, in one shape**.

Each of these shapes is question 1 of **the five questions** in `SKILL.md`: a command decides it. Whatever else a ticket below wants said about the interface goes where questions 2 to 5 send it.

**A layer with no precedent yet:** a product from zero takes its adapter, its interaction helper and its first journey script, as the precedent, from the **contract ticket**. Cut that ticket first. The criteria of the tickets behind it copy their `CHECK:` and `EXPECT:` from what it lands. Nothing here sends you back to the `to-spec` skill for a precedent the spec cannot have.

## Seam and Owns on these tickets

**Seam** says where this ticket is verified and what puts the product into the state it is verified in. Each criterion shape above answers both, so a ticket's **Seam** names the ones its criteria use:

- A story criterion observes the product's story page for a mount, rendered with no backend behind it. The story adapter reading that scene's scene data is what puts the product there.
- A boundary criterion observes the product's own outbound call module, replaced for the test. The interaction helper acting on the row's `data-ui` id is what puts the product there.
- A journey criterion observes the real product, brought up by `start` in `.mmw/target.json`.
- The design-system criterion, the static-guard criteria and the harness-guard criterion observe the repository tree: a shell command reads the files, and nothing has to put the product anywhere.

**Seam** also names the precedent to copy: on a product from zero it is what the **contract ticket** lands, and a later ticket copies it rather than deriving its own.

**Owns** says where this ticket may write, so no design page is ever an entry there: the design package is a baseline under **Read first**, and the worker is forbidden to edit it. Translate the pages a ticket takes into product paths through the contract, whose `pages.<page>.component` names the directory the implementation owns each `Component · ` page under. Everything else follows step 5 of `SKILL.md`: the test files this ticket adds, and the files it must edit to put what it creates in service.

## design-system ticket

Cut one whenever the design package carries a design system under `_ds/<folder>/` whose variables or part stylesheets the product code does not yet have; otherwise each interface ticket writes the styles its component needs from the design pages. A design system built from an existing product's code counts: it merges inconsistent values into one scale and records each merge in its `readme.md` table `Unifications`, so copying it back changes the product. The ticket copies the variables (colour, type scale, spacing, radius, shadow), the fonts and the part stylesheets (each part a class name with its stylesheet) from `_ds/<folder>/` into the product code, keeping the class names. It sits ahead of the **contract ticket** and blocks it: the contract ticket's element parity precedent needs a component whose styles are already in the product. A batch with no contract ticket has it block every **component page ticket** and **app page ticket** instead. Its criterion does not depend on `.mmw/`.

**The design-system ticket is the second exception to vertical slicing**, beside the wide refactor `SKILL.md` step 3 names. It lands one layer, the styles, and demonstrates no behaviour of its own.

**Read first** names the `_ds/` copy in the design package, the design system Claude Design used to draw the pages. **Owns** is the product files the variables, fonts and part stylesheets land in.

Its criterion is one comparison, written under question 1 of **the five questions** in `SKILL.md`: a shell command that the design system's variables and part stylesheets exist in the product code. Whether those styles match the design system, value by value, is each later **interface ticket**'s element parity.

## contract ticket

An existing product: fill only what `target_config.py --check` of the `ui-acceptance` skill reports missing. That command sees whether each answer is there, not what it was built for: a story service or story adapter that reads a design package or scene shape other than the current one, an interaction helper that finds controls by anything but `data-ui` id, or a `start` without the break switch counts as missing too, and the spec's **How a test arrives at a state** says which. When something is missing, this ticket blocks the tickets that need those deliverables. When nothing is, cut none.

A new product: land `.mmw/` in full. It blocks every ticket in the batch except the **design-system ticket**. What it lands is the precedent later tickets copy.

What it delivers:

- the spec's **API contract** subsection turned into models and route signatures
- `.mmw/target.json`, including `harness_markers`
- the story service and the first story adapter
- the interaction helper that finds a control by its `data-ui` id
- this product's element parity precedent: one existing component made comparable, with the design page's `data-ui` ids written onto its elements and `[data-story-root]` on its root, rendered by the first story adapter; for a new product with no component yet, see below
- the static guards: the interface takes no fake data; `mount` is unique in one render; a `data-ui` id repeats only on the repeating part of a list
- the **break switch** under `.mmw/harness/`: `start` reads `MMW_BREAK` and the switch acts only on the product process
- the smoke journey
- the **harness guard**

Which of those carry a criterion follows **the five questions** in `SKILL.md`, and most do not. Question 1 reaches the smoke journey, one journey criterion on this ticket, and the static guards, one command each, on the batch's last ticket (below). The story service, the first story adapter, the interaction helper, the element parity precedent and the break switch carry none of their own: each is a precedent, and a precedent is first decided by a command on the ticket that copies it: the first **component page ticket** for the story service, the adapter, the interaction helper and the element parity precedent (next paragraph), the first **acceptance ticket** for the break switch. Whether any of them is built well is question 2, for the `Standards` and `Tests` axes of code review.

The contract ticket's **What to build** fixes each static guard's test file and case name; the last ticket's static-guard `CHECK:` runs that case with the repository's test runner, and its `EXPECT:` is the runner's success line.

The element parity precedent is written here and judged on the **component page ticket** that takes its component's page. This ticket writes the `data-ui` ids onto that component and builds the story adapter for its page, and its **Owns** lists those component files beside `.mmw/`. That component page ticket is blocked by this one, like every page ticket, and carries the story criterion and the boundary criteria of that page, which are the first commands to judge the precedent's ids and adapter. Its **Owns** lists the same component directory; the **Blocked by** edge orders the two, as step 5 of `SKILL.md` asks of two tickets writing one file. A new product with no component yet has nothing to make comparable here: its precedent is the component the first **component page ticket** builds. This ticket then delivers the story service, the story adapter shape and the interaction helper that ticket uses, and lists no component files under **Owns**; that first component page ticket's story criterion is the first command to judge them.

The **harness guard** and the static guards are delivered here and their criteria are not. Each sweeps the whole repository: no product module reads scene data, `mount` unique in one render, a `data-ui` id repeated only on the repeating part of a list, no acceptance name outside its allowed places. Step 4 of `SKILL.md` puts a sweep on the batch's last ticket, and every page ticket landing after this one adds components these sweeps read. Put the static-guard criteria and the harness-guard criterion on the batch's last ticket, which is the last **acceptance ticket** where the batch has one, and otherwise the last **app page ticket** or **component page ticket**. Only **Blocked by** makes a ticket last, so that ticket is blocked by every other agent ticket of the batch.

What every product answer must still guarantee is the `ui-acceptance` skill's `references/product-answers.md`. One product's shape is an example, not a requirement on the next.

The smoke journey uses the journey criterion and omits `--break`. It requires the product to come up and answer; it signs in when the product has a login. Its second pass is the product-down pass that section already names. The first **acceptance ticket**'s journey is what proves the break switch.

**Read first** names three sections of the `ui-acceptance` skill: `references/story-parity.md` **The story page the product serves**; `references/journey.md`; and `references/product-answers.md`. **Owns** is `.mmw/`, the story service and the interaction helper, and, as the prefactor ticket below, every file that registers a design page's scenes and routes.

Journeys appear on the contract ticket, on tickets the owner named, and on each acceptance ticket.

Where the spec has a screen contract, the **prefactor ticket** of step 5 is this ticket. It registers the scenes and routes of every design page in the contract, not only of the page it makes the precedent from.

## component page ticket

Cut by design page, `Component · ` pages. One story criterion (element parity) covers the mounts of the pages it takes. Each owned row whose `calls` is not `none`, or whose `next` is not `stay`, gets one boundary criterion; rows that share a test file may share one.

A row whose `next` is a scene of another page (`note-list.open`, whose `next` is `editor-open`, a scene of `Component · note-editor`) is tested where the component stands alone, and that other page is not in its render. Its boundary test asserts `calls`, `shows` and `on_failure` as for any row, and for `next` asserts what this component hands on: the event, route change or state it emits, carrying what the target scene needs (the id of the note to open). That the other page then enters the named scene is asserted once, by the `App · ` cross-component row the contract repeats this behaviour as, on the **app page ticket** that owns it.

**Owns** is the `component` directory the contract's `pages` declares for each page it takes, and the test files it adds. The design page names which rows the ticket is answerable for, never where it may write.

**Read first** carries two baseline lines, and the design page names for a person to read:

- the design package, for look and verbatim copy
- the screen contract with the row ids this ticket owns, written `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`: path and ids on one line, for calls, shown values, transitions and timing. Pages and mounts follow from those rows.

The rest of **Read first** is derived from those row ids, not hand-picked: `scenes.json`; and every `source` of the owned rows that is a baseline (a decision ticket (`#<n>`), an ADR, a domain document under `docs/`), listed once per document, with a word on what it settles. Spec sections and stories reach the worker through **Parent**.

A `CHECK:` that stubs the application's own network (`vi.stubGlobal('fetch')`, msw, nock, fetch-mock) is refused; mocking the product's outbound call module is the boundary test.

## app page ticket

Takes one `App · ` page. One story criterion covers that page's mount. Each **cross-component row** on that page gets one boundary criterion. The **component page ticket** of every `Component · ` page this App page composes blocks it.

**Owns** is the product's composition module (the code that wires the regions together in the running product), the story page that mounts that module rather than wiring the components itself, and the test files it adds. An `App · ` page names no `component` in the contract, so there is no product directory to translate it into: the composition module's path comes from the product's code; the App page itself stays a baseline under **Read first**.

**Read first** carries two baseline lines, and the App page name for a person to read:

- the design package, for look and verbatim copy
- the screen contract with the cross-component row ids this ticket owns, written `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`: path and ids on one line. Pages and mounts follow from those rows.

The rest of **Read first** is derived from those row ids, not hand-picked: `scenes.json`; and every baseline-class `source` of the owned rows, listed once per document.

## acceptance ticket

Cut none only when the product can never be started whole (a library, a component with no running product). A product whose `.mmw/target.json` does not exist yet still gets them: its **contract ticket** lands `start`.

The spec's **Critical flows** bullet names them: money, sign-in, one submit chain; none when the product has none. One **acceptance ticket** per flow.

The ticket-cutting session writes the journey criterion, with `--break`, taking as default the last write among the contract rows that flow involves. The worker who writes the journey script leaves that choice as it is.

**Parent** names the Implementation Decisions sections that flow lists. It is blocked by every ticket of this batch whose work that flow uses: the **component page ticket** and **app page ticket** of the pages it walks, and the tickets that build the operations those rows' `calls` name. A journey drives the real product with nothing mocked, so an operation that does not exist yet fails it at the first write, and the blockers are derived from the flow's rows, not from the list of ticket kinds. It is `senior-worker`. A new worker starts it on the merged base branch after those blockers have landed; a red run is `HANDOFF REQUIRED` for triage, and the closing comment names the step that broke.

**Owns** is `.mmw/journeys/<flow>/`, plus adding to the shared helper when there is one; product code is not in it.

## Shared journey helper

When two or more journey tickets in the batch (an **acceptance ticket**, or another ticket that names a journey) need the same product access (bringing the stack up, a health check, sign-in, a top-up), the **contract ticket** (when there is one) or the first journey ticket in the batch creates one helper module under `.mmw/harness/` and lists it under its **Owns**. Later journey tickets import it.

## reaction ticket

One extra *reaction* ticket: the user uses this spec's interface on the running product and judges what no story render shows, how it feels in use and whether the whole surface reads as one product. Appearance a story render does show, decoration with no `data-ui` id included, stops at question 2 first: it is the `UI` axis of code review, which looks at those renders. It is blocked by every **component page ticket** and **app page ticket**. The rest of a *reaction* ticket is [person-ticket.md](person-ticket.md).

## When the rows change

When a later pull's `pull-report.md` records `增删控件或改流转`, and the `write-screen-contract` skill's **Re-runs** have rewritten the rows:

- A ticket already cut and not yet landed has its criteria and **Read first** corrected to the new rows.
- A new row gains one boundary criterion on the ticket that owns it.
- A ticket already landed is followed by a correction ticket whose criterion is the same as the original's.

A published ticket is edited only by the main agent or the user, through the `to-spec` skill's step for revising a published spec.
