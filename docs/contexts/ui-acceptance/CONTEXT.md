# UI acceptance

How a local prototype becomes the UI baseline, and how a product's `verify-<product>` skill and e2e tests prove the product. The owner approves the winner at design freeze; the prototype and verification assets are read-only at night.

## Language

### The design side

**design freeze**:
The point at which the owner approves the running winner prototype. Later design changes go through a `contract` child or a new prototype round.

**API fake**:
A working, non-production implementation of the prototype's missing interfaces, in Martin Fowler's test-double sense. Existing interfaces use the real local backend, except referenced entities supplied by the fake to keep identifiers consistent; sample data comes from the environment tool's test seed data, and changes live in sessionStorage.

**environment tool**:
The product repository's development commands and operating skill for starting the whole product locally, with a backend and database per checkout and test accounts. The product's verification skill calls it rather than owning separate environment scripts.

### The acceptance side

**`verify-<product>`**:
The product-local verification skill generated under `.agents/skills/verify-<product>/`. It holds the knowledge of launching, checking, driving, capturing evidence, and cleaning up that product, together with its feature map.
_Avoid_: 产品验证技能

**feature map**:
One product's maintained account of its user-facing features, one feature file per feature under `.agents/skills/verify-<product>/features/`. It has no hand-written index or status field; test coverage is in each file's header, and unfinished work is on tickets.

**feature file**:
One feature's file, starting with its name, `Route:`, and `Tests:` on three lines. Its user-facing description comes from the winner, settled decisions and glossary before design freeze; `Proof` records what the user sees and can accomplish, while `Gotchas` records prerequisites and local limits that can look like defects.
_Avoid_: 功能文件

**e2e test**:
A fixed-step test under `tests/e2e/<product>/` that proves what a user sees and can accomplish. It is written in the day from current code for existing behavior or from the winner prototype for new behavior, with the same steps and assertions on both targets, and is read-only at night; backend tests prove real storage.

**`e2e.config.ts`**:
The product's e2e configuration under `tests/e2e/<product>/`, defining the product and design targets without a model. Every e2e command names this config so it selects the intended product.

**`product`** (target):
The e2e target that runs the real product against its real local back end. It is the target used at night.

**`design`** (target):
The e2e target that renders the winner prototype. For an existing web or Electron product, it uses the product's launch command with one environment variable; a new project starts its standalone prototype page. Daytime test writing proves it green, and Spec review uses it for screenshot pairs; nightly CHECK lines use `product`.

**CHECK line**:
The complete command a ticket copies from its product's verification skill's Launch section. It installs dependencies, performs required preparation, and runs the ticket's test file against the product target with its own trace output.

**Isolate**:
The two required layers of separation: each product run has its own port and fresh data directory, and each checkout has its own back-end stack. Test workers within one run do not separate two tickets' runs.

**known-issues**:
The shared verification-tool problem list, read during generation and maintenance. Problems shared by similar products belong here; product-specific guidance belongs in that product's Doctor or Gotchas.

**prerequisite ticket**:
A problem registered with the register-problem skill for a product that cannot meet either isolation layer. Its fix must land before that product gets UI tickets.

**smoke ticket**:
The first night's ticket proving a new project's product launch and reachable home page when generation could prove only the design target. It completes the product-side launch proof left pending at handover.

**pin**:
A criterion preserving an existing behavior that the ticket must keep. It passes on the base before the change, unlike a criterion for behavior the ticket adds.

**doc drift**:
A wrong or missing user-facing description, including disagreement between a feature file's test list and the test files. Maintenance corrects the feature map and e2e tests rather than changing the product to fit the description.

**harness gap**:
Working product behavior that the verification environment cannot drive. Maintenance repairs the environment and proves the repair live before shipping it.

**product gap**:
Product behavior that is actually broken, rather than a description or environment error. Maintenance opens a problem ticket and leaves the product fix outside its own changes.

**`contract` child** (UI acceptance):
A ticket's child reporting that its e2e test or winner prototype is wrong. Those assets stay unchanged at night; the worker abandons the affected criterion as stuck and hands the ticket back for daytime correction.

### The prototype side

**prototype**:
Code that answers a question in a leaf directory. A UI prototype is a complete, interactive design in the product's code, iterated with the owner; its winner is the appearance and interaction baseline, rewritten to production standards rather than shipped directly. Its conclusion lives in the feature file; LOGIC, EXP and SKETCH keep their verdict in a comment on the ticket that asked the question.

**leaf directory**:
`efforts/<effort>/prototypes/<issue>/<UI|LOGIC|EXP|SKETCH>/`, one prototype branch's code. UI keeps `winner/` and `candidates/<n>/`, with its conclusion in the feature file; LOGIC, EXP and SKETCH record their question, current conclusion, and what the real code has taken in a comment on the ticket that asked the question. The issue is a ticket number or a short feature name when there is no ticket.

**effort** (`<effort>`):
One whole piece of development work toward one destination: a wayfinder map with the research, prototypes, specs and nights it gives rise to, or one ticket outside any map that opened a `fix-<n>`. Its files live under `efforts/<effort>/`, the name taken from the map's `## Notes` or otherwise the current branch name with `/` replaced by `-`, as lowercase ASCII words joined by `-`. A lone Investigation or code review is not an effort. Distinct from the toolbox's `effort`, a model's reasoning effort.

**effort branch**:
The one branch an effort's work is committed on, cut from the project branch when the effort starts: for a map, when the map is created, and it becomes the night's branch; for a ticket outside any map, its `fix-<n>`. It reaches the project branch only through a pull request the owner accepts.
_Avoid_: base branch (for where an effort's commits go), proto-<n>

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
