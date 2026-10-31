# UI acceptance

UI design decisions, shared testing methods and product or formal checks used for acceptance. A product verification skill owns its run recipe and feature map; its implementation and delivery remain with the calling workflow.

## Language

### The design side

**design freeze**:
The point at which the owner approves the running winner prototype. Later design changes go through a `contract` child or a new prototype round. ADR [0066](../../adr/0066-ui-design-and-verification-have-distinct-owners.md) distinguishes this from repairs and behavior-preserving work that use a settled real-product baseline.

**API fake**:
A working, non-production implementation of the prototype's missing interfaces, in Martin Fowler's test-double sense. Existing interfaces use the real local backend, except referenced entities supplied by the fake to keep identifiers consistent; sample data comes from the environment tool's test seed data, and changes live in sessionStorage.

**environment tool**:
The product repository's development commands and operating skill for starting the whole product locally, with a backend and database per checkout and test accounts. The product's verification skill calls it rather than owning separate environment scripts.

### The acceptance side

**`verify-<product>`**:
The product-local verification skill holding its launch, observation, interaction, evidence and cleanup knowledge with its feature map. Acceptance preparation first uses its recipe to build tests; implementation, review and delivery reuse its actual instructions and commands.
_Avoid_: 产品验证技能

**feature map**:
One product's maintained account of its user-facing features, one feature file per feature under `.agents/skills/verify-<product>/features/`. It has no hand-written index or status field; test coverage is in each file's header, and unfinished work is on tickets.

**feature file**:
One product feature's user-facing description and proof, linked to its route and tests in its header. It belongs to the feature map rather than a queue of unfinished implementation.
_Avoid_: 功能文件

**e2e test**:
A fixed-step test of what a user sees or accomplishes, with its configuration and assets under the product's e2e directory. Settled daytime acceptance remains read-only to the nighttime worker.

**`e2e.config.ts`**:
The product's e2e configuration under `tests/e2e/<product>/`, defining the product and design targets without a model. Every e2e command names this config so it selects the intended product.

**`product` target**:
The configured target running the real product with its real local backend for implementation verification. It is distinct from the design target and the shipping product in Release.

**`design` target**:
The configured target rendering the chosen prototype for daytime acceptance preparation and comparison. It is distinct from the real-product target run during implementation.

**CHECK line**:
The product verification skill's executable acceptance recipe copied into a criterion. It includes the preparation and selected target required to run that product test.

**Isolate**:
The two required layers of separation: each product run has its own port and fresh data directory, and each checkout has its own back-end stack. Test workers within one run do not separate two tickets' runs.

**known-issues**:
The shared verification-tool problem list, read during generation and maintenance. Problems shared by similar products belong here; product-specific guidance belongs in that product's Doctor or Gotchas.

**prerequisite ticket**:
A problem registered with the register-problem skill for a product that cannot meet either isolation layer. Its fix must land before that product gets UI tickets.

**smoke ticket**:
The first night's ticket proving a new project's product launch and reachable home page when generation could prove only the design target. It completes the product-side launch proof left pending at handover.

**pin**:
A criterion or test preserving required existing behavior, demonstrated green before and after a behavior-preserving change. It is distinct from behavioral-red proof for newly added or repaired behavior.

**doc drift**:
A wrong or missing user-facing description, including disagreement between a feature file's test list and the test files. Maintenance corrects the feature map and e2e tests rather than changing the product to fit the description.

**harness gap**:
Working product behavior that the verification environment cannot drive. Maintenance repairs the environment and proves the repair live before shipping it.

**product gap**:
Product behavior that is actually broken, rather than a description or environment error. Maintenance opens a problem ticket and leaves the product fix outside its own changes.

**`contract` child (UI acceptance)**:
The ticket child reporting an incorrect frozen acceptance test or prototype baseline. It uses the ticket-run contract correction path rather than authorizing the worker to weaken the baseline.

**prepare-ui-acceptance**:
The [skill](../../../mmw-v4/skills/prepare-ui-acceptance/SKILL.md) preparing one change's fixed-step UI tests and feature registration from an approved new design, a reproduced repair requirement or current behavior to preserve. It uses existing product-running instructions and returns to its preparation caller.

**Design a UI**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/design-a-ui.md) owning a UI design through the owner's trial, iteration and confirmation of a runnable winner. The prototype skill constructs the pages; implementation preparation and execution remain with their original callers.

### The prototype side

**prototype artifact**:
The code artifact produced to answer a question through the prototype skill. Its verdict is an implementation baseline, with a UI winner's appearance and interaction preserved while production code is rewritten.

**leaf directory**:
The directory of one prototype question and branch under `efforts/<effort>/prototypes/`. UI candidates and the selected winner share that question's directory.

**development effort**:
One whole development destination and its durable assets, held under `efforts/<effort>/`. A map or independent change supplies its identity; it is distinct from a model's reasoning effort.

**effort branch**:
The branch carrying the effort's preparation, decisions and verification assets until accepted delivery. It is distinct from an implementation ticket branch.

**mount point**:
The environment-variable-controlled entry that renders the winner at the feature file's final `Route:`, or in the rendering module for a UI without its own route. Each page has its own entry, with one shared switcher for variants; entries stay until implementation and are removed per page by the last ticket, or the final commit of a single ticket.
_Avoid_: 挂载点

**shell**:
The HTML page around a logic prototype's pure module, or the harness around an experiment's reusable code. It stays with the prototype to run again, while production draws on the code it wraps.

**experiment round**:
One run or batch of runs answering an experiment's question under one parameter set, distinct from the tickets context's round. One comment on the experiment's ticket records each round.

**evidence page**:
The static HTML page an experiment generates at the end of each run, showing outputs as a comparison grid or catalogue. It reports facts, while comments on the ticket record observations and the conclusion.

**evidence scratch directory**:
The git-ignored `.scratch/<effort>/<issue>/evidence/<name>/` where an experiment writes its evidence page and media. The generator stays committed in the leaf directory, so this output can be reproduced after deletion once the approach is settled.

**`prototype`**:
The [skill](../../../mmw-v4/skills/prototype/SKILL.md) for building or updating a bounded UI, LOGIC, EXP or SKETCH artifact that answers its caller's question. Design a UI owns the full UI design interaction. The resulting prototype artifact is evidence for production work rather than shipping implementation.

**UI, LOGIC, EXP and SKETCH**:
The prototype branch family for appearance and interaction, state and logic exploration, empirical implementation questions and unresolved cross-ticket code shape. Each branch supplies its own artifact and comparison method.

### Verification maintenance

**feature map review**:
An owner-requested whole-product maintenance run by maintain-verification-skill, comparing the live product with its verification assets. Its clean, changed or blocked result is distinct from the bounded Find affected features lookup.

**`create-verification-skill`**:
The [skill](../../../mmw-v4/skills/create-verification-skill/SKILL.md) for generating a product-local verification recipe, feature map and deterministic acceptance setup from the actual product or settled prototype.

**`maintain-verification-skill`**:
The [skill](../../../mmw-v4/skills/maintain-verification-skill/SKILL.md) for finding affected existing features or performing owner-requested whole-product maintenance. Find affected features returns a bounded list without launching that maintenance.

**Find affected features**:
The maintain-verification-skill entry identifying the existing feature descriptions touched by planned work. Its result records which affected behaviors stay unchanged or change.

### Formal verification

**create-formal-verification-skill**:
The [skill](../../../mmw-v4/skills/create-formal-verification-skill/SKILL.md) establishing a rerunnable check of an important agreed rule against real code and generating project-local instructions for later related edits. Its proof records the assumptions and checked scope rather than claiming the whole product is correct.

**maintain-formal-verification-skill**:
The [skill](../../../mmw-v4/skills/maintain-formal-verification-skill/SKILL.md) reconciling existing formal checks with code changes that skipped their normal update method. Its per-check result distinguishes current correspondence, an updated check, a product bug and a blocked check.

**formal verification skill**:
A project-local skill identifying the actual code and rule checked by a model checker, proof or code-level verifier, with its command, tool version, assumptions, bounds and last correspondence commit. Its name follows the code area; a verify-* prefix alone does not distinguish it from product-driving instructions.

**sync commit**:
The code commit at which a formal check was last confirmed to describe the covered code. Advancing it records a completed correspondence check, not merely a passing stale model.

### Testing methods

**`test-audit`**:
The [skill](../../../mmw-v4/skills/test-audit/SKILL.md) owning testing judgments for writing, reviewing, selecting, diagnosing and maintaining tests, including TDD and behavior pins. It returns testing decisions and evidence within its caller's scope rather than starting another delivery workflow.

**behavioral red**:
A test failure demonstrating the missing or broken behavior before its repair. It is distinct from a missing test file, broken fixture or command that could not start.

**negative control**:
A bounded deliberate break of the promised behavior establishing that its test can detect that break. Its failure is evidence of test sensitivity rather than an acceptable product state.

**test contract**:
The observable behavior, invariant or independent interface promise a test protects. Its primary proof owner is distinct from duplicate tests of the same implementation details.

### Product control

**`control-ui`**:
The [skill](../../../mmw-v4/skills/control-ui/SKILL.md) for driving and inspecting a browser, Electron or web UI through a local harness, including screenshots, traces and profiles.

**`control-cli`**:
The [skill](../../../mmw-v4/skills/control-cli/SKILL.md) for driving and inspecting an interactive CLI or TUI through a local harness, including terminal behavior and runtime evidence.
