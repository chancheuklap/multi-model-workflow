# UI acceptance

How an interface is proved correct by machine: the design-side baselines a Claude Design project leaves behind, the judges that compare a product story against the design side, run a four-column boundary test twice, and run a real journey, the screen contract that says what every control does, and the lease that gives each run its own share of this machine. It exists because a UI judgement that no command decides is not an acceptance criterion, and because several agents run on one machine at once.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### The design side

**Claude Design**:
The design tool whose project is the only source of the design. Pages are written and signed off there; the repository's **handoff package** is written only by **pull**. Its page format is what `get_claude_design_prompt` returns when the **design system** is bound.
_Home_: `mmw-v2/skills/design-pages/references/edit-pages.md`

**design system**:
The first of the three design-pages entries, and the Claude Design artifact it builds from code that already runs, before any page is drawn. Distinct from **`DESIGN.md`**, which is not that source.
_Home_: `mmw-v2/skills/design-pages/references/design-system.md`

**edit pages**:
The second of the three design-pages entries: create the Claude Design project, write pages, check the preview after every change, act on comments, and take the user's sign-off. Page conventions live only in the project root `CLAUDE.md`, copied from `template-project-claude-md.md`.
_Avoid_: Porting (as an entry name)
_Home_: `mmw-v2/skills/design-pages/references/edit-pages.md`

**pull**:
The third of the three design-pages entries, and the command that writes the **handoff package**. It runs after sign-off, and later only in a session handling a design-class `contract` child.
_Avoid_: Handoff (as an entry name)
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**pull report**:
`pull-report.md` in the **handoff package**, written every **pull**. Findings do not fail the command.
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**state list**:
The fixed heading `## State list` in a UI prototype's leaf `README.md`: every state of the winning variant, one third-level heading per region and one list item per state starting with the state name. `scene` prop values reuse those names; the **pull report** matches them by name.
_Home_: `mmw-v2/upstream/skills/engineering/prototype/UI.md`

**handoff ticket**:
The wayfinder ticket that produces the **handoff package** for a destination with an interface: a `prototype` ticket, HITL, blocked by every `prototype` decision ticket and by every decision ticket that will change a page's states, worked with the design-pages skill. The first line of its body names that skill's **edit pages** and **pull** entries. It is what blocks the **alignment ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**component**:
A `Component · <name>` design page: one region the user sees as a unit, split that way rather than by code modules or directories. It exposes a `scene` enum prop whose values are that region's accepted states, taken from the **state list**. Language and directory of the matching product component are the product's; this entry does not name either. The `component` column of a screen contract's `pages` is a different thing — the product component that owns that page — and is defined in `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`.
_Avoid_: design component, scenario, scenario 属性, 状态开关
_Home_: `mmw-v2/skills/design-pages/references/template-project-claude-md.md`

**handoff package**:
The Claude Design project as it sits in the repository, written only by **pull** into the directory the command names — the project's `.dc.html` pages and what **pull** writes beside them. The screen contract's `baselines.look` names it; once pulled it is a contract, copied verbatim. A local edit is not blocked; the next pull overwrites it and the **pull report** says so.
_Avoid_: 交接包, 开发交接包, 基线目录, UI 基线
_Home_: `mmw-v2/skills/design-pages/references/pull.md`

**scene**:
One value of a design page's `scene` prop, and the matching `scenes.json` entry **pull** writes from those options. The screen contract declares every scene once under `scenes`. The product story is addressed by `?page=&scene=`. Values listed under `out_of_scope` do not become scenes.
_Avoid_: 场景 (when a scene is meant), 场景列表, scenario, 状态
_Home_: `mmw-v2/skills/design-pages/references/template-project-claude-md.md`

**scene data**:
The `data` field of a `scenes.json` entry: displayed values keyed by `data-ui` id, nested where an element with that id contains another, a document-order list where the same id appears more than once. **pull** writes it from the same offline render the story judge uses. The product story's **story adapter** reads the same object.
_Avoid_: fixture props (when this field is meant)
_Home_: `mmw-v2/skills/design-pages/scripts/pull_design.py`

**`DESIGN.md`**:
A DESIGN.md-format file a consuming repository may still keep. It is not the design source and not what pages are drawn from.
_Home_: `docs/adr/0029-claude-design-is-the-design-source.md`

**prototype**:
Code that answers one design question, kept in the repository under `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/` and iterated as the answer sharpens; the real implementation is written with it as reference. Its question and verdict live in the leaf `README.md`; it has no tests. A UI prototype is several structurally different **variants** (default three, at most five) on one real route, switched by `?variant=`; the user picks the winner, `?variant=<winner>`. The mount point, symlink, and switcher that let variants render inside the real app are **scaffolding**, taken down in step 7 of `prototype/UI.md`; a **prototype route** is one created for the variants and deleted with the rest of the scaffolding in that step. A prototype's chosen artifact — the winning variant, the validated logic module, an experiment's Reusable parts with its Conclusion — is a baseline source.
_Avoid_: throwaway (for this), 一次性分支, 原型 (as a term), 研究件, UI variation (in this repository's text), throwaway route, 挂载点连同软链
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

**leaf directory**:
`prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, one per prototype kind; `<task>` is the development effort — the wayfinder map's title where there is one — and `<issue>` is the ticket number, or a short feature name when there is no ticket. A UI prototype's variants live in the `UI/` one; **pull** writes the **handoff package** into the directory the command names, which may be that leaf. Once folded in, it is the only home a prototype has. Its `README.md` is the **leaf README.md**, read to its verdict as a `## Read first` item.
_Avoid_: 叶子目录, the leaf (bare)
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

### The judges

**`data-ui` id**:
The common element identity on a design page and on the matching product element. The **story judge** pairs by this id; a **four-column boundary test** finds the control by it.
_Avoid_: test hook (for this), data-testid (when this identity is meant)
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**element parity**:
The story judge's comparison: the same scene, viewport and scene data, both sides paired by **`data-ui` id**, then presence, visibility, text, size and position, and the listed style facts. One difference is one `DIFF` line naming the id and the property. Pixel difference images are evidence; they do not decide the exit code. `Component · ` and `App · ` pages use the same comparison.
_Avoid_: interface parity, visual parity
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**story**:
A product page that renders the product's own components from the same scene data the design page used, addressed as `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. A `Component · ` page is that component in one scene; an `App · ` page is the story service composing those components into a whole page. It lives in `.mmw/stories/`; the product's `stories` command prints `origin`. No backend, no seed, no route — and no lease: the service takes a port the machine hands out, so a story criterion costs no instance slot.
_Avoid_: storybook (when this page is meant), preview page
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**user story**:
One line of a spec's `## User Stories`.
_Avoid_: story (for this)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**story judge**:
`scripts/story-parity.py` beside the ui-acceptance `SKILL.md`: it decides **element parity** between a product story and the design page it was built from. Given `--contract` and `--pages <mount,…>` (and `--scenes` to narrow), it starts the `stories` command, opens each scene at each contract viewport, captures `[data-story-root]`, renders the design page offline in that same window, and compares both sides by **`data-ui` id**. It prints `STORY OK <passed>/<total>` (exit 0), or one `DIFF` line per failing fact (exit 1), or `NEGATIVE CONTROL FAILED` (exit 2). It refuses a contract with a non-empty `volatile_values` list or a `retired_ids` entry that carries `trigger`, and a product story that carries a Claude Design runtime. `--render-only` renders the design side alone. No address is on its line: a `CHECK:` names it bare, and `verify-ticket.py --tools` puts the ui-acceptance skill's `scripts/` on the `PATH` of the shell that runs it.
_Admitted_: `story-parity.py`
_Avoid_: interface parity, PARITY OK (the whole-product judge's success line)
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**story adapter**:
What puts a product's presentational component into one scene on a **story** page: one adapter per design page, identified by that page's `mount`, so a `?page=` with no adapter is a 404. Language and directory are the product's; the adapter takes the scene's **scene data** and maps those fields onto the component. The screen contract's `shows` column for each row says which field feeds which displayed value, and the `code-review` Spec axis checks that mapping field by field. It reaches for no backend, no seed and no route — the page puts the component in the scene by itself. The contract ticket lands the first one as the precedent every later interface ticket copies. `adapter` is a dead word on the **target** side only; this is the sense that stays.
_Home_: `mmw-v2/skills/ui-acceptance/references/story-parity.md`

**boundary**:
In this repository the word names one class of acceptance criterion and the judge that runs it: a **boundary criterion**, in the fixed shape of `references/boundary-check.md`, run by `boundary-check.py`. It is not a word for a **seam**.
_Avoid_: boundary (as a word for a seam)
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**four-column boundary test**:
A product test that asserts one screen-contract row's `calls`, `shows`, `next` and `on_failure` in the same test, locates the control by its **`data-ui` id**, and replaces the **outbound call module** with a mock. A cross-component row is the same test at whole-page composition. The **boundary criterion** is what runs it.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**outbound call module**:
The layer the consuming repository names as the one that emits outbound calls, whether they travel as HTTP, IPC, or an extension message. A **four-column boundary test** replaces this module with a mock; stubbing `fetch`, msw, nock or fetch-mock is not that seam.
_Avoid_: API client module (when this layer is meant)
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**boundary criterion**:
An acceptance criterion in the fixed shape of `references/boundary-check.md`, running `scripts/boundary-check.py --run "<the product's test command>"` against a **four-column boundary test**: the command is run twice in this process's cwd, first as written (must exit 0), then with `MMW_NEGATIVE=1` (must exit non-zero). `--run` takes one command, not a shell line, and may be repeated. Prints `BOUNDARY OK <n>/<n>`, or `MISS <command> — <last 20 lines>` when the first pass is already red, or `GREEN WITHOUT INTERACTION <command> — <why>` when the second pass is also green.
_Admitted_: boundary check
_Avoid_: wiring criterion, wiring-check.py, WIRING OK
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**mutation check**:
The second pass of a boundary criterion: the same command, with `MMW_NEGATIVE=1`, must go red. The product's shared interaction helper does nothing under that variable, so an assertion that does not depend on the click stays green and is refused. It is mechanical; a reviewer does not read the test to decide whether it can fail.
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**interaction helper**:
The one shared click-and-fill helper a consuming repository's **contract ticket** delivers, which every **four-column boundary test** calls instead of touching the page itself; it finds the control by its **`data-ui` id**. Under `MMW_NEGATIVE=1` it does nothing, and that is what makes the **mutation check** mechanical: a test whose assertion really depends on the interaction goes red on that second pass, while one that is true without the click stays green and is reported rather than passed. It is the interaction half of the boundary seam — the other half is the **outbound call module**, which the test replaces with a mock.
_Avoid_: click helper, 交互 helper, page object (for this)
_Home_: `mmw-v2/skills/ui-acceptance/references/boundary-check.md`

**break switch**:
The product-owned switch in `.mmw/harness/` that a journey criterion with `--break` arms on the second start. It is what distinguishes a journey's **negative control** from stopping the product.
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**journey**:
One Playwright path run against the real product on this machine: a directory under `.mmw/target.json`'s `journeys` key (default `.mmw/journeys`). `scripts/journey.py run <name>` starts the product, runs the script against the discovered addresses, and stops it; with `--break` the **negative control** arms the **break switch**, without `--break` it is the contract smoke journey with the product down. The script reads only those addresses and starts nothing itself. Quantity and content are the owner's; the default three are money, the login gate, and one submit chain.
_Admitted_: `journey.py`
_Avoid_: wiring check (when a whole-product run is meant), parity run
_Home_: `mmw-v2/skills/ui-acceptance/references/journey.md`

**`.mmw/harness`**:
The directory in a consuming repository that holds start-the-stack, the **break switch**, vendor stubs, account seeds, the few seeds a journey uses, and the entry that records an action that would leave the machine. Product answers live in `.mmw/` (`target.json`, `harness/`, `journeys/`, `stories/`); `harness-guard.py` fails a name that leaks outside `.mmw/`, `tests/`, `scripts/dev/`, a test file kept beside the code it tests (`__tests__/`, `__mocks__/`, `*.test.*`, `*.spec.*`), or a file `leaves_machine` names; what it reads is what git tracks or would track, never what a run happened to leave in the directory.
_Avoid_: reach script, `scripts/testing/` (when this directory is meant)
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**harness guard**:
`scripts/harness-guard.py` beside the ui-acceptance `SKILL.md`: given the repository root, it decides whether the names a repository uses only to make itself drivable have stayed in the allowed places. The leak strings are `.mmw/target.json`'s `harness_markers`; `MMW_` reads are judged regardless; story-service files must not name a `.dc.html`. What widens the allowed set is `leaves_machine`. It judges names in files, not a running product: it starts nothing and takes no lease. The **contract ticket** carries its criterion and names it bare.
_Admitted_: `harness-guard.py`
_Avoid_: leak check, back-door check
_Home_: `mmw-v2/skills/ui-acceptance/references/harness-guard.md`

**negative control**:
The pair each judge builds to prove it can fail. The story judge's perturbs a design-side style and strips product-side `data-ui` ids before any real result. The boundary criterion's is the **mutation check**. A journey with `--break` arms the **break switch**; a contract smoke journey without `--break` runs with the product down.
_Avoid_: 负控制, GREEN WITHOUT TRANSPORT
_Home_: `mmw-v2/skills/ui-acceptance/scripts/story-parity.py`, `mmw-v2/skills/ui-acceptance/scripts/boundary-check.py`, `mmw-v2/skills/ui-acceptance/scripts/journey.py`

**normalisation**:
How an accessibility tree is read as the sequence of its named nodes in reading order, each with its nearest named ancestor, unnamed wrappers and landmark names dropped. `normalize_aria` in `design_render.py` serves `extract_skeleton.py` and the **target trees**; the story judge no longer compares trees.
_Avoid_: 归一化, ARIA 归一化, ARIA 树, 视口
_Home_: `mmw-v2/skills/ui-acceptance/scripts/design_render.py`

### Screen contract

**screen contract**:
`docs/specs/<effort>/screen-contract.yaml`. The **control axis**, `rows`: one row per user-visible behaviour — the control (`trigger`, by role and accessible name), its `precondition`, the `scenes` it is visible in, what it `calls`, which field feeds each value it `shows`, what state is `next`, what `on_failure` shows, where the behaviour was decided (`source`), and whether design and backend agree (`gap`). `pages` names each design page's story id (`mount`) and the component that owns it; only an `App · ` page may carry `route`. `scenes` names which design page each scene of `scenes.json` belongs to. It also carries `effort`, `baselines`, `target.kind`, `viewports`, `retired_ids`, `volatile_values`, `readme_dispositions`, `backend_without_ui` and `proposed_operations`, and a key that is none of these is an error that names the key. It carries no address, no `observe`, no locating pin. Written by `write-screen-contract` on the alignment ticket; read by `to-spec`, `to-tickets`, `implement`, the Spec axis, the story judge, the boundary check and `verify-ticket --lint`. It is the behaviour baseline of an interface, beside the handoff package as its look-and-copy baseline; the two never bind the same thing.
_Avoid_: UI contract, interaction table, 界面合同表, 对齐表
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has an interface: a `grilling` ticket, blocked by every decision ticket and by the **handoff ticket**, resolved by running `write-screen-contract` and closed when every row's `gap` is `aligned`.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, written by `write-screen-contract` for the person to settle — the one judgement in that skill that is theirs.
_Avoid_: 差集
_Home_: `mmw-v2/skills/write-screen-contract/SKILL.md`

**`extract_skeleton.py`**:
`scripts/extract_skeleton.py` beside the write-screen-contract `SKILL.md`: one offline render of every scene of a **handoff package**, through `design_render.py`, writing the **skeleton** and, with `--targets`, the **target trees**. It judges nothing and needs no product. `--contract` beside `--targets` hides that contract's `retired_ids` triggers before the tree is read; the story judge does not hide them. It drives a real browser, so Chromium has to be installed for Playwright before it will run at all.
_Avoid_: the extractor, 骨架脚本
_Home_: `mmw-v2/skills/write-screen-contract/scripts/extract_skeleton.py`

**skeleton**:
The JSON `extract_skeleton.py` writes from that render, and the **row inventory** a screen contract is linted against: every interactive control of the handoff package keyed by (page, role, accessible name) with the list of scenes it is visible in, plus each scene's normalised tree and the class names in that subtree. It is the design side's inventory of controls, never the contract's: a control the skeleton has and the contract lacks is a lint error, and so is the reverse, and a row's `trigger` is a role and an accessible name copied from it exactly, hint text the tree folded in included. It is written to a scratch path and read there by `lint_screen_contract.py`; `--tools` on that script is an override of the sibling ui-acceptance lookup; what is kept out of the same render is the target trees.
_Avoid_: 骨架 (as a term), control inventory
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`, `mmw-v2/skills/write-screen-contract/scripts/extract_skeleton.py`

**`retired_ids`**:
The top-level list on a screen contract of row ids that once had a row and no longer do: an id is never renumbered and never reused, and the lint prints every entry on every run. The lint uses an entry's `page` and `trigger` to stop asking for a row; the story judge refuses any entry that carries `trigger`.
_Avoid_: 退役 id, deleted rows
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**contract ticket**:
The first ticket cut from a spec with a screen contract: `.mmw/` in full (target.json, harness, journeys, stories and adapters), the interaction helper the boundary check uses, a `journey.py run smoke` criterion that starts the stack and logs in, and the harness guard. Every other ticket of the batch is blocked by it. Interface tickets own by design page: one story criterion (`--pages`) and one boundary criterion per `calls` row.
_Avoid_: 合同票, prefactor ticket (for this one), addressing self-check
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**acceptance ticket**:
The ticket `to-tickets` cuts per line of a spec's **Cross-ticket flows**: it builds and runs that flow's journey on the merged base branch after every ticket the flow involves has landed. Unlike the **contract ticket**, it comes after the batch rather than before it.
_Avoid_: 验收票, flow ticket
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**Cross-ticket flows**:
An optional bullet of a spec's `## Testing Decisions`: one line per user flow that spans tickets, naming the flow (the directory under `.mmw/journeys/<flow>/`) and the Implementation Decisions sections it involves. `to-tickets` cuts one **acceptance ticket** per line. A spec that omits the bullet cuts none.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**mount**:
A design page's `mount` in the contract's `pages`: the story page id the product serves as `?page=<mount>`. Declared by the person writing the contract, never derived from rows; lowercase `[a-z0-9-]`, unique across pages. A story criterion names the ticket's mounts with `--pages`. `--mount` is a retired flag of `story-parity.py`, listed under `retired` in `verify-ticket.py`'s `PIPELINE_SCRIPTS` and reported by `--lint` as `[screen-contract]`; the live name is `--pages <mount,…>`. It is also the value of `data-screen` on the one product element this page *is*, when the surface carries that attribute.
_Avoid_: mount point (for this), 挂载点, data-screen-label, test hook (for this)
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

**target trees**:
`docs/specs/<effort>/targets/<page>.aria` and `<page>.classes`, one pair per design page, written by `extract_skeleton.py --targets` with `normalize_aria` in `design_render.py`: every scene's normalised tree and the class names in that subtree, headed by the sha256 of `scenes.json` and of the page. The handoff package's behavioural counterpart and a derived view of it — the package is the baseline, the tree the view, the hashes what keeps them from disagreeing (the contract lint fails when they do). An interface ticket lists its pages' pair under `## Read first`.
_Avoid_: 目标树, target elements, expected tree
_Home_: `mmw-v2/skills/write-screen-contract/references/screen-contract-format.md`

### The runtime a repository answers for

**`design_render.py`**:
`scripts/design_render.py` beside the ui-acceptance `SKILL.md`: the shared runtime `story-parity.py` and `extract_skeleton.py` import — the contract's pages and scenes, the baseline server and its CDN answering (`vendor/`, cache, network), `capture`, the wrapper page, and the normaliser. Nothing in it judges. The contract lint loads this file in-process for `volatile_triggers` and `count_volatile_hits`.
_Avoid_: the driver module, 共用驱动, Adapter (the driver class)
_Home_: `mmw-v2/skills/ui-acceptance/scripts/design_render.py`

**`target_config.py`**:
`scripts/target_config.py` beside the ui-acceptance `SKILL.md`: reads and checks `.mmw/target.json`. Run as a command, `target_config.py --check` is the setup-time bar for one repository. The contract lint loads this file in-process for the product kinds and that check.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/target_config.py`

**target**:
What kind of product this repository is, named in the contract as `target.kind` — `electron`, `web-spa`, `web-server-rendered`, `chrome-extension`. The repository answers for this product on this machine in `.mmw/target.json`, in the fields `target_config.py`'s `FIELDS` declares, which `target_config.py --check` prints with one sentence and one example each, exiting 0 once the file is complete. The list does not change with the kind. The contract carries no `adapter` key.
_Avoid_: platform (bare), 目标 (as a term), 适配器 (and `adapter`, as a word for anything on the target side; the file name `.release-adapter.json` and the key template's `--adapter` flag are literals a program reads and stay), target.adapter, the nine questions
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the runtime and never written in a contract or a criterion: what brings this product up on this machine, what takes it down, where it answers, where its story pages and journeys are, and what it does that reaches past the machine. Which fields those are is `target_config.py`'s `FIELDS`, printed one sentence and one example each by `target_config.py --check`. Addresses change per machine and per worktree; this file is where they are answered afresh.
_Avoid_: target config, 地址文件, reach (the target.json field), transport_off, transport_on
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`checks`**:
The optional key of `.mmw/target.json`: a list run in order at the repository root by `--closeout` only, after the draft is accepted, before the ticket branch is pushed and an `ALL MET` ticket closes. An entry is a command string, held to `DEFAULT_TIMEOUT` (600 s), or `{"run": …, "timeout": …}` held to its own bound; every command receives `MMW_BASE_REF=origin/<into>` from the newest `worker.started`. The run is posted as a `ticket.checked` of run `repo-checks` before the closing comment: `met` when every command exited 0, and the branch is pushed and the ticket closes; `unmet` with each failed command and its last 20 lines when any did not, and the ticket stays open, still assigned and in the agent queue. A `checks` value that is not a list, an entry of another shape, or a file that is not JSON, is an `unmet` run naming that problem, not absence. `--reverify`, `--lint`, `--check-only`, and a `HANDOFF REQUIRED` draft do not run them. A repository without the key is unchanged.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`stop`**:
The key of `.mmw/target.json` that ends what `start` started and nothing else — the only way a run may end a process, since `tool-guard.py pretool` refuses `kill`, `pkill`, `killall` and `xargs kill` and sends the reader to it. It ends only what this run recorded as its own, including this run's containers, leaves a neighbour's product alone, and exits 0 with nothing of its own to end. It does not release the lease; `lease.py` does. A repository that declares `start` declares `stop`, or the refusal points at a command that does not exist.
_Avoid_: 停止命令, teardown
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`leaves_machine`**:
The required key of `.mmw/target.json` that answers what this product does in a run that reaches past the machine — opening the system browser, calling a paid service, writing a machine-global location — and how the run neutralises and records each under `MMW_AUTOMATION=1`. `[]` is an answer; a missing key is not, because a run that reached a live service looks exactly like one that did not.
_Avoid_: 离机操作, side effects (for this)
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

### The lease

**lease**:
One run's share of this machine: a registration of `worktree path -> slot` in `MMW_HOME/leases`, defaulting to `~/.mmw/leases`, recording the repository's git directory. A ticket worktree claims it at the first run of its criteria that needs the product — writing code takes none, and neither `start` nor `adopt` takes one — and keeps it until its ticket's work ends, at an event in `SLOT_ENDS`, since the worker's first run, final reverify and the closeout's checks all want the same application; a replaced or lost worker's worktree keeps it for the worker that carries on there. A criterion or judge run outside an `issue-<n>` ticket worktree gives back the lease it claimed itself when that run ends, and leaves alone a lease the worktree already held, which is somebody else's product; `lease.py run` instead starts a product for a person or agent and keeps the lease. `advance` and `land` give a ticket's lease back when they archive the workspace, `advance` also when it gives back a lost worker's claim, `--closeout` when it hands the ticket back, `suspend` and `retract` with the claim. `claim` reclaims a registration whose worktree no longer exists and whose ports are quiet. `lease.py claim | env | run | release | remove-instance | list | count` is the whole surface. Two limits bound a claim: the machine's `MMW_LEASE_SLOTS`, and the product's `instance.max`, which counts every claim made from the repository wherever its directory is. A claim past either is not taken — `claim` exits 4 naming the limit and who holds the slots — and the run waits under a `worker.queued` event. The count and the take happen under one lock on the registry, the take is atomic (`O_CREAT | O_EXCL`), there is no fallback to a second slot, and **nothing in it ever ends a process** except through the repository's own `stop`, which `release --stop` runs: `release` refuses while anything still listens on the slot and names the pid and the directory. Whether a port is held is asked of the port — a connection to both loopback addresses, then a bind — so a listener bound to every address (where a container engine publishes one) or to the IPv6 loopback alone counts as held. `target_config.py`'s `command_env` puts this run's lease into the environment of every command `.mmw/target.json` declares.
_Admitted_: instance lease
_Avoid_: 租约 (as a term), seat, reservation
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`

**slot**:
What a lease hands out: a block of ports and a data directory that no other slot overlaps, numbered from 0. `MMW_LEASE_SLOTS` (8) is how many this machine holds, `MMW_LEASE_PORT_BASE` (21000) and `MMW_LEASE_PORT_STRIDE` (20) where the blocks start and how wide they are. Bare `slot` is always this one.
_Avoid_: 槽位, port range (for this), seat
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`

**instance**:
One run of a product on this machine, and the optional `instance` field of `.mmw/target.json`: how many of them one machine holds at once, and how a run takes one. `.mmw/target.json`'s `"instance": {"max": <n>, "why": "<what stops a second one>"}` is where a repository whose product cannot move its ports says so: every claim the repository holds counts toward `max`, the main checkout's included, and a run past it waits for a slot under a `worker.queued` event; `advance` still starts every frontier ticket. Its `MMW_DATA_DIR` remains as long as its ticket worktree remains and is removed by `lease.py remove-instance` after the workspace archive removes that worktree. `discover` prints `instance`, a readable name for messages. After `stop`, `journey.py` checks that this run's slot is empty.
_Avoid_: 实例 (as a term)
_Home_: `mmw-v2/skills/ui-acceptance/references/product-answers.md`

**`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`**:
The six variables a lease puts into the environment of every command `.mmw/target.json` declares: a readable machine-unique name for this run, the slot number, the first port of its block, how many ports the block holds, a directory it owns, and `1` as the signal that what would leave this machine is to be neutralised and recorded instead. A repository reads them **at the moment it starts a process, never into the session or the test environment**: a suite that asserts its product's registered port number is right to, and a derived port leaking into it turns a correct suite red.
_Home_: `mmw-v2/skills/ui-acceptance/scripts/lease.py`

### Values at a glance

| name | values |
| --- | --- |
| `target.kind` | `electron` · `web-spa` · `web-server-rendered` · `chrome-extension` |
| lease environment | `MMW_INSTANCE` · `MMW_SLOT` · `MMW_PORT_BASE` · `MMW_PORT_COUNT` · `MMW_DATA_DIR` · `MMW_AUTOMATION` |
| `lease.py` constants | `MMW_LEASE_SLOTS = 8` · `MMW_LEASE_PORT_BASE = 21000` · `MMW_LEASE_PORT_STRIDE = 20` |
