# Release

How this toolbox ships an installable package for a product on the current branch, through the `exe-release` skill: which products a change reaches, one product's release loop from a release manifest to a finished package, the automatic diagnosis and repair of what breaks in that loop, and the check that a shipped set came from one commit.

## Language

### The run

**product**:
The shipping unit `exe-release` packages: one per release manifest, named by the manifest's own `product` field and used in fingerprints and delivery paths. Step 2 of a run decides, from the paths a change touched, which products to ship.

**release manifest**:
The JSON file declaring how one product is packaged, one file per product. Its filename and every script's `--adapter` flag call it the adapter; prose calls it the release manifest, and anything that only differs by value across products belongs in it, never in a product repository's own script.

**`exe-release`**:
The [skill](../../../mmw-v4/skills/exe-release/SKILL.md) for packaging the current branch's committed product code through its release manifests and user install test. It is distinct from promoting or installing MMW itself.

**package scope file**:
The release input classification naming product-specific and shared packaging paths. It lets the same-commit check recognize an older package whose inputs are unchanged.

### The release engine

**release engine**:
The release-flow.sh state machine driving one product's build stages and bounded repair attempts. Its recorded state supplies the continuation after interruption.

**release loop**:
One product's release-engine run, with its current stage, attempts and budget in release-state.json. A multi-product release completes one loop at a time.

**`where`**:
`release-flow.sh where`, the release engine's status command: every step of driving a release starts here, and the agent does what the **`where` state** says rather than picking the next stage itself.

**`where` state**:
The release engine's reported pending-stage, success, pause or corrupt-state family. It describes the next permitted action independently of the command's exit code.

**`release-flow.sh resume`**:
`release-flow.sh resume`, continuing a paused release loop once its cause is gone: when HEAD has moved since the release loop's commit, every stage runs again against the new HEAD, so a code change reaches it only once committed; on the same HEAD it restarts from the first failed or running stage.

**close**:
`release-flow.sh close`, finishing a product's release loop: it refuses one that has not shipped and, once it has, writes the delivery record.

**abort**:
`release-flow.sh abort`, dropping the current release loop without writing a delivery record, unlike `close`.

**delivery record**:
What `close` leaves once a product's release loop ships: the product's name, the commit it shipped, and when. The same-commit check reads it back; `abort` writes none.

**same-commit check**:
The release-engine check that all shipped products use the current commit or unchanged packaging inputs established by a package scope file. It detects mixed product inputs rather than demanding a rebuild of unchanged packages.

**release receipt**:
`release-flow.sh receipt`, the rendered account of the open release loop, headed `# release receipt`: every attempt tried so far (its stage, what kind of action it was, its outcome and fingerprint) and how many times each root-cause fingerprint has recurred. Given to the user as-is on a `PAUSED:needs-redirection` state, and read on `CORRUPT:`.

### Diagnosis and repair

**release finding**:
A build or release diagnostic identifying its product, failed dimension and supporting location. A failing result carries its repair classification and root-cause fingerprint, distinct from a skill-set-review finding.

**root-cause fingerprint**:
The release finding's identifier of its failure cause. Its transient or environment class can select retry or pause before tier-based repair applies.

**tier**:
The release repair classification P0, P1 or P2 for redirection, a fix brief or deterministic derive repair. It is distinct from a code-review severity or a test layer.

**diagnoser**:
The release mechanism translating a failed stage log into findings using product-specific rules and the general diagnose_core.py table. A manifest can supply its own diagnosis command.

**remediation**:
The suggested repair on a release finding, carried into a fix brief or environment-context pause.

**fix brief**:
The release repair assignment generated from a P1 finding, carrying its evidence and applicable repair rules. It is distinct from the dispatch brief supplied for a second opinion.

**derive**:
A product's declared deterministic regeneration action, used for P2 repair. It is distinct from an agent-authored fix to product behavior.

**circuit breaker**:
The release engine's bounded-repeat protection for one recurring root-cause fingerprint. Reaching its limit pauses automatic repair for the owner's redirection.

**budget**:
The release loop's bounds on repair attempts and elapsed time. Spending the budget produces a pause rather than permission to keep trying.

**fix round**:
One P2 `derive` run that changed and committed something, counted in `budget.fix_rounds` against the `--max-rounds` cap. Distinct from a ticket's own round, one pass fixing a criterion or a code-review finding.

**`release-flow.sh surface`**:
The release-engine operation pausing a loop for missing context or owner redirection. It is distinct from a product's user interaction surface.

### Stages and hooks

**stage**:
One named step of a product's release build, including manifest-defined preparation and the engine's packaging stages. It is distinct from a ticket.checked stage.

**build hook**:
A product-defined callback in the release build, attached to a stable hook phase. It is distinct from a host hook and a git hook.

**hook phase**:
The fixed name a build hook hangs on: `runtime_ready`, `backend_ready`, `artifact_ready`, `installer_ready`, `release_ready`.

### Writing a release manifest

**`build_target`**:
The release manifest section defining the product's build and installer inputs. It identifies packaging particulars rather than a separate release engine per product.

**`python_backend`**:
The release-manifest section declaring the Nuitka compile of the product's Python backend into a Windows executable: the interpreter and packages to compile, what data to embed versus ship separately, and the smoke run on the freshly compiled exe.

**`electron`**:
The release-manifest section declaring the Electron shell around the compiled backend and how its installer is produced: the generic `electron_builder` path, or a product's own `repo_hook` installer.

**`toolchain`**:
The release-manifest list of tools the build machine must have beyond those the generated build script already invokes. Step 1 of the build checks both, so a derived tool restated here is a tool demanded and never used.

**`event_sink`**:
The optional release manifest destination for structured release-loop events. It is distinct from ticket events posted to the tracker.

**vendor artifact**:
A binary the package ships but git cannot hold (ffmpeg, an embedded interpreter): kept on the build machine's own cache under a fixed path, copied into the package and checked against a sha256 recorded in a lock file, never downloaded during the build.

**runtime asset**:
Data that ships beside the compiled exe rather than embedded inside it, read by path at run time: for a package that cannot be embedded at all, one too large to unpack on every launch, or one that must stay replaceable after install.

**smoke module**:
The module a compiled exe can run on its own, before it serves its first request, that imports everything the app needs: the one guard between a missing dynamic dependency and a customer finding it first.
_Avoid_: self-check module

**smoke**:
The release manifest contract for launching the compiled executable and checking its required imports. It is distinct from a new project's smoke ticket.

**`diagnose_rules`**:
The release manifest's product-specific log diagnosis rules. Their findings use the same repair classification as the general diagnoser.

### The build machine

**build machine**:
The local or remote machine packaging a committed product snapshot. Its declared setup and teardown belong to the release manifest rather than a different copy of the release engine.
