# UI acceptance

How an interface is proved correct by machine: the design package a Claude Design project leaves in the repository, the judges that compare a product story with its design page, run a four-column boundary test twice and run a real journey, the screen contract that says what every control does, and the lease that gives each run its own share of this machine.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

## Language

### The design side

**Claude Design**:
The design tool whose project is the only source of the design: pages are drawn and signed off there, and the repository's **design package** is written only by **pull**.
_Home_: `mmw-v2/skills/design-pages/references/edit-pages.md`

**design system**:
A Claude Design project holding a product's look — variables, fonts, icons and reusable parts — from which the pages of a bound project are drawn; Claude Design copies it into that project's `_ds/<folder>/`. It holds no page regions, example data or product logic.
_Home_: `mmw-v2/skills/design-pages/references/design-system.md`

**edit pages**:
The `design-pages` skill's moment around the user's design work: creating the Claude Design project, bringing an existing product's screens into it, acting on comments sent to Claude, drawing pages when asked, and taking the sign-off.
_Home_: `mmw-v2/skills/design-pages/references/edit-pages.md`

**pull**:
The `design-pages` skill's moment, and its command, that writes the **design package** from a signed-off Claude Design project.
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**pull report**:
`pull-report.md` in the **design package**, written at every **pull**. Its findings do not fail the command.
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**state list**:
The fixed heading `## State list` in a UI prototype's leaf `README.md`: every state of the winning variant, one heading per **region**. On a wayfinder map it is in the **design ticket**'s leaf `README.md`.
_Home_: `mmw-v2/upstream/skills/engineering/prototype/UI.md`

**design ticket**:
The wayfinder ticket that produces the **design package** for a destination with an interface, worked with the `design-pages` skill. It blocks the **alignment ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/references/interface-and-remake.md`

**component**:
A `Component · <name>` design page: one **region** of the screen, the unit acceptance checks, exposing a `scene` prop whose values are that region's accepted states. Distinct from the `component` column of a screen contract's `pages`, which names the **product component**.
_Home_: `mmw-v2/skills/design-pages/references/template-project-claude-md.md`

**product component**:
The product's own component that a **story** page renders and a `pages` entry's `component` column names; on a story page it is presentational and reaches for no backend of its own.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**region**:
One `Component · ` page's area of a screen, named by that page: the `<region>` half of a **`data-ui` id** (`<region>.<part>`).
_Home_: `mmw-v2/skills/design-pages/references/template-project-claude-md.md`

**design package**:
The Claude Design project as it sits in the repository, written only by **pull** into `prototypes/<effort>/claude-design/`: the project's pages, every file they load, and what pull writes beside them. The screen contract's `baselines.look` names it.
_Avoid_: handoff package (for this; `handoff` is the `handoff` skill and `HANDOFF REQUIRED`)
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**scene**:
One value of a design page's `scene` prop, and the matching `scenes.json` entry **pull** writes. The product story is addressed by `?page=&scene=`.
_Home_: `mmw-v2/skills/design-pages/references/template-project-claude-md.md`

**scene input**:
The value in a design-package data file that a design page draws one scene from, declared in the screen contract as `scenes.<name>.input` when the page runs logic over backend-shaped data. The **story adapter** then feeds the product component from it instead of from the **scene data**.
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**scene data**:
The `data` field of a `scenes.json` entry: the displayed values keyed by **`data-ui` id**, which **pull** writes from the offline render and the **story adapter** reads.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**`DESIGN.md`**:
A DESIGN.md-format file a consuming repository may keep. It is not the design source.
_Home_: `docs/adr/0029-claude-design-is-the-design-source.md`

**prototype**:
Code that answers one design question, kept under `prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/` with its question and verdict in the leaf `README.md`. A UI prototype is several structurally different variants on one real route, of which the user picks the winner.
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

**leaf directory**:
`prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/`, one per prototype kind. Its `README.md` is read to its verdict as a `## Read first` item.
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

### The judges

**judge**:
One of the four scripts an acceptance criterion names by its bare name: the **story judge**, `boundary-check.py`, `journey.py` and the **harness guard**.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`data-ui` id**:
The element identity shared by a design page and the matching product element. The story judge pairs elements by it, and a four-column boundary test finds the control by it.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**element parity**:
The story judge's comparison of a product story with its design page, both sides paired by **`data-ui` id**: presence, visibility, text, size, position and the listed style facts, one `DIFF` line per difference.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**story**:
A product page, served from `.mmw/stories/`, that renders the product's own components from the same scene data the design page used, addressed as `?page=<mount>&scene=<name>&viewport=<WxH>`. It has no backend, seed, route or lease.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**user story**:
One line of a spec's `## User Stories`.
_Avoid_: story (for this; a story is the product page the story judge opens)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**story judge**:
`story-parity.py` of the ui-acceptance skill, which decides **element parity** between a product story and the design page it was built from.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**story adapter**:
What puts a **product component** into one scene on a **story** page: one per design page, identified by its `mount`, mapping the scene's **scene data** onto the component.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**boundary**:
In this repository, the word for one class of acceptance criterion and the judge that runs it, the **boundary criterion**. It is not a word for a **seam**.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**four-column boundary test**:
A product test that asserts one screen-contract row's `calls`, `shows`, `next` and `on_failure` together, finding the control by its **`data-ui` id** and replacing the **outbound call module** with a mock.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**outbound call module**:
The layer a consuming repository names as the one that makes outbound calls, over HTTP, IPC or an extension message. A four-column boundary test replaces it with a mock.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**boundary criterion**:
An acceptance criterion running `boundary-check.py --run "<the product's test command>"` against a **four-column boundary test**: the command must pass as written and fail with `MMW_NEGATIVE=1`.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**interaction helper**:
The one shared click-and-fill helper the **contract ticket** delivers, which every four-column boundary test calls to act on the page. Under `MMW_NEGATIVE=1` it does nothing, which is what the boundary criterion's **negative control** relies on.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**break switch**:
The product-owned switch in `.mmw/harness/` that a journey criterion with `--break` arms on its second start, so that the product itself fails one named interface.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**journey**:
One Playwright path run against the real product on this machine, from a directory under `.mmw/journeys/`. `journey.py run <name>` starts the product, runs the script and stops the product.
_Home_: `mmw-v2/skills/ui-acceptance/references/journey.md`

**`.mmw/harness`**:
The directory in a consuming repository that holds what starts the stack, the **break switch**, vendor stubs, seeds, and the record of actions that would leave the machine.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**harness guard**:
`harness-guard.py` of the ui-acceptance skill, which checks that the names a repository uses only to make itself drivable stay in their allowed places. It judges files, not a running product.
_Home_: `mmw-v2/skills/ui-acceptance/references/harness-guard.md`

**negative control**:
The pass a judge makes to prove it can fail: the story judge perturbs its inputs, the boundary criterion reruns the test with `MMW_NEGATIVE=1`, and a journey runs with the **break switch** armed or the product down. The harness guard has none.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/story-parity.py`, `mmw-v2/skills/ui-acceptance/scripts/boundary-check.py`, `mmw-v2/skills/ui-acceptance/scripts/journey.py`

### Screen contract

**screen contract**:
`docs/specs/<effort>/screen-contract.yaml`: one row per user-visible behaviour — the control, what it calls, which field feeds each shown value, what state follows, what a failure shows — written by the `write-screen-contract` skill. It is an interface's behaviour baseline, beside the design package as its look-and-copy baseline.
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**cross-component row**:
A screen-contract row on an `App · ` page recording one region's action changing another region's scene. It carries `app`.
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has an interface, blocked by every decision ticket and by the **design ticket**, and resolved by running `write-screen-contract` until every row's `gap` is `aligned`.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/references/interface-and-remake.md`, `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`, `mmw-v2/skills/write-screen-contract/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, which `write-screen-contract` puts to the user to settle.
_Home_: `mmw-v2/skills/write-screen-contract/SKILL.md`

**`extract_skeleton.py`**:
`extract_skeleton.py` of the write-screen-contract skill: one offline render of every scene of a **design package**, writing the **skeleton**. It judges nothing and needs no product.
_Home_: `mmw-v2/skills/write-screen-contract/scripts/extract_skeleton.py`

**skeleton**:
The JSON `extract_skeleton.py` writes: every visible `[data-ui]` control of the design package, keyed by page and **`data-ui` id**, the inventory of controls a screen contract is linted against.
_Home_: `mmw-v2/skills/write-screen-contract/scripts/extract_skeleton.py`, `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**`retired_ids`**:
The screen contract's top-level list of row ids that once had a row. An id is never reused.
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

The ticket kinds a screen contract produces (contract ticket, acceptance ticket and the rest) and a spec's Critical flows bullet are defined in `docs/contexts/tickets/CONTEXT.md`.

**mount**:
A design page's `mount` in the contract's `pages`: the story page id the product serves as `?page=<mount>`, which a story criterion names with `--pages`.
_Avoid_: mount point (for this; a mount point is a UI prototype's scaffolding)
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

### The runtime a repository answers for

**`design_render.py`**:
`design_render.py` of the ui-acceptance skill, the shared code `story-parity.py` and `extract_skeleton.py` import to serve and render a design page offline and read its `[data-ui]` elements. Nothing in it judges.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/design_render.py`

**product answers**:
What a consuming repository answers in `.mmw/` so the judges can run its product: `.mmw/target.json`, `.mmw/harness/`, `.mmw/journeys/` and `.mmw/stories/`. Answering them makes the repository an acceptance runtime.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`target_config.py`**:
`target_config.py` of the ui-acceptance skill, which reads and checks `.mmw/target.json`; `target_config.py --check` lists what a repository has not answered yet.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/target_config.py`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the runtime: what brings the product up and down on this machine, where it answers, where its stories and journeys are, and what it does that reaches past the machine.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`checks`**:
The optional `.mmw/target.json` key listing the repository's own commands, which `--closeout` runs after an `ALL MET` draft is accepted and before the ticket closes, posting them as a `ticket.checked` of run `repo-checks`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`stop`**:
The `.mmw/target.json` key that ends what `start` started and nothing else: the only way a run may end a process.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`leaves_machine`**:
The required `.mmw/target.json` key answering what the product does in a run that reaches past the machine, and how the run neutralises and records each such action under `MMW_AUTOMATION=1`. `[]` is an answer.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

### The lease

**lease**:
One run's share of this machine: a registration of `worktree path -> slot` under `MMW_HOME/leases`, claimed by a ticket worktree at its first run that needs the product and kept until the ticket's work ends. `lease.py` is its whole interface.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`

**slot**:
What a lease hands out: a block of ports and a data directory that no other slot overlaps, numbered from 0.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`

**instance**:
One run of a product on this machine, and the optional `.mmw/target.json` field `instance`, which says how many one machine may hold at once (`max`) and why.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`**:
The six variables a lease puts into the environment of every command `.mmw/target.json` declares: a readable name for the run, the slot number, the first port and the number of ports of its block, a directory it owns, and `1` as the signal to neutralise what would leave the machine.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`
