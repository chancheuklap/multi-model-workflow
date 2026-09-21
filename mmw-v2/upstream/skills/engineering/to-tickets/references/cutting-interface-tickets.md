# Cutting interface tickets

Reached from step 3 of [`SKILL.md`](../SKILL.md) when the spec has a screen contract, and from that file's `<issue-template>` `## Read first`. The five kinds of ticket, the shared journey helper, the extra *reaction* ticket, and what to do after the rows change, are all here. An **interface ticket** is any of the five — `verify-ticket.py --lint` calls a ticket that carries a `screen-contract.yaml rows:` line one; the **component page ticket** below is one kind.

Copy each criterion from the named section of the `ui-acceptance` skill; the shape lives only there:

- A story criterion: `references/story-parity.md` § **The criterion, in one shape**.
- A boundary criterion: `references/boundary-check.md` § **The criterion, in one shape**. The product's test asserts the four columns of that row.
- A journey criterion: `references/journey.md` § **The criterion, in one shape**.

**A layer with no precedent yet:** a product from zero takes its adapter, its interaction helper and its first journey script, as the precedent, from the **contract ticket**. Cut that ticket first. The criteria of the tickets behind it copy their `CHECK:` and `EXPECT:` from what it lands. Nothing here sends you back to the `to-spec` skill for a precedent the spec cannot have.

## design-system ticket

Only a new product gets one. It copies the design system's style tokens and shared components into the product code, keeping the class names. It sits ahead of the **contract ticket** and blocks it: the contract ticket's element parity precedent needs a component whose styles are already in the product. Its criterion does not depend on `.mmw/`.

**Read first** names the `_ds/` copy in the handoff package, the design system Claude Design used to draw the pages.

Its criterion is one comparison, written under question 1 of **the five questions** in `SKILL.md`: a shell command that the style tokens and the shared components exist in the product code. Whether those styles match the design system, value by value, is each later **interface ticket**'s element parity.

## contract ticket

An existing product whose `.mmw/` is already complete: fill only what `target_config.py --check` of the `ui-acceptance` skill still reports missing. When something is missing, this ticket blocks the tickets that need those deliverables. When the command reports nothing missing, cut none.

A new product: land `.mmw/` in full. It blocks every ticket in the batch except the **design-system ticket**. What it lands is the precedent later tickets copy.

What it delivers:

- `.mmw/target.json`, including `harness_markers`
- the story service and the first story adapter
- the interaction helper that finds a control by its `data-ui` id
- this product's element parity precedent
- the static guards: the interface takes no fake data; `mount` is unique in one render; a `data-ui` id repeats only on the repeating part of a list
- the **break switch** under `.mmw/harness/`: `start` reads `MMW_BREAK` and the switch acts only on the product process
- the smoke journey
- the **harness guard**

What every product answer must still guarantee is the `ui-acceptance` skill's `references/product-answers.md`. One product's shape is an example, not a requirement on the next.

The smoke journey uses the journey criterion and omits `--break`. It requires the product to come up and answer; it signs in when the product has a login. Its second pass is the product-down pass that section already names. The first **acceptance ticket**'s journey is what proves the break switch.

**Read first** names three sections of the `ui-acceptance` skill: `references/story-parity.md` **The story page the product serves**; `references/journey.md`; and `references/product-answers.md`.

Journeys appear on the contract ticket, on tickets the owner named, and on each acceptance ticket.

Where the spec has a screen contract, the **prefactor ticket** of step 5 is this ticket. It registers the scenes and routes of every design page in the contract, not only of the page it makes the precedent from.

## component page ticket

Owns by design page, `Component · ` pages. One story criterion (element parity) covers the mounts of the pages it owns. Each owned row whose `calls` is not `none`, or whose `next` is not `stay`, gets one boundary criterion; rows that share a test file may share one.

**Read first** carries two baseline lines, and the design page names for a person to read:

- the handoff package, for look and verbatim copy
- the screen contract with the row ids this ticket owns, written `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`: path and ids on one line, for calls, shown values, transitions and timing. Pages and mounts follow from those rows.

The rest of **Read first** is derived from those row ids, not hand-picked: `scenes.json`; and every `source` of the owned rows that is a baseline (a decision ticket (`#<n>`), an ADR, a domain document under `docs/`), listed once per document, with a word on what it settles. Spec sections and stories reach the worker through **Parent**.

A `CHECK:` that stubs the application's own network (`vi.stubGlobal('fetch')`, msw, nock, fetch-mock) is refused; mocking the product's outbound call module is the boundary test.

## app page ticket

Owns an `App · ` page. One story criterion covers that page's mount. Each **cross-component row** on that page gets one boundary criterion. The **component page ticket** of every `Component · ` page this App page composes blocks it.

**Read first** carries two baseline lines, and the App page name for a person to read:

- the handoff package, for look and verbatim copy
- the screen contract with the cross-component row ids this ticket owns, written `docs/specs/<effort>/screen-contract.yaml rows: a.b, a.c`: path and ids on one line. Pages and mounts follow from those rows.

The rest of **Read first** is derived from those row ids, not hand-picked: `scenes.json`; and every baseline-class `source` of the owned rows, listed once per document.

## acceptance ticket

Cut none when the repository's `.mmw/target.json` cannot start the whole product.

The spec's **Critical flows** bullet names them: money, sign-in, one submit chain; none when the product has none. One **acceptance ticket** per flow.

The ticket-cutting session writes the journey criterion, with `--break`, taking as default the last write among the contract rows that flow involves. The worker who writes the journey script leaves that choice as it is.

**Parent** names the Implementation Decisions sections that flow lists. It is blocked by every ticket of this batch whose work that flow uses: the **component page ticket** and **app page ticket** of the pages it walks, and the tickets that build the operations those rows' `calls` name. A journey drives the real product with nothing mocked, so an operation that does not exist yet fails it at the first write, and the blockers are derived from the flow's rows, not from the list of ticket kinds. It is `senior-worker`. A new worker starts it on the merged base branch after those blockers have landed; a red run is `HANDOFF REQUIRED` for morning triage, and the closing comment names the step that broke.

**Owns** is `.mmw/journeys/<flow>/`, plus adding to the shared helper when there is one. **Seam** may forbid edits to product code; it does not forbid adding to that helper. The `verify-ticket` skill's `references/linting.md` already treats an **Owns** covering `.mmw/journeys/<flow>/` as the ticket that builds it; the shared helper is covered by the ticket that creates it.

## Shared journey helper

When two or more journey tickets in the batch (an **acceptance ticket**, or another ticket that names a journey) need the same product access (bringing the stack up, a health check, sign-in, a top-up), the **contract ticket** (when there is one) or the first journey ticket in the batch creates one helper module under `.mmw/harness/` and lists it under its **Owns**. Later journey tickets import it.

## reaction ticket

One extra *reaction* ticket: the user looks at this spec's interface on the real product and finds appearance the scripts do not cover (decoration with no `data-ui` id, the overall look). It is blocked by every **component page ticket** and **app page ticket**. The rest of a *reaction* ticket is [person-ticket.md](person-ticket.md).

## When the rows change

When a later pull's `pull-report.md` records `增删控件或改流转`, and the `write-screen-contract` skill's **Re-runs** have rewritten the rows:

- A ticket already cut and not yet landed has its criteria and **Read first** corrected to the new rows.
- A new row gains one boundary criterion on the ticket that owns it.
- A ticket already landed is followed by a correction ticket whose criterion is the same as the original's.

A published ticket is edited only by the main agent or the user, through the `to-spec` skill's step for revising a published spec.
