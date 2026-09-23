# Cutting interface tickets

The five kinds of ticket below are what a screen contract produces. An **interface ticket** is one whose **Read first** carries a `screen-contract.yaml rows:` line, as `verify-ticket.py --lint` reads it: the **component page ticket** and the **app page ticket**.

Copy each criterion from the named section of the `ui-acceptance` skill; the shape lives only there:

- A story criterion: `references/story-parity.md` § **The criterion, in one shape**.
- A boundary criterion: `references/boundary-check.md` § **The criterion, in one shape** and § **Selecting one row's test**. The product's test asserts the four columns of that row.
- A journey criterion: `references/journey.md` § **The criterion, in one shape**.

**A layer with no precedent yet:** a product from zero takes its adapter, its interaction helper and its first journey script, as the precedent, from the **contract ticket**. Cut that ticket first. The criteria of the tickets behind it copy their `CHECK:` and `EXPECT:` from what it lands. Nothing here sends you back to the `to-spec` skill for a precedent the spec cannot have.

## Seam and Owns on these tickets

**Seam** names, for each criterion shape the ticket uses, where it observes and what puts the product there: a story criterion observes the product's story page, put into its scene by the story adapter reading the scene data; a boundary criterion observes the product's outbound call module, replaced for the test, with the interaction helper acting on the row's `data-ui` id; a journey criterion observes the real product brought up by `start` in `.mmw/target.json`; the design-system, static-guard and harness-guard criteria read the repository tree. **Seam** also names the precedent to copy; on a product from zero that is what the **contract ticket** lands.

**Owns** says where this ticket may write, so no design page is ever an entry there: the design package is a baseline under **Read first**, and the worker is forbidden to edit it. Translate the pages a ticket takes into product paths through the contract, whose `pages.<page>.component` names the directory the implementation owns each `Component · ` page under.

## design-system ticket

Cut one whenever the design package carries a design system under `_ds/<folder>/` whose variables or part stylesheets the product code does not yet have; otherwise each interface ticket writes the styles its component needs from the design pages. A design system built from an existing product's code counts: it merges inconsistent values into one scale and records each merge in its `readme.md` table `Unifications`, so copying it back changes the product. The ticket copies the variables (colour, type scale, spacing, radius, shadow), the fonts and the part stylesheets (each part a class name with its stylesheet) from `_ds/<folder>/` into the product code, keeping the class names. It sits ahead of the **contract ticket** and blocks it: the contract ticket's element parity precedent needs a component whose styles are already in the product. A batch with no contract ticket has it block every **component page ticket** and **app page ticket** instead. Its criterion does not depend on `.mmw/`.

**The design-system ticket is the second exception to vertical slicing**, beside the wide refactor `SKILL.md` step 3 names. It lands one layer, the styles, and demonstrates no behaviour of its own.

**Read first** names the `_ds/` copy in the design package, the design system Claude Design used to draw the pages. **Owns** is the product files the variables, fonts and part stylesheets land in.

Its criterion is one shell command showing that the design system's variables and part stylesheets exist in the product code. Whether those styles match the design system, value by value, is each later **interface ticket**'s element parity.

## contract ticket

An existing product: fill only what the spec's **How a test arrives at a state** names as missing. When something is missing, this ticket blocks the tickets that need those deliverables. When nothing is, cut none.

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

Of those, only the smoke journey carries a criterion on this ticket. The static guards and the harness guard sweep the whole repository, which every later page ticket adds to, so their criteria (one command each) go on the batch's last ticket: the last **acceptance ticket** where the batch has one, otherwise the last **app page ticket** or **component page ticket**, made last by being blocked by every other agent ticket of the batch. The rest are precedents, first decided by a command on the ticket that copies them: the first **component page ticket** for the story service, the story adapter, the interaction helper and the element parity precedent; the first **acceptance ticket** for the break switch. Whether any of them is built well is code review's.

The contract ticket's **What to build** fixes each static guard's test file and case name; the last ticket's static-guard `CHECK:` runs that case with the repository's test runner, and its `EXPECT:` is the runner's success line.

This ticket writes the `data-ui` ids onto the precedent's component and builds the story adapter for its page, and its **Owns** lists those component files beside `.mmw/`. The **component page ticket** that takes that component's page owns the same directory, is blocked by this one, and carries the story and boundary criteria that first judge the precedent. A new product with no component yet has nothing to make comparable here: its precedent is the component the first **component page ticket** builds, and this ticket delivers the story service, the story adapter shape and the interaction helper that ticket uses, with no component files under **Owns**.

The smoke journey uses the journey criterion and omits `--break`. It requires the product to come up and answer; it signs in when the product has a login. Its second pass is the product-down pass that section already names. The first **acceptance ticket**'s journey is what proves the break switch.

**Read first** names three sections of the `ui-acceptance` skill: `references/story-parity.md` **The story page the product serves**; `references/journey.md`; and `references/product-answers.md`. **Owns** is `.mmw/`, the story service and the interaction helper, and, as the prefactor ticket below, every file that registers a design page's scenes and routes.

Journeys appear on the contract ticket, on tickets the user named, and on each acceptance ticket.

Where the spec has a screen contract, the **prefactor ticket** of step 5 is this ticket. It registers the scenes and routes of every design page in the contract, not only of the page it makes the precedent from.

## component page ticket

Cut by design page, `Component · ` pages. One story criterion (element parity) covers the mounts of the pages it takes. Each owned row whose `calls` is not `none`, or whose `next` is not `stay`, gets one boundary criterion; rows that share a test file may share one.

A row whose `next` is a scene of another page (`note-list.open`, whose `next` is `editor-open`, a scene of `Component · note-editor`) is tested where the component stands alone, and that other page is not in its render. Its boundary test asserts `calls`, `shows` and `on_failure` as for any row, and for `next` asserts what this component hands on: the event, route change or state it emits, carrying what the target scene needs (the id of the note to open). That the other page then enters the named scene is asserted once, by the `App · ` cross-component row the contract repeats this behaviour as, on the **app page ticket** that owns it.

**Owns** is the `component` directory the contract's `pages` declares for each page it takes, and the test files it adds. The design page names which rows the ticket is answerable for, never where it may write.

**Read first** carries two baseline lines, and the design page names for a person to read:

- the design package, for look and verbatim copy
- the screen contract with the row ids this ticket owns, written `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`: path and ids on one line, for calls, shown values, transitions and timing. Pages and mounts follow from those rows.

The rest of **Read first** is derived from those row ids, not hand-picked: `scenes.json`; and every `source` of the owned rows that is a baseline (a decision ticket (`#<n>`), an ADR, a domain document under `docs/`), listed once per document, with a word on what it settles. Spec sections and stories reach the worker through **Parent**.

When a contract row this ticket owns cites a section of an earlier spec as its source, name that spec and its sections after the parent's, in the same words, and never first (for example, "#12, Implementation Decisions sections 5 and 7; #7 Implementation Decisions section 4").

## app page ticket

Takes one `App · ` page. One story criterion covers that page's mount. Each **cross-component row** on that page gets one boundary criterion. The **component page ticket** of every `Component · ` page this App page composes blocks it.

**Owns** is the product's composition module (the code that wires the regions together in the running product), the story page that mounts that module rather than wiring the components itself, and the test files it adds. An `App · ` page names no `component` in the contract, so there is no product directory to translate it into: the composition module's path comes from the product's code; the App page itself stays a baseline under **Read first**.

**Read first** carries the same two baseline lines as a **component page ticket**'s, with the cross-component row ids this ticket owns, and the App page name for a person to read; the rest is derived from those row ids the same way.

## acceptance ticket

One **acceptance ticket** per line of the spec's **Critical flows**; none when that bullet reads `none` or the spec has no such bullet.

The ticket-cutting session writes the journey criterion, with `--break`, taking as default the last write among the contract rows that flow involves. The worker who writes the journey script leaves that choice as it is.

**Parent** names the Implementation Decisions sections that flow lists. It is blocked by every ticket of this batch whose work that flow uses: the **component page ticket** and **app page ticket** of the pages it walks, and the tickets that build the operations those rows' `calls` name. A journey drives the real product with nothing mocked, so an operation that does not exist yet fails it at the first write, and the blockers are derived from the flow's rows, not from the list of ticket kinds. It is `senior-worker`.

**Owns** is `.mmw/journeys/<flow>/`, plus adding to the shared helper when there is one; product code is not in it.

## Shared journey helper

When two or more journey tickets in the batch (an **acceptance ticket**, or another ticket that names a journey) need the same product access (bringing the stack up, a health check, sign-in, a top-up), the **contract ticket** (when there is one) or the first journey ticket in the batch creates one helper module under `.mmw/harness/` and lists it under its **Owns**. Later journey tickets import it.

## reaction ticket

One extra *reaction* ticket: the user uses this spec's interface on the running product and judges what no story render shows, how it feels in use and whether the whole surface reads as one product. Appearance a story render does show, decoration with no `data-ui` id included, stops at question 2 first: it is the `UI` axis of code review, which looks at those renders. It is blocked by every **component page ticket** and **app page ticket**. The rest of a *reaction* ticket is [person-ticket.md](person-ticket.md).

## When the rows change

The `to-spec` skill's `references/revising-a-spec.md` says how tickets already cut follow rows a later pull changed.
