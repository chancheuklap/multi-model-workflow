# A spec with a screen contract

For an effort with a UI, which has a **screen contract**: what reading it asks before the spec is written, and what the spec gains. Everything else in `SKILL.md` holds as written.

## Before writing

An effort with a UI has a **screen contract** (`docs/specs/<effort>/screen-contract.yaml`, written by the `write-screen-contract` skill) and two baselines with separate jurisdictions: the design package for look and verbatim copy, the screen contract for what each control calls, which field feeds each shown value, what state follows and how a test reaches it. Read the screen contract in full, its `pages` and `scenes` included. A row whose `gap` is not `aligned` is a decision nobody has made: stop rather than write a spec around it. A decision that no row carries and the design package does not draw (a behaviour of something that is text, not a control) is written in the subsection it belongs to as "this spec's decision", citing what it rests on.

With a screen contract, a story page is put into a scene by its adapter reading that scene's values, so a test at that seam cannot reach a product state that only a real request produces. A four-column boundary test that asserts `calls`, `shows`, `next` and `on_failure` after a click still cannot seed the database the click would have written.

## What the spec gains

Under `## Implementation Decisions`:

An effort with a screen contract has one fixed subsection here, **API contract**: one entry per distinct operation in the screen contract's `calls` column (its request fields, its response fields, its failure cases), derived from the rows' `shows` and `on_failure`, each entry citing the row ids that use it. This is where a new project's OpenAPI document starts.

The same effort has one fixed subsection here, **cross-component composition**: one entry per **cross-component row**, naming the request fields that row's action carries and the state the other region enters, citing the row id.

The same effort has one paragraph on **visual acceptance**, in its own numbered subsection or the one that carries the `data-ui` ids, and it restates no command: appearance is decided by **element parity** (the story oracle of the `ui-acceptance` skill pairs both sides by `data-ui` id), citing the screen contract's `pages`, `App · ` pages included. Each design page's `mount` is the story page id.

Under `## Testing Decisions`, the bullet **How a test arrives at a state** also says: With a screen contract, three mechanisms are named here: the story adapter that puts a story page into a scene from its scene data (or the screen contract's scene input), the interaction helper that puts a control on screen by its `data-ui` id for a four-column boundary test, and `start` in `.mmw/target.json`, which brings the product up for a journey. On a new product all three are new. On a product whose `.mmw/` already answers, say which is missing, counting what `target_config.py --check` of the `ui-acceptance` skill reports and any answer built for a design package, scene shape or control lookup other than the current ones, or say that nothing is. How each is shaped is that skill's references, and is not restated.

Under `## Testing Decisions`, one more bullet, before the commands to run before committing:

- **Critical flows** (关键流程). Only with a screen contract: List the flows where a silent break costs the user money, access or submitted work, not every path through the UI. One line per such flow, naming the flow (the directory name under `.mmw/journeys/<flow>/`) and the Implementation Decisions section numbers it involves. Each line sits nested under the bullet in one shape, ``- `<flow>`: Implementation Decisions sections <n>, <n>``: the words `Implementation Decisions` stay in English whatever language the spec is written in, as a ticket's `## Parent` names them, and the numbers follow them. The `verify-ticket` skill's `--lint` reads these lines to decide which journeys need `--break`, and reports any line it cannot read. Each line becomes a critical-flow ticket: a journey that drives the real product end to end with nothing mocked, and runs again with the flow's last write broken to prove the journey notices. Write `none` when the product has no such flow; omit the bullet also when the product can never be started whole (a library, a component with no running product); a product whose `.mmw/target.json` does not exist yet still writes it, because its contract ticket lands `start`.
