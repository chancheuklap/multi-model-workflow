# UI acceptance

How an interface is proved correct by machine: the design-side baselines a Claude Design project leaves behind, the judges that compare a running product against them scene by scene, the screen contract that says what every control does, and the lease that gives each run its own share of this machine. It exists because a UI judgement that no command decides is not an acceptance criterion, and because several agents run on one machine at once.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### The design side

**Claude Design**:
The design tool whose downloaded project is the handoff package and the baseline side of a parity run. Its page format is Design Components (`<x-dc>`, helmet, `sc-if` / `sc-for`, `{{ }}` template holes, `data-props`, `dc-import`); its runtime is `support.js`.
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**component**:
A root-level `<name>.dc.html` page in a Claude Design project that owns its state, exposes a `scene` enum prop — one value per state, and those values are the page's scene names — so the Tweaks panel can switch states, and reports cross-component actions through callback props. Its helmet pins the page root `#dc-root` to the application window size, which is where the baseline side is screenshotted from. The parity wrapper page imports it with `<dc-import name="…" …>` carrying that scene's `props` as attributes, which is what pins one scene. The `component` column of a screen contract's `pages` is a different thing — the product component that owns that page — and is defined in `mmw-v2/skills/align-screens/references/contract-format.md`.
_Avoid_: design component, scenario, scenario 属性, 状态开关
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**handoff package**:
A Claude Design project downloaded into the prototype leaf directory the port started from, `prototypes/<task>/<issue>/UI/`: every `.dc.html` page the project has — components and app pages alike, since a scene's data and its render both come from the page — plus `styles/`, `data/`, `support.js`, `scenes.json` and `vendor/` holding the three scripts `support.js` loads, which together are what the driver renders; plus the `README.md` the handoff run writes beside them, recording where each exact value and piece of verbatim copy came from, which a spec and its tickets take exact values, verbatim copy and `viewports` from. The screen contract's `baselines.look` names it; `story-parity.py` and `extract_skeleton.py` render it; the Spec axis does not open it; it supersedes the winning variant under `## Read first`; once downloaded it is a contract, copied verbatim, not a reference. The target trees are its derived view.
_Avoid_: 交接包, 开发交接包, 基线目录, UI 基线
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**scene**:
One entry of `scenes.json`: `name`, `page` (the `.dc.html` it pins), `props` (the prop set that puts the design page into that state), and `data` (**scene data**). The screen contract declares every scene once under `scenes`, with its page. The product story is addressed by `?page=&scene=`; the view does not answer a query parameter from fixtures of its own. Each scene gets its own screenshot and tree per viewport. The name may not contain `/`, because its wrapper page is `/__parity-<name>.dc.html`. In Claude Design a scene is one value of a component's `scene` prop, switched from the Tweaks panel; the word is the same on both sides, and there is no second word for it.
_Avoid_: 场景 (when a scene is meant), 场景列表, scenario, 状态
_Home_: `mmw-v2/skills/claude-design-blocks/references/handoff.md`

**scene data**:
The `data` field of a `scenes.json` entry: `{state, vals}` — the page's own logic class constructed with that scene's props, then `componentDidMount()`, then `renderVals()`, run in Node the way `support.js` runs it in a browser, with `state` and `vals` taken through JSON so functions are stripped. `export_scene_data.py` writes it from the downloaded page, never from a source under `src/`; the product story's adapter reads the same object. A package whose `data` is missing or stale is a lint failure, not a product defect.
_Avoid_: fixture props (when this field is meant)
_Home_: `mmw-v2/skills/claude-design-blocks/references/handoff.md`

**`DESIGN.md`**:
The consuming repository's design-system file. It is checked for before the first upload of a port; when it is missing, the `create-design-md` skill writes one from that repository, and it is uploaded once per project — not once per port — in Claude Design under "Create new design system", so every interface designed afterwards holds to that system.
_Home_: `mmw-v2/skills/claude-design-blocks/references/porting.md`

**prototype**:
Code that answers one design question, kept in the repository under `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/` and iterated as the answer sharpens; the real implementation is written with it as reference. Its question and verdict live in the leaf `README.md`; it has no tests. A UI prototype is several structurally different **variants** (default three, at most five) on one real route, switched by `?variant=`; the user picks the winner, `?variant=<winner>`. The mount point, symlink, and switcher that let variants render inside the real app are **scaffolding**, taken down in step 6 of `prototype/UI.md`; a **prototype route** is one created for the variants and deleted when the winner is promoted. A prototype's chosen artifact — the winning variant, the validated logic module, an experiment's Reusable parts with its Conclusion — is a baseline source.
_Avoid_: throwaway (for this), 一次性分支, 原型 (as a term), 研究件, UI variation (in this repository's text), throwaway route, 挂载点连同软链
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

**leaf directory**:
`prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, one per prototype kind; `<task>` is the development effort — the wayfinder map's title where there is one — and `<issue>` is the ticket number, or a short feature name when there is no ticket. The handoff package and `scenes.json` live in the `UI/` one. Once folded in, it is the only home a prototype has. Its `README.md` is the **leaf README.md**, read to its verdict as a `## Read first` item.
_Avoid_: 叶子目录, the leaf (bare)
_Home_: `mmw-v2/upstream/skills/engineering/prototype/SKILL.md`

### The judges

**story**:
A product page that renders one presentational component from the same scene data the design page used, addressed as `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. It lives in `.mmw/stories/`; the product's `stories` command prints `origin`. No backend, no seed, no route.
_Avoid_: storybook (when this page is meant), preview page
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**user story**:
One line of a spec's `## User Stories`.
_Avoid_: story (for this)
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**story judge**:
`scripts/story-parity.py` beside the drive-target `SKILL.md`: it decides whether a product story matches the design page it was built from. Given `--contract` and `--pages <mount,…>` (and `--scenes` to narrow), it starts the `stories` command, opens each scene at each contract viewport, captures `[data-story-root]`, renders the design page offline with `#dc-root` pinned to that box (`frame_box`), and compares the normalised accessibility tree and pixels after sub-cell alignment. The class set is not compared. It prints `STORY OK <passed>/<total> pixel<=<worst>%` (exit 0), or one `DIFF <scene> <viewport> <pct>% (unaligned <pct>%) — <reasons>` line per failing pair (exit 1), or `NEGATIVE CONTROL FAILED` (exit 2). `--render-only` renders the design side alone. No address is on its line: a `CHECK:` names it bare, and `verify-ticket.py --tools` puts the drive-target skill's `scripts/` on the `PATH` of the shell that runs it.
_Admitted_: `story-parity.py`
_Avoid_: visual-parity.py (as the judge), interface parity, PARITY OK (the whole-product judge's success line), visual parity
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

**story adapter**:
What puts a product's presentational component into one scene on a **story** page: one module per design page, `stories/adapters/<page>.mjs` under `.mmw/`, named by that page's `mount`, so a `?page=` with no adapter is a 404. It takes the scene's **scene data** and maps those fields onto the component's props; the screen contract's `shows` column for each row says which field feeds which displayed value, and the `code-review` Spec axis checks that mapping field by field. It reaches for no backend, no seed and no route — the page puts the component in the scene by itself. The contract ticket lands the first one as the precedent every later interface ticket copies. `adapter` is a dead word on the **target** side only; this is the sense that stays.
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`, `.mmw/stories/serve.py`

**boundary**:
In this repository the word names one class of acceptance criterion and the judge that runs it: a **boundary criterion**, in the fixed shape of `references/boundary-check.md`, run by `boundary-check.py`. It is not a word for a **seam**.
_Avoid_: boundary (as a word for a seam)
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**boundary criterion**:
An acceptance criterion in the fixed shape of `references/boundary-check.md`, running `scripts/boundary-check.py --run "<the product's test command>"`: the command is run twice in this process's cwd, first as written (must exit 0), then with `MMW_NEGATIVE=1` (must exit non-zero). `--run` takes one command, not a shell line, and may be repeated. Prints `BOUNDARY OK <n>/<n>`, or `MISS <command> — <last 20 lines>` when the first pass is already red, or `GREEN WITHOUT INTERACTION <command> — <why>` when the second pass is also green. Mocking the product's own API client module is the allowed seam; stubbing `fetch`, msw, nock or fetch-mock is not.
_Admitted_: boundary check
_Avoid_: wiring criterion, wiring-check.py, WIRING OK
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**mutation check**:
The second pass of a boundary criterion: the same command, with `MMW_NEGATIVE=1`, must go red. The product's shared interaction helper does nothing under that variable, so an assertion that does not depend on the click stays green and is refused. It is mechanical; a reviewer does not read the test to decide whether it can fail.
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**interaction helper**:
The one shared click-and-fill helper a consuming repository's **contract ticket** delivers, which every boundary test calls instead of touching the page itself. Under `MMW_NEGATIVE=1` it does nothing, and that is what makes the **mutation check** mechanical: a test whose assertion really depends on the interaction goes red on that second pass, while one that is true without the click stays green and is reported rather than passed. It is the interaction half of the boundary seam — the other half is the product's own API client module, which the test replaces with a mock.
_Avoid_: click helper, 交互 helper, page object (for this)
_Home_: `mmw-v2/skills/drive-target/references/boundary-check.md`

**journey**:
One Playwright path run against the real product on this machine: a directory `<journeys>/<name>/` holding an executable `run`, or a `package.json` declaring `scripts.run`, where `<journeys>` is `.mmw/target.json`'s `journeys` key, default `.mmw/journeys`. `scripts/journey.py run <name>` claims the lease, runs `start`, runs `discover`, puts the addresses (uppercased, so `origin` arrives as `ORIGIN`) and lease variables into the environment, runs the script in that directory, and runs `stop` whether the script succeeded or not; then runs the script once more as its **negative control**. Prints `JOURNEY OK <name>`, `JOURNEY FAILED <name> at <last line>`, or `JOURNEY GREEN WITHOUT PRODUCT <name> at <last line>`. Quantity and content are the owner's; the default three are money, the login gate, and one submit chain.
_Admitted_: `journey.py`
_Avoid_: wiring check (when a whole-product run is meant), parity run
_Home_: `mmw-v2/skills/drive-target/references/journey.md`

**`.mmw/harness`**:
The directory in a consuming repository that holds start-the-stack, vendor stubs, account seeds, the few seeds a journey uses, and the entry that records an action that would leave the machine. Product answers live in `.mmw/` (`target.json`, `harness/`, `journeys/`, `stories/`); `harness-guard.py` fails a name that leaks outside `.mmw/`, `tests/`, `scripts/dev/`, or a file `leaves_machine` names.
_Avoid_: reach script, `scripts/testing/` (when this directory is meant)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**harness guard**:
`scripts/harness-guard.py` beside the drive-target `SKILL.md`: given one argument, the repository root, it walks the repository, reads every text file it can, and decides whether the names a repository uses only to make itself drivable have stayed in the places `.mmw/harness` names. Anywhere else is a leak — a back door opened for automated acceptance that ships to a customer's machine with the release. It prints `HARNESS OK` (exit 0), or one `HARNESS LEAK <file>:<line>` line per leak (exit 1). What widens the allowed set is `.mmw/target.json`'s `leaves_machine`, never an exception written into the check. The **contract ticket** carries its criterion, `CHECK: harness-guard.py .`, and names it bare like every other judge. It judges names in files, not a running product: it starts nothing and takes no lease.
_Admitted_: `harness-guard.py`
_Avoid_: leak check, back-door check
_Home_: `mmw-v2/skills/drive-target/references/harness-guard.md`

**negative control**:
The pair each judge builds to prove it can fail. The story judge's is judged before any real result: after the first scene at the first viewport, the baseline server serves that scene's own address with an error banner in the served bytes, the story page is captured again, and the two must differ — equal means the product capture read the design's server, and the run stops with `NEGATIVE CONTROL FAILED`. The boundary criterion's is the **mutation check**. The journey's runs last, after `stop`: the script runs again with every discovered address repointed to a closed port and `MMW_JOURNEY_NEGATIVE=1` set, and a second pass is `JOURNEY GREEN WITHOUT PRODUCT`.
_Avoid_: 负控制, GREEN WITHOUT TRANSPORT
_Home_: `mmw-v2/skills/drive-target/scripts/story-parity.py`, `mmw-v2/skills/drive-target/scripts/boundary-check.py`, `mmw-v2/skills/drive-target/scripts/journey.py`

**normalisation**:
How an accessibility tree is read before comparison: as the sequence of its named nodes in reading order — role, name or text, and state attributes — each followed by ` < ` and its nearest named ancestor, with unnamed wrappers and landmark names dropped. One normaliser, `normalize_aria` in `screen_driver.py`, serves the story judge and the target trees. The accessibility tree walks the whole subtree under `[data-story-root]` or `#dc-root`; the pixel judge sees only that box intersected with the viewport, on both sides.
_Avoid_: 归一化, ARIA 归一化, ARIA 树, 视口
_Home_: `mmw-v2/skills/drive-target/references/story-parity.md`

### Screen contract

**screen contract**:
`docs/specs/<effort>/screen-contract.yaml`. The **control axis**, `rows`: one row per user-visible behaviour — the control (`trigger`, by role and accessible name), its `precondition`, the `scenes` it is visible in, what it `calls`, which field feeds each value it `shows`, what state is `next`, what `on_failure` shows, where the behaviour was decided (`source`), and whether design and backend agree (`gap`). `pages` names each design page's story id (`mount`) and the component that owns it; only an `App · ` page may carry `route`. `scenes` names which design page each scene of `scenes.json` belongs to. It also carries `effort`, `baselines`, `target.kind`, `viewports`, `retired_ids`, `volatile_values`, `readme_dispositions`, `backend_without_ui` and `proposed_operations`, and a key that is none of these is an error that names the key. It carries no address, no `observe`, no locating pin. Written by `align-screens` on the alignment ticket; read by `to-spec`, `to-tickets`, `implement`, the Spec axis, the story judge, the boundary check and `verify-ticket --lint`. It is the behaviour baseline of an interface, beside the handoff package as its look-and-copy baseline; the two never bind the same thing.
_Avoid_: UI contract, interaction table, 界面合同表, 对齐表
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**alignment ticket**:
The last ticket of a wayfinder map whose destination has an interface: a `grilling` ticket, blocked by every decision ticket and by the ticket that produces the handoff package, resolved by running `align-screens` and closed when every row's `gap` is `aligned`.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**gap list**:
The rows of a screen contract whose `gap` is `design-only` or `backend-only`, written by `align-screens` for the person to settle — the one judgement in that skill that is theirs.
_Avoid_: 差集
_Home_: `mmw-v2/skills/align-screens/SKILL.md`

**`extract_skeleton.py`**:
`scripts/extract_skeleton.py` beside the drive-target `SKILL.md`: one offline render of every scene of a **handoff package**, through the same driver and the same normaliser the story judge uses, so what comes out is what the judge will later read. It judges nothing and needs no product. `align-screens` runs it twice on one contract — once for the **skeleton**, and once more with `--targets` (and `--contract`, which hides the contract's `retired_ids` the way the judge hides them) to write the **target trees**. It drives a real browser, so Chromium has to be installed for Playwright before it will run at all.
_Avoid_: the extractor, 骨架脚本
_Home_: `mmw-v2/skills/drive-target/scripts/extract_skeleton.py`

**skeleton**:
The JSON `extract_skeleton.py` writes from that render, and the **row inventory** a screen contract is linted against: every interactive control of the handoff package keyed by (page, role, accessible name) with the list of scenes it is visible in, plus each scene's normalised tree and the class names in that subtree. It is the design side's inventory of controls, never the contract's: a control the skeleton has and the contract lacks is a lint error, and so is the reverse, and a row's `trigger` is a role and an accessible name copied from it exactly, hint text the tree folded in included. It is written to a scratch path and read there by `lint_contract.py`, which is why `--tools` stays required for that script; what is kept out of the same render is the target trees.
_Avoid_: 骨架 (as a term), control inventory
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`, `mmw-v2/skills/drive-target/scripts/extract_skeleton.py`

**`retired_ids`**:
The top-level list on a screen contract of row ids that once had a row and no longer do: an id is never renumbered and never reused, and the lint prints every entry on every run. An entry carries the id and a one-line note saying when and why it was retired; when the handoff package still shows the control, it also carries the `page` the control is on and a `trigger` in the same shape as `volatile_values` — a handoff role and accessible name — and that pair does two things at once: the lint stops asking for a row for that control, and the judges hide it, on that page's scenes and on the design side only. An entry that names no `page` whose name also lives on another page is hidden everywhere, which the lint warns about.
_Avoid_: 退役 id, deleted rows
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**contract ticket**:
The first ticket cut from a spec with a screen contract: `.mmw/` in full (target.json, harness, journeys, stories and adapters), the interaction helper the boundary check uses, a `journey.py run smoke` criterion that starts the stack and logs in, and the harness guard. Every other ticket of the batch is blocked by it. Interface tickets own by design page: one story criterion (`--pages`) and one boundary criterion per `calls` row.
_Avoid_: 合同票, prefactor ticket (for this one), addressing self-check
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**mount**:
A design page's `mount` in the contract's `pages`: the story page id the product serves as `?page=<mount>`. Declared by the person writing the contract, never derived from rows; lowercase `[a-z0-9-]`, unique across pages. A story criterion names the ticket's mounts with `--pages`. `--mount` is a retired flag of `story-parity.py`, listed under `retired` in `verify-ticket.py`'s `PIPELINE_SCRIPTS` and reported by `--lint` as `[screen-contract]`; the live name is `--pages <mount,…>`. It is also the value of `data-screen` on the one product element this page *is*, when the surface carries that attribute.
_Avoid_: mount point (for this), 挂载点, data-screen-label, test hook (for this)
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**target trees**:
`docs/specs/<effort>/targets/<page>.aria` and `<page>.classes`, one pair per design page, written by `extract_skeleton.py --targets` with the story judge's normaliser: every scene's normalised tree and the class names in that subtree, headed by the sha256 of `scenes.json` and of the page. The handoff package's behavioural counterpart and a derived view of it — the package is the baseline, the tree the view, the hashes what keeps them from disagreeing (the contract lint fails when they do). An interface ticket lists its pages' pair under `## Read first`.
_Avoid_: 目标树, target elements, expected tree
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

**`volatile_values`**:
A top-level list on the screen contract of display values the seed must not write — a wallet balance belonging to an external account, not a difference to hide. Each entry is a `page`, a `trigger` (role and accessible name, the same shape as `retired_ids`), one line of `reason`, and `after`, the previous named node, when another node on the scene shares its role and its name with the digits removed. One function, `matches_volatile`, matches an entry on the story judge and on the lint; both judges replace the matched node with one token before comparing, and how the mask is applied is in the contract format.
_Home_: `mmw-v2/skills/align-screens/references/contract-format.md`

### The runtime a repository answers for

**`screen_driver.py`**:
`scripts/screen_driver.py` beside the drive-target `SKILL.md`: the shared runtime `story-parity.py` and `extract_skeleton.py` import — the contract's pages and scenes, `.mmw/target.json` and the declaration of its fields (`FIELDS`), the baseline server and its CDN answering (`vendor/`, cache, network), `capture`, the wrapper page, and the normaliser. Nothing in it judges. Run as a command, `screen_driver.py target --check` is the setup-time bar for one repository. The contract lint loads this file in-process: kinds from `KINDS`, the `.mmw/target.json` check through the function `target --validate` runs.
_Avoid_: the driver module, 共用驱动, Adapter (the driver class)
_Home_: `mmw-v2/skills/drive-target/scripts/screen_driver.py`

**target**:
What kind of product this repository is, named in the contract as `target.kind` — `electron`, `web-spa`, `web-server-rendered`, `chrome-extension`. The repository answers for this product on this machine in `.mmw/target.json`, in the fields `screen_driver.py`'s `FIELDS` declares, which `screen_driver.py target --check` prints with one sentence and one example each, exiting 0 once the file is complete. The list does not change with the kind. The contract carries no `adapter` key.
_Avoid_: platform (bare), 目标 (as a term), 适配器 (and `adapter`, as a word for anything on the target side; the file name `.release-adapter.json` and the key template's `--adapter` flag are literals a program reads and stay), target.adapter, the nine questions
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`.mmw/target.json`**:
The consuming repository's machine facts, read by the runtime and never written in a contract or a criterion: what brings this product up on this machine, what takes it down, where it answers, where its story pages and journeys are, and what it does that reaches past the machine. Which fields those are is `screen_driver.py`'s `FIELDS`, printed one sentence and one example each by `screen_driver.py target --check`. Addresses change per machine and per worktree; this file is where they are answered afresh.
_Avoid_: target config, 地址文件, reach (the target.json field), transport_off, transport_on
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`checks`**:
The optional key of `.mmw/target.json`: a list run in order at the repository root by `--closeout` only, after the draft is accepted, before the ticket branch is pushed and an `ALL MET` ticket closes. An entry is a command string, held to `DEFAULT_TIMEOUT` (600 s), or `{"run": …, "timeout": …}` held to its own bound; every command receives `MMW_BASE_REF=origin/<into>` from the newest `worker.started`. The run is posted as a `ticket.checked` of run `repo-checks` before the closing comment: `met` when every command exited 0, and the branch is pushed and the ticket closes; `unmet` with each failed command and its last 20 lines when any did not, and the ticket stays open, still assigned and in the agent queue. A `checks` value that is not a list, an entry of another shape, or a file that is not JSON, is an `unmet` run naming that problem, not absence. `--reverify`, `--lint`, `--check-only`, and a `HANDOFF REQUIRED` draft do not run them. A repository without the key is unchanged.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`stop`**:
The key of `.mmw/target.json` that ends what `start` started and nothing else — the only way a run may end a process, since `hook.py pretool` refuses `kill`, `pkill`, `killall` and `xargs kill` and sends the reader to it. It ends only what this run recorded as its own, including this run's containers, leaves a neighbour's product alone, and exits 0 with nothing of its own to end. It does not release the lease; the driver does. A repository that declares `start` declares `stop`, or the refusal points at a command that does not exist.
_Avoid_: 停止命令, teardown
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`leaves_machine`**:
The required key of `.mmw/target.json` that answers what this product does in a run that reaches past the machine — opening the system browser, calling a paid service, writing a machine-global location — and how the run neutralises and records each under `MMW_AUTOMATION=1`. `[]` is an answer; a missing key is not, because a run that reached a live service looks exactly like one that did not.
_Avoid_: 离机操作, side effects (for this)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

### The lease

**lease**:
One run's share of this machine: a registration of `worktree path -> slot` in `MMW_HOME/leases`, defaulting to `~/.mmw/leases`, recording the repository's git directory. A ticket worktree claims it at the first run of its criteria that needs the product — writing code takes none, and neither `start` nor `adopt` takes one — and keeps it until its ticket's work ends, at an event in `SLOT_ENDS`, since the worker's run, the verifier's reverify and the closeout's checks all want the same application; a replaced or lost worker's worktree keeps it for the worker that carries on there. A criterion or judge run outside an `issue-<n>` ticket worktree gives its lease back when that run ends; `lease.py run` instead starts a product for a person or agent and keeps the lease. `advance` and `land` give a ticket's lease back when they archive the workspace, `advance` also when it gives back a lost worker's claim, `--closeout` when it hands the ticket back, `suspend` and `retract` with the claim. `claim` reclaims a registration whose worktree no longer exists and whose ports are quiet. `lease.py claim | env | run | release | remove-instance | list | count` is the whole surface. Two limits bound a claim: the machine's `MMW_LEASE_SLOTS`, and the product's `instance.max`, which counts every claim made from the repository wherever its directory is. A claim past either is not taken — `claim` exits 4 naming the limit and who holds the slots — and the run waits under a `worker.queued` event. The count and the take happen under one lock on the registry, the take is atomic (`O_CREAT | O_EXCL`), there is no fallback to a second slot, and **nothing in it ever ends a process** except through the repository's own `stop`, which `release --stop` runs: `release` refuses while anything still listens on the slot and names the pid and the directory. The driver claims the lease before it runs any command `.mmw/target.json` declares.
_Admitted_: instance lease
_Avoid_: 租约 (as a term), seat, reservation
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

**slot**:
What a lease hands out: a block of ports and a data directory that no other slot overlaps, numbered from 0. `MMW_LEASE_SLOTS` (8) is how many this machine holds, `MMW_LEASE_PORT_BASE` (21000) and `MMW_LEASE_PORT_STRIDE` (20) where the blocks start and how wide they are. Bare `slot` is always this one.
_Avoid_: 槽位, port range (for this), seat
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

**instance**:
One run of a product on this machine, and the optional `instance` field of `.mmw/target.json`: how many of them one machine holds at once, and how a run takes one. `.mmw/target.json`'s `"instance": {"max": <n>, "why": "<what stops a second one>"}` is where a repository whose product cannot move its ports says so: every claim the repository holds counts toward `max`, the main checkout's included, and a run past it waits for a slot under a `worker.queued` event; `advance` still starts every frontier ticket. Its `MMW_DATA_DIR` remains as long as its ticket worktree remains and is removed by `lease.py remove-instance` after the workspace archive removes that worktree. `discover` prints `instance`, a readable name for messages, and `instance_check`, one `observe` line whose truth means the product answering is the one this run started — which is what makes question 2 mean *answering and mine*.
_Avoid_: 实例 (as a term)
_Home_: `mmw-v2/skills/drive-target/references/runtime-environment.md`

**`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`**:
The six variables a lease puts into the environment of every command `.mmw/target.json` declares: a readable machine-unique name for this run, the slot number, the first port of its block, how many ports the block holds, a directory it owns, and `1` as the signal that what would leave this machine is to be neutralised and recorded instead. A repository reads them **at the moment it starts a process, never into the session or the test environment**: a suite that asserts its product's registered port number is right to, and a derived port leaking into it turns a correct suite red.
_Home_: `mmw-v2/skills/drive-target/scripts/lease.py`

### Values at a glance

| name | values |
| --- | --- |
| `target.kind` | `electron` · `web-spa` · `web-server-rendered` · `chrome-extension` |
| lease environment | `MMW_INSTANCE` · `MMW_SLOT` · `MMW_PORT_BASE` · `MMW_PORT_COUNT` · `MMW_DATA_DIR` · `MMW_AUTOMATION` |
| `lease.py` constants | `MMW_LEASE_SLOTS = 8` · `MMW_LEASE_PORT_BASE = 21000` · `MMW_LEASE_PORT_STRIDE = 20` |
