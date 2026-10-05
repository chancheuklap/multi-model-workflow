# Release

How this toolbox ships an installable package for a product on the current branch, through the `exe-release` skill: which products a change reaches, one product's release loop from a release manifest to a finished package, the automatic diagnosis and repair of what breaks in that loop, and the check that a shipped set came from one commit.

## Language

### The run

**product**:
The shipping unit `exe-release` packages: one per release manifest, named by the manifest's own `product` field and used in fingerprints and delivery paths. Step 2 of a run decides, from the paths a change touched, which products to ship.
_Home_: `mmw-v3/skills/exe-release/SKILL.md`

**release manifest**:
The JSON file declaring how one product is packaged, one file per product. Its filename and every script's `--adapter` flag call it the adapter; prose calls it the release manifest, and anything that only differs by value across products belongs in it, never in a product repository's own script.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

### The release engine

**release engine**:
`release-flow.sh`, the state machine that drives one product's **release loop**: which stage runs next, what a failed stage's fix attempt was, how many rounds it has spent, and when the release loop has succeeded. The agent driving a release reads this state through `where` and `receipt` rather than remembering it or resuming from session memory.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`

**release loop**:
One product's run of the **release engine**, from `release-flow.sh init` to `close` or `abort`, its state kept in `release-state.json`; a release ships its products one release loop at a time, and `init` refuses to open a second while one is open. Its `.round` counter (`round next`, `ROUND=`, `ROUND-CAP:`) rises by one after each failed stage that did not pause, within the **budget**.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`, `mmw-v3/skills/exe-release/SKILL.md`

**`where`**:
`release-flow.sh where`, the release engine's status command: every step of driving a release starts here, and the agent does what the **`where` state** says rather than picking the next stage itself.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

**`where` state**:
What `where` reports, and every one of them exits 0 so the state is read from stdout and never the exit code: `STAGE:<name>` naming the pending stage, `SUCCESS:all stages done`, `PAUSED:needs-context` (resolve it, then `resume`), `PAUSED:needs-redirection` (a circuit breaker, a spent budget or a P0 failure; stop and report to the user), and `CORRUPT:` for a state file that cannot be read.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

**`release-flow.sh resume`**:
`release-flow.sh resume`, continuing a paused release loop once its cause is gone: when HEAD has moved since the release loop's commit, every stage runs again against the new HEAD, so a code change reaches it only once committed; on the same HEAD it restarts from the first failed or running stage.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

**close**:
`release-flow.sh close`, finishing a product's release loop: it refuses one that has not shipped and, once it has, writes the delivery record.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

**abort**:
`release-flow.sh abort`, dropping the current release loop without writing a delivery record, unlike `close`.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

**delivery record**:
What `close` leaves once a product's release loop ships: the product's name, the commit it shipped, and when. The same-commit check reads it back; `abort` writes none.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`

**same-commit check**:
`release-flow.sh same-commit <product>...`, run once every product on a run's list has shipped: it prints `OK <product>` when that product's delivery record matches the current HEAD and `MISMATCH <product> <commit>` when it does not, so a shipped set is never a mix of commits.
_Home_: `mmw-v3/skills/exe-release/SKILL.md`, `scripts/release-flow.sh`

**release receipt**:
`release-flow.sh receipt`, the rendered account of the open release loop, headed `# release receipt`: every attempt tried so far (its stage, what kind of action it was, its outcome and fingerprint) and how many times each root-cause fingerprint has recurred. Given to the user as-is on a `PAUSED:needs-redirection` state, and read on `CORRUPT:`.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

### Diagnosis and repair

**release finding**:
One translated result of a release check or a build-failure diagnosis: its product, dimension, name and status (`ok`, `warn`, `fail` or `deferred`), a locator, a detail and a remediation, and, on a `fail`, the tier and root-cause fingerprint it must carry.
_Avoid_: finding (bare, in this context; a skill-set-review finding is a different concept, an established problem in a skill's own text that carries no tier)
_Home_: `mmw-v3/skills/exe-release/scripts/release_contracts.py` (`ReleaseFinding`), `scripts/diagnose_core.py`

**root-cause fingerprint**:
The string on a release finding that names a failure's cause and, by its prefix, decides the release engine's next move before any tier is considered: `transient:` re-runs the stage as it is, `env:` pauses for the agent driving the release to act on directly, and every other prefix goes to tier.
_Home_: `mmw-v3/skills/exe-release/scripts/diagnose_core.py`, `references/key.md` (`diagnose_rules`)

**tier**:
The three-level classification of a release finding whose root-cause fingerprint is neither `transient:` nor `env:`: `P0` stops the release engine and hands the release loop to a person, `P1` writes a fix brief for the agent driving the release, `P2` tries the product's own `derive` self-heal script. The agent driving a release never assigns it.
_Home_: `mmw-v3/skills/exe-release/scripts/diagnose_core.py`, `scripts/release_contracts.py` (`ReleaseFinding.tier`), `scripts/release-flow.sh`

**diagnoser**:
`diagnose_core.py`, the skill's general rule table that translates a failed stage's log into release findings, matched after a release manifest's own `diagnose_rules`. A release manifest whose `diagnose` field names a command replaces it for that product.
_Home_: `mmw-v3/skills/exe-release/scripts/diagnose_core.py`, `scripts/release-flow.sh`, `references/key.md`

**remediation**:
The suggested-fix text carried on a release finding: folded into a fix brief for a person or an agent to read, or, for an `env:` fingerprint, given as the pause's own question.
_Home_: `mmw-v3/skills/exe-release/scripts/diagnose_core.py`

**fix brief**:
The Markdown file `fix_dispatch.py` writes for a P1 failure: the rules for the agent driving the release plus the findings, printed as `FIX-BRIEF=<path>`. One member of the same family as an advisor brief and an agent brief.
_Home_: `mmw-v3/skills/exe-release/scripts/fix_dispatch.py`

**derive**:
A product's own deterministic regeneration script, declared in the release manifest and the sole P2 self-heal path: checked only for a pre-existing tracked diff before it runs, committed on the product's own branch when it changes something.
_Home_: `mmw-v3/skills/exe-release/references/key.md`, `scripts/release-flow.sh`

**circuit breaker**:
What stops the release engine dispatching the same root-cause fingerprint a fourth time: once a fingerprint has recurred three times, the release loop pauses and is handed to a person instead of tried again.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`

**budget**:
The three caps on a release loop's automated repair: a maximum number of **fix round**s and a maximum of the `.round` counter (`ROUND-CAP:`), both set by `--max-rounds`, and a wall-clock maximum (`--max-wall-clock`). Breaching one stops the release engine trying on its own and hands the release loop to a person, the same as a circuit breaker.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`

**fix round**:
One P2 `derive` run that changed and committed something, counted in `budget.fix_rounds` against the `--max-rounds` cap. Distinct from a ticket's own round, one pass fixing a criterion or a code-review finding.
_Home_: `mmw-v3/skills/exe-release/scripts/release-flow.sh`

**surface**:
`release-flow.sh surface --kind needs-context|needs-redirection --question <text>`, pausing the current release loop with a question: `needs-context` for the agent driving the release to resolve, `needs-redirection` for the user, the way a circuit breaker or a spent budget pauses it on its own.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md`, `scripts/release-flow.sh`

### Stages and hooks

**stage**:
One named step of a product's build pipeline: the release manifest's own `stages` run first, against its own repository, then the release engine appends its fixed three — verify the manifest, assemble the build script, build.
_Home_: `mmw-v3/skills/exe-release/references/key.md`, `scripts/release-flow.sh`, `scripts/release_contracts.py` (`StageSpec`)

**build hook**:
A named callback point in the build pipeline where a product's own script runs, keyed to a fixed phase rather than a step number, so the phase stays put as the release manifest's own stages change which step number it is. Optional as a whole; a first release manifest omits it.
_Avoid_: hook (bare, in this context; a host hook and a git hook are different mechanisms)
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**hook phase**:
The fixed name a build hook hangs on: `runtime_ready`, `backend_ready`, `artifact_ready`, `installer_ready`, `release_ready`.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

### Writing a release manifest

**`build_target`**:
The release-manifest section naming a product's own build particulars: the Electron app directory, the installer's brand and where its finished file lands, which paths mean this product changed, and any native-extension DLL the compiler does not carry on its own.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**`python_backend`**:
The release-manifest section declaring the Nuitka compile of the product's Python backend into a Windows executable: the interpreter and packages to compile, what data to embed versus ship separately, and the smoke run on the freshly compiled exe.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**`electron`**:
The release-manifest section declaring the Electron shell around the compiled backend and how its installer is produced: the generic `electron_builder` path, or a product's own `repo_hook` installer.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**`toolchain`**:
The release-manifest list of tools the build machine must have beyond those the generated build script already invokes. Step 1 of the build checks both, so a derived tool restated here is a tool demanded and never used.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**`event_sink`**:
The optional release-manifest field naming a command that receives each release loop event (`paused`, `stage.failed`, `classified`) as one JSON line of the `ReleaseLoopEvent` shape, for a product's own log system. Left out, the events are recorded nowhere.
_Home_: `mmw-v3/skills/exe-release/references/key.md`, `scripts/release-flow.sh` (`emit_event`)

**vendor artifact**:
A binary the package ships but git cannot hold (ffmpeg, an embedded interpreter): kept on the build machine's own cache under a fixed path, copied into the package and checked against a sha256 recorded in a lock file, never downloaded during the build.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**runtime asset**:
Data that ships beside the compiled exe rather than embedded inside it, read by path at run time: for a package that cannot be embedded at all, one too large to unpack on every launch, or one that must stay replaceable after install.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**smoke module**:
The module a compiled exe can run on its own, before it serves its first request, that imports everything the app needs: the one guard between a missing dynamic dependency and a customer finding it first.
_Avoid_: self-check module
_Home_: `mmw-v3/skills/exe-release/references/new-product.md`

**smoke**:
The release-manifest field naming the compiled exe's smoke invocation and the modules it must be able to import, run right after the compile. Also the guard on `nofollow_imports`: a nofollow pattern that would block one of those modules is caught here, not forty minutes into the next compile.
_Home_: `mmw-v3/skills/exe-release/references/key.md`

**`diagnose_rules`**:
A release manifest's own log-pattern rules for this product's build, matched before the skill's general table because a product knows its own log's shape first; each rule's fingerprint prefix decides the release engine's next move the same way the general table's does.
_Home_: `mmw-v3/skills/exe-release/references/key.md`, `scripts/diagnose_core.py`

### The build machine

**build machine**:
The (often remote, Windows) machine that compiles and packages a product over SSH, named by `RELEASE_REMOTE_HOST`/`RELEASE_REMOTE_ROOT` or, failing those, a `remote-build.json` beside the release manifest. It receives only `git archive HEAD`, never a dirty working tree. A release manifest's `build_machine` section can name a `setup` command, run on it before the first long step, and a `teardown` command, run after the build.
_Home_: `mmw-v3/skills/exe-release/references/new-product.md`, `SKILL.md`
