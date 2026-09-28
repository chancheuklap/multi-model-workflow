# Release

How this toolbox ships an installable package for a product on the current branch, through the `exe-release` skill: which products a change reaches, one product's build loop from a release manifest to a finished package, the automatic diagnosis and repair of what breaks in that loop, and the check that a shipped set came from one commit.

## Language

### The run

**product**:
The shipping unit `exe-release` packages: one per release manifest, named by the manifest's own `product` field and used in fingerprints and delivery paths. Step 2 of a run decides, from the paths a change touched, which products to ship.
_Home_: `mmw-v2/skills/exe-release/SKILL.md`

**release manifest**:
The JSON file declaring how one product is packaged, one file per product. Its filename and every script's `--adapter` flag call it the adapter; prose calls it the release manifest, and anything that only differs by value across products belongs in it, never in a product repository's own script.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

### The release engine

**release engine**:
`release-flow.sh`, the state machine that drives one product's build loop: which stage runs next, what a failed stage's fix attempt was, how many rounds it has spent, and when the round has succeeded. The agent driving a release reads this state through `where` and `receipt` rather than remembering it or resuming from session memory.
_Home_: `mmw-v2/skills/exe-release/scripts/release-flow.sh`

**`where`**:
`release-flow.sh where`, the release engine's status command: every round of driving a release starts here, and the agent does what the verdict says rather than picking the next stage itself.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

**verdict**:
What `where` reports, and every one of them exits 0 so the state is read from stdout and never the exit code: `STAGE:<name>` naming the pending stage, `SUCCESS:all stages done`, `PAUSED:needs-context` (resolve it, then `resume`), `PAUSED:needs-redirection` (a circuit breaker, a spent budget or a P0 failure; stop and report to the user), and `CORRUPT:` for a state file that cannot be read.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

**`release-flow.sh resume`**:
`release-flow.sh resume`, continuing a paused round once its cause is gone: it re-verifies every stage against the current HEAD, so a code change reaches it only once committed.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

**close**:
`release-flow.sh close`, finishing a product's round: it refuses one that has not shipped and, once it has, writes the delivery record.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

**abort**:
`release-flow.sh abort`, dropping the current round without writing a delivery record, unlike `close`.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

**delivery record**:
What `close` leaves once a product's round ships: the product's name, the commit it shipped, and when. The same-commit check reads it back; `abort` writes none.
_Home_: `mmw-v2/skills/exe-release/scripts/release-flow.sh`

**same-commit check**:
`release-flow.sh same-commit <product>...`, run once every product on a run's list has shipped: it prints `OK <product>` when that product's delivery record matches the current HEAD and `MISMATCH <product> <commit>` when it does not, so a shipped set is never a mix of commits.
_Home_: `mmw-v2/skills/exe-release/SKILL.md`, `scripts/release-flow.sh`

**receipt**:
`release-flow.sh receipt`, the rendered account of a paused round: every attempt tried so far (its stage, what kind of action it was, its outcome and fingerprint) and how many times each root-cause fingerprint has recurred. Given to the user as-is on a `PAUSED:needs-redirection` verdict.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

### Diagnosis and repair

**release finding**:
One translated build-failure diagnosis: a name, a tier, a root-cause fingerprint, a detail and a remediation.
_Avoid_: finding (bare, in this context; a skill-set-review finding is a different concept, an established problem in a skill's own text that carries no tier)
_Home_: `mmw-v2/skills/exe-release/scripts/release_contracts.py` (`ReleaseFinding`), `scripts/diagnose_core.py`

**root-cause fingerprint**:
The string on a release finding that names a failure's cause and, by its prefix, decides the release engine's next move before any tier is considered: `transient:` re-runs the stage as it is, `env:` pauses for the agent driving the release to act on directly, and every other prefix goes to tier.
_Home_: `mmw-v2/skills/exe-release/scripts/diagnose_core.py`, `references/key.md` (`diagnose_rules`)

**tier**:
The three-level classification of a release finding whose root-cause fingerprint is neither `transient:` nor `env:`: `P0` stops the release engine and hands the round to a person, `P1` writes a fix brief for the agent driving the release, `P2` tries the product's own `derive` self-heal script. The agent driving a release never assigns it.
_Home_: `mmw-v2/skills/exe-release/scripts/diagnose_core.py`, `scripts/release_contracts.py` (`ReleaseFinding.tier`), `scripts/release-flow.sh`

**remediation**:
The suggested-fix text carried on a release finding: folded into a fix brief for a person or an agent to read, or, for an `env:` fingerprint, given as the pause's own question.
_Home_: `mmw-v2/skills/exe-release/scripts/diagnose_core.py`

**fix brief**:
The Markdown file `fix_dispatch.py` writes for a P1 failure: the rules for the agent driving the release plus the findings, printed as `FIX-BRIEF=<path>`. One member of the same family as an advisor brief and an agent brief.
_Home_: `mmw-v2/skills/exe-release/scripts/fix_dispatch.py`

**derive**:
A product's own deterministic regeneration script, declared in the release manifest and the sole P2 self-heal path: checked only for a pre-existing tracked diff before it runs, committed on the product's own branch when it changes something.
_Home_: `mmw-v2/skills/exe-release/references/key.md`, `scripts/release-flow.sh`

**circuit breaker**:
What stops the release engine dispatching the same root-cause fingerprint a fourth time: once a fingerprint has recurred three times, the round pauses and is handed to a person instead of tried again.
_Home_: `mmw-v2/skills/exe-release/scripts/release-flow.sh`

**budget**:
The two limits on a round's automated repair — a maximum number of fix rounds and a wall-clock maximum — whose breach stops the release engine trying on its own and hands the round to a person, the same as a circuit breaker.
_Home_: `mmw-v2/skills/exe-release/scripts/release-flow.sh`

**fix round**:
One pass of stage-run, diagnose and dispatch, counted against the round budget. Distinct from a ticket's own round, one pass fixing a criterion or a code-review finding.
_Home_: `mmw-v2/skills/exe-release/scripts/release-flow.sh`

**surface**:
`release-flow.sh surface`, escalating the current round to the user directly, the way a circuit breaker or a spent budget does on its own.
_Home_: `mmw-v2/skills/exe-release/references/driving.md`, `scripts/release-flow.sh`

### Stages and hooks

**stage**:
One named step of a product's build pipeline: the release manifest's own `stages` run first, against its own repository, then the release engine appends its fixed three — verify the manifest, assemble the build script, build.
_Home_: `mmw-v2/skills/exe-release/references/key.md`, `scripts/release-flow.sh`, `scripts/release_contracts.py` (`StageSpec`)

**build hook**:
A named callback point in the release pipeline where a product's own script runs, keyed to a fixed phase rather than a step number, so the phase stays put as the release manifest's own stages change which step number it is. Optional as a whole; a first release manifest omits it.
_Avoid_: hook (bare, in this context; a host hook and a git hook are different mechanisms)
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**hook phase**:
The fixed name a build hook hangs on: `runtime_ready`, `backend_ready`, `artifact_ready`, `installer_ready`, `release_ready`.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

### Writing a release manifest

**`build_target`**:
The release-manifest section naming a product's own build particulars: the Electron app directory, the installer's brand and where its finished file lands, which paths mean this product changed, and any native-extension DLL the compiler does not carry on its own.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**`python_backend`**:
The release-manifest section declaring the Nuitka compile of the product's Python backend into a Windows executable: the interpreter and packages to compile, what data to embed versus ship separately, and the self-check to run on the freshly compiled exe.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**`electron`**:
The release-manifest section declaring the Electron shell around the compiled backend and how its installer is produced: the generic `electron_builder` path, or a product's own `repo_hook` installer.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**vendor artifact**:
A binary the package ships but git cannot hold (ffmpeg, an embedded interpreter): kept on the build machine's own cache under a fixed path, copied into the package and checked against a sha256 recorded in a lock file, never downloaded during the build.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**runtime asset**:
Data that ships beside the compiled exe rather than embedded inside it, read by path at run time: for a package that cannot be embedded at all, one too large to unpack on every launch, or one that must stay replaceable after install.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**self-check module**:
The module a compiled exe can run on its own, before it serves its first request, that imports everything the app needs: the one guard between a missing dynamic dependency and a customer finding it first.
_Home_: `mmw-v2/skills/exe-release/references/new-product.md`

**smoke**:
The release-manifest field naming the compiled exe's self-check invocation and the modules it must be able to import, run right after the compile. Also the guard on `nofollow_imports`: a nofollow pattern that would block one of those modules is caught here, not forty minutes into the next compile.
_Home_: `mmw-v2/skills/exe-release/references/key.md`

**`diagnose_rules`**:
A release manifest's own log-pattern rules for this product's build, matched before the skill's general table because a product knows its own log's shape first; each rule's fingerprint prefix decides the release engine's next move the same way the general table's does.
_Home_: `mmw-v2/skills/exe-release/references/key.md`, `scripts/diagnose_core.py`

### The build machine

**build machine**:
The (often remote, Windows) machine that compiles and packages a product over SSH, named by `RELEASE_REMOTE_HOST`/`RELEASE_REMOTE_ROOT` or, failing those, a `remote-build.json` beside the release manifest. It receives only `git archive HEAD`, never a dirty working tree.
_Home_: `mmw-v2/skills/exe-release/references/new-product.md`, `SKILL.md`
