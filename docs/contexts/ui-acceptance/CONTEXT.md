# UI acceptance

How a UI is proved correct by machine: the design package a Claude Design project leaves in the repository, the oracles that compare a product story with its design page, run a four-column boundary test twice and run a real journey, the screen contract that says what every control does, and the lease that gives each ticket worktree its own share of this machine.

## Language

### The design side

**Claude Design**:
The design tool whose project is the only source of the design: pages are drawn and signed off there, and the repository's **design package** is written only by **pull**.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`

**Claude Design agent**:
The agent inside one Claude Design project, separate from the `design-pages` session: it sees only its own project and reads the repository only through Claude Design's GitHub connection, reads the project-root `CLAUDE.md` on every conversation, and does the work `task.md` lists when the user says to start or continue.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`, `mmw-v3/skills/mmw-mode/playbooks/build-a-design-system.md`

**design system**:
A Claude Design project holding a product's look — variables, fonts, icons and reusable parts — from which the pages of a bound **page project** are drawn; that project holds a copy of it under `_ds/<folder>/`, which the `design-pages` session writes when it creates the project and refreshes after the design system changes. It holds no page regions, **example data** or product logic.
_Home_: `mmw-v3/skills/design-pages/references/template-design-system-claude-md.md`, `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`

**page project**:
A Claude Design project holding a product's pages, as opposed to a **design system** project; bound to a design system when the product has one.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`, `mmw-v3/skills/mmw-mode/playbooks/build-a-design-system.md`

**part** (design system):
One reusable element of a **design system** (a button kind, a status mark, a list row, a card shell): one class name with its variants, shown on its own card, which renders every state of the part. Distinct from the `<element>` half of a **`data-ui` id**, and from the **Reusable parts** section of an experiment's `README.md`.
_Home_: `mmw-v3/skills/design-pages/references/template-design-system-claude-md.md`

**Unifications**:
The table at the end of a design system's `readme.md` recording each value it unified, the code values it joined, and its class name; the product follows it once pages drawn from the design system are pulled.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/build-a-design-system.md`

**Design in Claude Design**:
The `mmw-mode` playbook around the editing of pages in Claude Design: creating the project, writing `task.md` for the **Claude Design agent**, refreshing `_ds/` after a design-system change, acting on the comments sent to Claude, and taking the sign-off. The pages themselves are edited inside Claude Design, by the user and that agent; bringing an existing product's look in is the `Build a design system` playbook.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`

**pull**:
The `Pull a design` playbook, and its command `pull_design.py` in the `design-pages` skill, that writes the **design package** from a signed-off Claude Design project.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md`

**pull report**:
`pull-report.md` in the **design package**, written at every **pull** under the headings `设计检查`, `覆盖`, `改动分类` and `本地改过的说明`; `改动分类` (`增删控件或改流转` or `只改外观或文案`) decides which skill the pull hands to. Its design problems do not fail the command.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md`

**`MMW_DESIGN_PREVIEW_URL`**:
The environment variable pull sets to the MCP `render_preview` result's `serve_url`, the short-lived address `pull_design.py` reads to render a page offline; never printed or written to a file.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md`

**`task.md`**:
The Claude Design project-root file this session writes, listing the work its own agent does now, one checkbox item per piece of work; it never overrides `CLAUDE.md`.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`, `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**`state-list.md`**:
The Claude Design project-root file, when present, listing the regions and states to draw, one `### <region>` heading per `Component ·` page; a page and the list disagreeing is put to the user, never silently edited.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**`ui-ids.md`**:
The Claude Design project-root file, when present, listing the `data-ui` ids a product already carries, collected by reading every `[data-ui]` its story pages render; a page drawn for such a product reuses those ids.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md`, `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**`CLAUDE.md`** (Claude Design project):
The instruction file at a Claude Design project's root — a page project's page conventions, or a design system's sources and unification rules — that only that project's **Claude Design agent** reads, on every conversation. Distinct from a repository's own `CLAUDE.md` (`docs/contexts/toolbox/CONTEXT.md`), which holds only `@AGENTS.md`.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`, `mmw-v3/skills/design-pages/references/template-design-system-claude-md.md`

**state list**:
The fixed heading `## State list` in a UI prototype's leaf `README.md`: every state of the winning variant, one heading per **region**. On a wayfinder map it is in the **design ticket**'s leaf `README.md`; for an existing product brought into Claude Design, in `efforts/<effort>/README.md`.
_Home_: `mmw-v3/skills/prototype/UI.md`, `mmw-v3/skills/design-pages/SKILL.md`

**design ticket**:
The wayfinder ticket that produces the **design package** for a destination with a UI, worked with the `design-pages` skill. It blocks the **alignment ticket**.
_Home_: `mmw-v3/skills/mmw-mode/references/interface-and-remake.md`

**design page**:
A `.dc.html` page of a Claude Design project, or of the **design package** pull writes from it. **Component page** and **App page** are the two kinds acceptance reads; a page under any other name (notes, overviews, explorations) is not pulled into acceptance.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**Component page**:
A `Component · <name>` **design page**: one **region** of the screen, the unit acceptance checks, exposing a `scene` prop whose values are that region's accepted states. Distinct from the `component` column of a screen contract's `pages`, which names the **product component**.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**App page**:
An `App · <name>` **design page**: a whole screen made of `Component ·` pages, needed only when their states must be checked together; it sets no region's own background, so a region drawn over others shows through what it covers.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**product component**:
The product's own component that a **story** page renders and a `pages` entry's `component` column names; on a story page it is presentational and reaches for no backend of its own.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**composition module**:
The product's own code that wires a screen's regions together in the running product. The **story** page for an **App page** mounts it and feeds it scene data without wiring the components itself, so a region the product leaves unwired stays unwired on the story page.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**region**:
One `Component · ` page's area of a screen, named by that page: the `<region>` half of a **`data-ui` id** (`<region>.<element>`).
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**`dc-import`**:
The mechanism by which an `App ·` page wires in the `Component ·` pages it shows, repeating their `data-ui` ids by doing so; the screen contract's cross-component rows are read off this wiring.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**`$preview`**:
The `data-props` field every `Component ·`/`App ·` page declares, `width` and `height` in pixels: the size each scene is rendered and checked at.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**design package**:
The Claude Design project as it sits in the repository, written only by **pull** into `efforts/<effort>/claude-design/`: the project's pages, every file they load, and what pull writes beside them. The screen contract's `baselines.look` names it.
_Avoid_: handoff package (for this; `handoff` is the `handoff` skill and `HANDOFF REQUIRED`)
_Home_: `mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md`

**scene**:
One value of a design page's `scene` prop, and the matching `scenes.json` entry **pull** writes. The product story is addressed by `?page=&scene=`.
_Home_: `mmw-v3/skills/design-pages/references/template-project-claude-md.md`

**scene input**:
The value in a design-package data file that a design page draws one scene from, declared in the screen contract as `scenes.<name>.input` when the page runs logic over backend-shaped data. The **story adapter** then feeds the product component from it instead of from the **scene data**.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**scene data**:
The `data` field of a `scenes.json` entry: the displayed values keyed by **`data-ui` id**, which **pull** writes from the offline render and the **story adapter** reads.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**example data**:
The product's real data for the states a design draws, kept in its own directory beside the **design package** (`efforts/<effort>/example-data/`), never inside it; a design system's `CLAUDE.md` names it, and the **Claude Design agent** derives each region's data file from it. Distinct from a page's own data files under `data/`, which the project template's `## Page data` governs.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/build-a-design-system.md`, `mmw-v3/skills/design-pages/references/template-design-system-claude-md.md`

**`DESIGN.md`**:
A DESIGN.md-format file a consuming repository may keep. It is not the design source.
_Home_: `docs/adr/0029-claude-design-is-the-design-source.md`

**prototype**:
Code that answers one design question, kept under `efforts/<effort>/prototypes/<issue>/<UI|LOGIC|EXP>/` with its question and verdict in the leaf `README.md`. A UI prototype is several structurally different variants on one real route, of which the user picks the winner, handed to Claude Design rather than folded into the real code directly.
_Home_: `mmw-v3/skills/prototype/SKILL.md`

**leaf directory**:
`efforts/<effort>/prototypes/<issue>/<UI|LOGIC|EXP>/`, one per prototype kind, `<issue>` the ticket number or a short feature name when there is no ticket. Its `README.md` is read to its verdict as a `## Read first` item.
_Home_: `mmw-v3/skills/prototype/SKILL.md`

**effort** (`<effort>`):
The development effort's directory name, lowercase ASCII words joined by `-`, from a wayfinder map's `## Notes` when the ticket has one, otherwise asked of the user with the current branch name as fallback. Its directory `efforts/<effort>/` holds every file of that effort and nothing else: the **design package**, the **example data**, the **state list** of an existing product, the **screen contract**, its **prototype**s under `prototypes/` and its map's research notes under `research/`. Whether the effort is still open is its spec's or map's state on the tracker, recorded nowhere in the directory; a closed effort's directory records what was built then, not the product as it is now. Distinct from the toolbox's **`effort`**, a model's reasoning effort in `models.json`.
_Home_: `mmw-v3/skills/prototype/SKILL.md`

**scaffolding**:
The mount point or prototype route, the floating switcher, the leaf directory's import, and any route-side symlink that let a UI prototype's variants render inside the real app; taken down after the design's first pull.
_Home_: `mmw-v3/skills/prototype/UI.md`, `mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md`

**shell**:
The wrapper kept outside a prototype's reusable core — the HTML page around a logic prototype's pure module, the harness around an experiment's boundary — which stays in the leaf directory to run again and is never promoted to production.
_Home_: `mmw-v3/skills/prototype/LOGIC.md`, `mmw-v3/skills/prototype/EXP.md`

**experiment round**:
One run, or one batch of runs, made to answer an experiment's question under one set of parameters; the leaf `README.md`'s **Rounds** section holds one subsection per round, newest first.
_Avoid_: round (for this; the tickets context's **round** is a different unit of work)
_Home_: `mmw-v3/skills/prototype/EXP.md`

**experiment `README.md` section**:
One of the six fixed sections of an experiment's leaf `README.md`, in order: Question and bar, How to run, Legend, Rounds, Conclusion, Reusable parts.
_Home_: `mmw-v3/skills/prototype/EXP.md`

**evidence page**:
The static HTML page an experiment's own generator writes at the end of every run, laying its outputs side by side as a comparison grid (one row per sample, one column per approach) or a catalogue (a summary table plus one block per item); facts only, no verdict, and the next run overwrites it.
_Home_: `mmw-v3/skills/prototype/EXP.md`, `mmw-v3/skills/prototype/evidence-page.md`

**evidence scratch directory**:
`.scratch/<effort>/<issue>/evidence/<name>/`, the project's own git-ignored location an evidence page and its media are written to, mirroring the leaf path; deleted once the approach is settled, since the generator can reproduce it.
_Avoid_: scratch (for this; write-screen-contract's `<scratch>` is a different, `mktemp`-created directory)
_Home_: `mmw-v3/skills/prototype/EXP.md`

### The oracles

**product under test**:
The application a consuming repository runs under automation, which the oracles test; "the product" is its short form. The repository answers in `.mmw/` what the ui-acceptance skill cannot know about it.
_Home_: `mmw-v3/skills/ui-acceptance/SKILL.md`

**oracle**:
One of the four scripts an acceptance criterion names by its bare name: the **story oracle**, `boundary-check.py`, `journey.py` and the **harness guard**.
_Avoid_: judge
_Home_: `mmw-v3/skills/verify-ticket/SKILL.md`

**`data-ui` id**:
The element identity shared by a design page and the matching product element. The story oracle pairs elements by it, and a four-column boundary test finds the control by it.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**element parity**:
The story oracle's comparison of a product story with its design page, both sides paired by **`data-ui` id**: presence, visibility, text, size, position and the listed style facts, one `DIFF` line per difference.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**story**:
A product page, served from `.mmw/stories/`, that renders the product's own components from the same scene data the design page used, addressed as `?page=<mount>&scene=<name>&viewport=<WxH>`. It has no backend, seed, route or lease.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**user story**:
One line of a spec's `## User Stories`.
_Avoid_: story (for this; a story is the product page the story oracle opens)
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-a-spec.md`

**story oracle**:
`story-parity.py` of the ui-acceptance skill, which decides **element parity** between a product story and the design page it was built from.
_Avoid_: story judge
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**story adapter**:
What puts a **product component** into one scene on a **story** page: one per design page, identified by its `mount`, mapping the scene's **scene data** onto the component.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**story service**:
The server `.mmw/target.json`'s `stories` command brings up under `.mmw/stories/`, serving the story pages both the story oracle and the harness guard read.
_Avoid_: story-service files (for the server itself; that phrase names its files, in `references/harness-guard.md`)
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**`[data-story-root]`**:
The attribute on the product component's own root element that the story oracle compares from; the design page's root carries the same `data-ui` id.
_Home_: `mmw-v3/skills/ui-acceptance/references/story-parity.md`

**four-column boundary test**:
A product test that asserts one screen-contract row's `calls`, `shows`, `next` and `on_failure` together, finding the control by its **`data-ui` id** and replacing the **gateway** with a mock.
_Home_: `mmw-v3/skills/ui-acceptance/references/boundary-check.md`

**gateway**:
The layer a consuming repository names as the one that makes outbound calls, over HTTP, IPC or an extension message. A four-column boundary test replaces it with a mock.
_Avoid_: outbound call module
_Home_: `mmw-v3/skills/ui-acceptance/references/boundary-check.md`

**boundary criterion**:
An acceptance criterion running `boundary-check.py --run "<the product's test command>"` against a **four-column boundary test**: the command must pass as written and fail with `MMW_NEGATIVE=1`.
_Home_: `mmw-v3/skills/ui-acceptance/references/boundary-check.md`

**journey criterion**:
An acceptance criterion running `journey.py run <name>`, with `--break "<METHOD> <route>"` on a critical-flow ticket's journey so its second start fails that one operation; the contract ticket's smoke journey runs without it, and its second pass runs with the product down.
_Home_: `mmw-v3/skills/ui-acceptance/references/journey.md`

**harness guard criterion**:
An acceptance criterion running `harness-guard.py .` from the repository root, passing on `HARNESS OK`.
_Home_: `mmw-v3/skills/ui-acceptance/references/harness-guard.md`

**interaction helper**:
The one shared click-and-fill helper the **contract ticket** delivers, which every four-column boundary test calls to act on the page. Under `MMW_NEGATIVE=1` it does nothing, which is what the boundary criterion's **negative control** relies on.
_Home_: `mmw-v3/skills/ui-acceptance/references/boundary-check.md`

**fault-injection switch**:
The product-owned switch in `.mmw/harness/` that a journey criterion with `--break` arms on its second start, so that the product itself fails one named operation. On that start `journey.py` puts the operation in `MMW_BREAK`, and `start` must print the exact line `BREAK ARMED <METHOD> <route>`; anything else is a refusal.
_Avoid_: break switch
_Home_: `mmw-v3/skills/ui-acceptance/references/journey.md`

**journey**:
One Playwright path run against the real product on this machine, from a directory under `.mmw/journeys/`. `journey.py run <name>` starts the product, runs the script and stops the product.
_Home_: `mmw-v3/skills/ui-acceptance/references/journey.md`

**`.mmw/harness`**:
The directory in a consuming repository that holds what starts the stack, the **fault-injection switch**, vendor stubs, seeds, and the record of actions that would leave the machine.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**harness guard**:
`harness-guard.py` of the ui-acceptance skill, which checks that the names a repository uses only to make itself drivable stay in their allowed places. It judges files, not a running product.
_Home_: `mmw-v3/skills/ui-acceptance/references/harness-guard.md`

**`harness_markers`**:
The `.mmw/target.json` field declaring a product's own **back doors**; `[]` is a legal answer, and a missing key is not a default.
_Home_: `mmw-v3/skills/ui-acceptance/references/harness-guard.md`, `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**back door**:
A name a repository uses only to make itself drivable for automated acceptance, which must stay inside the places `harness-guard.py` allows (`.mmw/`, `tests/`, `scripts/dev/`, a test file beside the code it tests, or a file `leaves_machine` names). Found anywhere else it is what Meszaros calls Test Logic in Production, and it is a back door in the security sense: a way in that the shipped product keeps, on every customer's machine the release reaches.
_Home_: `mmw-v3/skills/ui-acceptance/references/harness-guard.md`

**negative control**:
The pass an oracle makes to prove it can fail: the story oracle perturbs its inputs, the boundary criterion reruns the test with `MMW_NEGATIVE=1`, and a journey runs with the **fault-injection switch** armed or the product down. The harness guard has none.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/story-parity.py`, `mmw-v3/skills/ui-acceptance/scripts/boundary-check.py`, `mmw-v3/skills/ui-acceptance/scripts/journey.py`

**oracle output line**:
The fixed line an oracle prints to state its verdict or explain a refusal, one set per oracle: `MISS`, `GREEN WITHOUT INTERACTION`, `BOUNDARY OK` (`boundary-check.py`); `JOURNEY OK`, `JOURNEY FAILED`, `JOURNEY GREEN WITH BREAK`, `JOURNEY GREEN WITHOUT PRODUCT`, `JOURNEY LEFT THE PRODUCT UP` (`journey.py`); `STORY OK`, the `DIFF` line and `NEGATIVE CONTROL FAILED` (`story-parity.py`); `HARNESS LEAK`, `HARNESS DESIGN PAGE`, `HARNESS OK` (`harness-guard.py`).
_Home_: `mmw-v3/skills/ui-acceptance/scripts/boundary-check.py`, `mmw-v3/skills/ui-acceptance/scripts/journey.py`, `mmw-v3/skills/ui-acceptance/scripts/story-parity.py`, `mmw-v3/skills/ui-acceptance/scripts/harness-guard.py`

### Screen contract

**screen contract**:
`efforts/<effort>/screen-contract.yaml`: one row per user-visible behaviour — the control, what it calls, which field feeds each shown value, what state follows, what a failure shows — written by the `write-screen-contract` skill. It is a UI's behaviour baseline, beside the design package as its look-and-copy baseline.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**row** (screen-contract row):
One entry of `rows`, the screen contract's list of one row per user-visible behaviour, keyed by the control's `data-ui` id and identified by `trigger` plus `precondition` (the same control in different states is several rows); distinct from `pages` and `scenes`, which declare which story page and which scene each row is visible on, and cannot be derived from `rows`.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**row column**:
One of a row's fixed fields — `id` (the row's own identity, distinct from `trigger`), `component`, `trigger`, `precondition`, `scenes`, `calls`, `shows`, `next`, `on_failure`, `source`, `gap`, and `app` on a cross-component row — each with its own rule.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**cross-component row**:
A screen-contract row on an `App · ` page recording one region's action changing another region's scene. It carries `app`.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has a UI, blocked by every decision ticket and by the **design ticket**, and resolved by running `write-screen-contract` until every row's `gap` is `aligned`.
_Home_: `mmw-v3/skills/mmw-mode/references/interface-and-remake.md`, `mmw-v3/skills/wayfinder/SKILL.md`, `mmw-v3/skills/write-screen-contract/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, which `write-screen-contract` puts to the user to settle.
_Home_: `mmw-v3/skills/write-screen-contract/SKILL.md`

**`extract_skeleton.py`**:
`extract_skeleton.py` of the write-screen-contract skill: one offline render of every scene of a **design package**, writing the **skeleton**. It judges nothing and needs no product.
_Home_: `mmw-v3/skills/write-screen-contract/scripts/extract_skeleton.py`

**skeleton**:
The JSON `extract_skeleton.py` writes: every visible `[data-ui]` control of the design package, keyed by page and **`data-ui` id**, the inventory of controls a screen contract is linted against.
_Home_: `mmw-v3/skills/write-screen-contract/scripts/extract_skeleton.py`, `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**`dump_openapi.py`**:
The write-screen-contract skill's script that calls a FastAPI app factory and writes its OpenAPI document to a file, for a repository with no exporter of its own.
_Home_: `mmw-v3/skills/write-screen-contract/scripts/dump_openapi.py`

**`<scratch>`**:
The `mktemp`-created directory holding a write-screen-contract run's screen contract in progress, until step 8 of Write the screen contract copies it to `efforts/<effort>/`.
_Home_: `mmw-v3/skills/write-screen-contract/SKILL.md`

**`retired_ids`**:
The screen contract's top-level list of row ids that once had a row. An id is never reused.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**`states`** (top-level key):
The screen contract's list of domain and local view-state names `next` and `on_failure` may use when they are not a scene; the lint accepts only this list. Distinct from the **state list**, the fixed `## State list` heading enumerating a prototype's regions and states, and from `state-list.md`, the Claude Design project file carrying that list in.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**`baselines.precedence`**:
The screen contract's top-level string stating which file governs which columns: look and verbatim copy to the design package, `calls`/`shows`/`next`/`on_failure` to the screen contract.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**`proposed_operations`**:
The screen contract's top-level list of operations rows need that `openapi.json` lacks yet; the **reverse sweep** requires every such operation to appear here, in a row's `calls`, or in `backend_without_ui`.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**`backend_without_ui`**:
The screen contract's top-level list of decisions or operations with no control, one line each saying why the UI has no place for it.
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**reverse sweep**:
Step 6 of the `Write the screen contract` playbook, the pass from the backend to the design: every decision an end user could notice lands in a row's `source`, becomes a `backend-only` row, or gets a `backend_without_ui` line, and the **screen-contract lint** requires every operation in `openapi.json` to appear in a row's `calls`, in `backend_without_ui` or in `proposed_operations`. Without a machine-readable `openapi.json` the lint prints `UNVERIFIED` for it.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/write-the-screen-contract.md`, `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

**screen-contract lint**:
Running `lint_screen_contract.py` directly on a screen contract against its skeleton and, optionally, `openapi.json`; narrower than the tickets context's **lint**, `verify-ticket.py --lint`, which runs it as one of several checks.
_Home_: `mmw-v3/skills/write-screen-contract/SKILL.md`

**screen-contract lint output line**:
One of `lint_screen_contract.py`'s own printed lines: `RETIRED <id>: <note>` for every `retired_ids` entry on every run, `UNVERIFIED …` for a row or the whole reverse sweep with no machine-readable source, and the `WARN`/`ERROR` levels the tickets context's lint also uses.
_Home_: `mmw-v3/skills/write-screen-contract/scripts/lint_screen_contract.py`

The ticket kinds a screen contract produces (contract ticket, critical-flow ticket and the rest) and a spec's Critical flows bullet are defined in `docs/contexts/tickets/CONTEXT.md`.

**mount**:
A design page's `mount` in the screen contract's `pages`: the story page id the product serves as `?page=<mount>`, which a story criterion names with `--pages`.
_Avoid_: mount point (for this; a mount point is a UI prototype's scaffolding)
_Home_: `mmw-v3/skills/write-screen-contract/references/screen-contract-format.md`

### Product answers and the scripts that read them

**`design_render.py`**:
`design_render.py` of the ui-acceptance skill, the shared code `story-parity.py` and `extract_skeleton.py` import to serve and render a design page offline and read its `[data-ui]` elements. Nothing in it judges.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/design_render.py`

**product answers**:
What a consuming repository answers in `.mmw/` so the oracles can run its product: `.mmw/target.json`, `.mmw/harness/`, `.mmw/journeys/` and `.mmw/stories/`.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**Claude Design runtime marker**:
One of the four strings (`sc-interp`, `data-dc-tpl`, `data-dc-script`, `dc-root`) that mark an element as drawn by Claude Design's own renderer; neither a story page nor an App page may carry one.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**`target_config.py`**:
`target_config.py` of the ui-acceptance skill, which reads and checks `.mmw/target.json`; `target_config.py --check` lists what a repository has not answered yet.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/target_config.py`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the runtime: what brings the product up and down on this machine, where it answers, where its stories and journeys are, and what it does that reaches past the machine.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**`discover`**:
The `.mmw/target.json` command printing the product's address and its **instance** name; `journey.py` reads every key it prints, uppercased, into the journey script's environment.
_Home_: `mmw-v3/skills/ui-acceptance/references/journey.md`

**`checks`**:
The optional `.mmw/target.json` key listing the repository's own commands, which `dispatch.sh` runs on each ticket's merge result before it pushes; a failing one bounces the ticket with a `Failed checks:` line naming it.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**`stop`**:
The `.mmw/target.json` key that ends what `start` started and nothing else: the only way a run may end a process.
_Home_: `mmw-v3/skills/ui-acceptance/references/product-answers.md`

**`leaves_machine`**:
The required `.mmw/target.json` key answering what the product does in a run that reaches past the machine, and how the run neutralises and records each such action under `MMW_AUTOMATION=1`. `[]` is an answer.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/target_config.py`

### The lease

**lease**:
One ticket worktree's share of this machine: a registration of `worktree path -> slot` under `MMW_HOME/leases`, acquired by a ticket worktree at its first run that needs the product and kept until the ticket's work ends. Unlike a distributed-systems lease it has no term and is never renewed: it ends only by `release`, or when `lease.py`'s `sweep()` finds its worktree gone and nothing listening on its ports. `lease.py` is its whole interface.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/lease.py`

**release** (lease):
Giving a worktree's slot back once nothing still listens on its ports; refuses while a listener remains, because taking it back from a live process is the same act as killing it. Distinct from `ticket.released` and the `RELEASE` line of `status.py --advance-plan` (`docs/contexts/night/CONTEXT.md`).
_Home_: `mmw-v3/skills/ui-acceptance/scripts/lease.py`

**slot**:
What a lease hands out: a block of ports and a data directory that no other slot overlaps, numbered from 0. A machine holds `MMW_LEASE_SLOTS` of them (8 by default); with every one taken, `lease.py claim` exits 4 and the run that needed one reports its ticket blocked.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/lease.py`

**instance**:
One running copy of the product on this machine, one per **slot**, named by `MMW_INSTANCE`; `discover` prints it back as `instance`.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/lease.py`, `mmw-v3/skills/ui-acceptance/scripts/target_config.py`

**`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`**:
The six variables a lease puts into the environment of every command `.mmw/target.json` declares: a readable name for the run, the slot number, the first port and the number of ports of its block, a directory it owns, and `1` as the signal to neutralise what would leave the machine.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/lease.py`

### Refusals

**`REPORT_BLOCKED`**:
The fixed sentence given as a **refusal**'s next step when no command would help: report the ticket blocked and stop, with no wait, retry, environment change or touching another run.
_Home_: `mmw-v3/skills/ui-acceptance/scripts/refusal.py`
