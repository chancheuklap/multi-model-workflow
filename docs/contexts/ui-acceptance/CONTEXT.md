# UI acceptance

How signed-off pages come from Claude Design into a design package, and how a product's `verify-<product>` skill and e2e tests prove the product. The design package is the UI's standard answer; verification assets are written in the day and read-only at night.

## Language

### The design side

**Claude Design**:
The design tool where the owner signs off a product's pages. Its project is the source of the repository's design package.
_Home_: `mmw-v4/skills/design-pages/SKILL.md`

**Claude Design agent**:
The agent inside a Claude Design project, separate from the repository session. It reads that project's root `CLAUDE.md`, follows the selected task sheet, and reads pushed repository code through Claude Design's GitHub connection.
_Home_: `mmw-v4/skills/design-pages/SKILL.md`

**design system**:
A product's Claude Design project holding its visual variables, fonts, icons, and reusable parts, without product logic or whole page regions. A bound page project holds a copy under `_ds/<folder>/` that the design-pages session refreshes after a change.
_Home_: `mmw-v4/skills/design-pages/references/design-system.md`, `mmw-v4/skills/design-pages/references/template-design-system-claude-md.md`

**page project**:
One long-lived Claude Design project per product, bound to its design system and holding the pages the owner designs. For an existing product, a task redraws only the pages it changes, from current code.
_Home_: `mmw-v4/skills/design-pages/references/pages.md`

**`tasks/<n>.md`**:
A page project's task sheet for the calling ticket n, naming its pages, states, references, and completion criteria. Sheets without a top `Pulled:` line reserve their listed pages for that task, since Claude Design has no branches.
_Home_: `mmw-v4/skills/design-pages/SKILL.md`, `mmw-v4/skills/design-pages/references/pages.md`, `mmw-v4/skills/design-pages/references/pull.md`

**`设计决策记录.md`**:
The page-project file recording decisions made while drawing, under the current task's number, marked `已确认` or `待确认`. Pull registers each pending decision's ticket before downloading; confirmed decisions accompany the pages as baseline.
_Home_: `mmw-v4/skills/design-pages/references/template-page-project-claude-md.md`, `mmw-v4/skills/design-pages/references/pull.md`

**pull**:
The design-pages skill's part C, which registers decisions and uses `scripts/pull_design.py` to bring only the task's signed-off pages and their files into the repository. Its commit goes directly to the project branch.
_Home_: `mmw-v4/skills/design-pages/references/pull.md`

**design package**:
The signed-off Claude Design pages and their files in `design/<product>/`, written by pull. It is the baseline for the UI's appearance, copy, and interactions, with confirmed design decisions included.
_Home_: `mmw-v4/skills/design-pages/SKILL.md`, `mmw-v4/skills/design-pages/references/pull.md`

### The acceptance side

**`verify-<product>`**:
The product-local verification skill generated under `.agents/skills/verify-<product>/`. It holds the knowledge of launching, checking, driving, capturing evidence, and cleaning up that product, together with its feature map.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**feature map**:
One product's maintained account of its user-facing features, one feature file per feature under `.agents/skills/verify-<product>/features/`. It has no hand-written index or status field; test coverage is in each file's header, and unfinished work is on tickets.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**feature file**:
One feature's file, starting with its name, `Route:`, and `Tests:` on three lines. Its `Proof` names the observable end state on screen and in side-effect stores; `Gotchas` records prerequisites and local limits that can look like defects.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**e2e test**:
A fixed-step test under `tests/e2e/<product>/` that proves a user path and its side effects. It is written in the day from current code for existing behavior or from the design package for a new feature, and read-only at night.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**`e2e.config.ts`**:
The product's e2e configuration under `tests/e2e/<product>/`, defining the product and design targets without a model. Every e2e command names this config so it selects the intended product.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**`product`** (target):
The e2e target that runs the real product against its real local back end. It is the target used at night.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**`design`** (target):
The e2e target that serves `design/<product>/` through a local static server for the same tests' assertions. It runs during daytime test writing or maintenance, not at night.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**CHECK line**:
The complete command a ticket copies from its product's verification skill's Launch section. It installs dependencies, performs required preparation, and runs the ticket's test file against the product target with its own trace output.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**Isolate**:
The two required layers of separation: each product run has its own port and fresh data directory, and each checkout has its own back-end stack. Test workers within one run do not separate two tickets' runs.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**ensure script**:
The Launch helper that removes stacks whose checkout is gone, reuses this checkout's reachable stack, and starts it when unreachable. Runs in the same checkout share that stack; the helper uses its existing idempotent lifecycle command.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**prerequisite ticket**:
A problem ticket for a product that cannot meet either isolation layer. It must land before that product gets UI tickets.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**smoke ticket**:
The first night's ticket proving a new project's product launch and reachable home page when generation could prove only the design target. It completes the product-side launch proof left pending at handover.
_Home_: `mmw-v4/skills/create-verification-skill/SKILL.md`

**pin**:
A criterion preserving an existing behavior that the ticket must keep. It passes on the base before the change, unlike a criterion for behavior the ticket adds.
_Home_: `mmw-v4/skills/mmw-mode/playbooks/to-tickets.md`

**doc drift**:
A wrong or missing user-facing description, including disagreement between a feature file's test list and the test files. Maintenance corrects the feature map and e2e tests rather than changing the product to fit the description.
_Home_: `mmw-v4/skills/maintain-verification-skill/SKILL.md`

**harness gap**:
Working product behavior that the verification environment cannot drive. Maintenance repairs the environment and proves the repair live before shipping it.
_Home_: `mmw-v4/skills/maintain-verification-skill/SKILL.md`

**product gap**:
Product behavior that is actually broken, rather than a description or environment error. Maintenance opens a problem ticket and leaves the product fix outside its own changes.
_Home_: `mmw-v4/skills/maintain-verification-skill/SKILL.md`

**`contract` child** (UI acceptance):
A ticket's child reporting that its e2e test or design package is wrong. Those assets stay unchanged at night; the worker abandons the affected criterion as stuck and hands the ticket back for daytime correction.
_Home_: `mmw-v4/skills/mmw-mode/playbooks/work-a-ticket.md`, `mmw-v4/skills/mmw-mode/playbooks/run-a-night.md`

### The prototype side

**prototype**:
Code that answers one question, kept with its question and verdict in a leaf directory rather than shipped directly. A winning UI variant becomes signed-off pages through design-pages; the production implementation is written from the settled answer.
_Home_: `mmw-v4/skills/prototype/SKILL.md`, `mmw-v4/skills/prototype/UI.md`

**leaf directory**:
`efforts/<effort>/prototypes/<issue>/<UI|LOGIC|EXP|SKETCH>/`, one prototype branch's code and `README.md` holding its question, current conclusion, and what the real code has taken. The issue is a ticket number or a short feature name when there is no ticket.
_Home_: `mmw-v4/skills/prototype/SKILL.md`

**effort** (`<effort>`):
The development effort's directory name under `efforts/`, taken from the filing map's `## Notes` or otherwise the current branch name with `/` replaced by `-`, as lowercase ASCII words joined by `-`. Distinct from the toolbox's `effort`, a model's reasoning effort.
_Home_: `mmw-v4/skills/prototype/SKILL.md`

**scaffolding**:
The mount point, prototype route, switcher, and any route-side symlink that let UI variants render in the app. It comes down after the winner is recorded, leaving the variants in their leaf directory as reference.
_Home_: `mmw-v4/skills/prototype/UI.md`

**shell**:
The HTML page around a logic prototype's pure module, or the harness around an experiment's reusable code. It stays with the prototype to run again, while production draws on the code it wraps.
_Home_: `mmw-v4/skills/prototype/LOGIC.md`, `mmw-v4/skills/prototype/EXP.md`

**experiment round**:
One run or batch of runs answering an experiment's question under one parameter set. The leaf `README.md` records each round under `Rounds`, newest first.
_Avoid_: round (bare for this; the tickets context's round is a different unit of work)
_Home_: `mmw-v4/skills/prototype/EXP.md`

**evidence page**:
The static HTML page an experiment generates at the end of each run, showing outputs as a comparison grid or catalogue. It reports facts, while the leaf `README.md` records observations and the conclusion.
_Home_: `mmw-v4/skills/prototype/EXP.md`, `mmw-v4/skills/prototype/evidence-page.md`

**evidence scratch directory**:
The git-ignored `.scratch/<effort>/<issue>/evidence/<name>/` where an experiment writes its evidence page and media. The generator stays committed in the leaf directory, so this output can be reproduced after deletion once the approach is settled.
_Home_: `mmw-v4/skills/prototype/EXP.md`
