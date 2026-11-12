# Product verification

Product verification connects a claim about a specific version of a product to an action, an observation, and a result someone else can inspect.

## Language

### Evidence and observation

**Verification**:
A check of a specific claim against the relevant version of the code, running product, or artifact. The Prove It Works principle calls for direct observation of the path or state the claim depends on. A planned check produces evidence when someone runs it.

**Verifier**:
An agent assigned to check a claim at a specified revision. A PR verifier checks the change independently of its author. In formal verification, a verifier can also be a software tool. [Pull request delivery](../pull-request-delivery/GLOSSARY.md) and [Formal verification](../formal-verification/GLOSSARY.md).

**Product surface**:
The interface through which the product user or caller experiences the behavior, such as a web UI, a terminal, a mobile app, a service API, or a library's public interface. An outcome that crosses two surfaces can require observations on both.

**Test seam**:
The public interface at which a test can observe the behavior in question. A test can exercise the download command even when several module boundaries lie behind it.

**Evidence**:
A source or observation that bears on a claim. A failing run is evidence too.

**Proof**:
Evidence that establishes the claimed result under the stated conditions. For a saved edit, the action, the resulting screen, and a readback of the stored value can together establish that the edit persisted.

**Proof artifact**:
A record another person can inspect after a check, such as a recording of the user action and its result, a terminal transcript, or the request and response. For a project verification skill, proof artifacts remain available after cleanup.

**Pass predicate**:
The observable condition that decides whether a verification scenario passes. For a download, the saved artifact might be the file and the predicate might be that it contains exactly the selected records. The spec supplies the expected result. [Planning and tickets](../planning-and-tickets/GLOSSARY.md).

Sources include [to-spec](../../../skills/to-spec/SKILL.md), [principle-prove-it-works](../../../skills/principle-prove-it-works/SKILL.md), the [Multi-phase plan playbook](../../../skills/poteto-mode/playbooks/multi-phase-plan.md), and the [verification guide](../../guide/06-verify-and-ship.md).

### Claims and verdicts

**Falsifiable claim**:
A statement of the condition, the result to observe or measure, and the threshold that would settle the claim. A threshold can be an exact outcome, such as an exit code of zero.

**Verification baseline**:
The observed result on the old state, such as the merge base, a parent commit, or the failing reproduction. A performance comparison uses a measurement baseline. [Performance](../performance/GLOSSARY.md#benchmark-claims).
_Avoid_: baseline alone when the comparison might instead refer to an approved design or a frozen reference image.

**Treatment**:
The observed result on the changed state under the same command, data, warmup, and environment as the verification baseline. The difference between the two results is the delta.

**Verification verdict**:
The conclusion about one falsifiable claim. `VERIFIED` means the result moved in the predicted direction by the claimed threshold, with no evident confounding factor. `NOT VERIFIED` means a valid comparison showed no change, the wrong direction, or a result below the threshold. `INCONCLUSIVE` means the comparison could not settle the claim, for example because the baseline was missing, the signal was noisy, or the environments differed.
_Avoid_: using a claim verdict as the merge verdict on a PR.

The claim verdicts come from [verify-this](../../../skills/verify-this/SKILL.md).

### Control of the running product

**Control skill**:
A skill that drives an interface. A terminal control skill can send a key and capture a prompt. A browser control skill can click a button and record the new state. Native mobile uses the project's simulator driver when available.

**Local harness**:
The repeatable setup that runs the app, sends input, and observes the result on the machine under test. It can be a repository's existing test or demo harness, a terminal session, a browser connection, or a direct HTTP request to a service.

**Terminal harness**:
A local harness for an interactive CLI or text user interface. A managed `tmux` session or a pseudo-terminal (PTY) can deliver keystrokes, interrupts, and resize events and capture the screen. A prompt or other visible pattern tells the harness when the next action can run.

**Browser harness**:
A local harness for a web, IDE, or Electron interface. It drives a browser page directly or connects to a running Chromium instance through the Chrome DevTools Protocol (CDP). A fresh page snapshot shows which control is available after each interaction.

**App marker**:
An observable identifier that selects the correct app or window when several pages share a debug port. A stable root element or landmark can identify the app. Within the page, stable handles such as accessible roles and names identify the intended control.

**Control CLI**:
A project's command-line tool for driving its app. A verification skill can call its commands to operate a browser, invoke a product command, or inspect a result. The bundled skill for controlling interactive terminal programs is [control-cli](../../../skills/control-cli/SKILL.md).

Sources include [control-cli](../../../skills/control-cli/SKILL.md), [control-ui](../../../skills/control-ui/SKILL.md), and the [project verification guide](../../guide/06-verify-and-ship.md#create-a-project-verification-skill).

### Feature map

**Verification skill**:
A project-local skill, usually named `verify-<app>`, for launching the real app, driving mapped features as a user would, and capturing evidence. Its instructions identify how to launch, check, drive, and clean up an instance and how to use any helper it ships.

**Launch**:
The part of the verification skill that brings the named build to a usable state, including required migrations and seed data. For a short-lived CLI, launch prepares the executable and each drive starts its own session.

**Doctor**:
A read-only check that identifies an instance and establishes that it is ready to drive. The project's checks can include its build revision, port ownership, and authentication. A healthy process can still need a reset if the user interface is stuck.

**Drive**:
A sequence of actions through the real user path, with a concrete observable result for each action. A drive that saves data checks both what the user sees and the resulting side effect. A dry run supplies evidence about the effects that were actually observed.

**Cleanup**:
Teardown of the instances, processes, and scratch data that the verification run created. The skill names a separate location where its proof artifacts survive teardown.

**Feature map**:
The verification skill's maintained index of user-facing features, with a file for each mapped feature. Each file names the sub-features, every user entry point, the actions that drive them, their observable results, and the gotchas that affect coverage.

**Feature entry**:
The recipe for one mapped feature. `Sub-features` identifies distinct behaviors. `How to get to it (user POV)` lists the user entry points. `Driving it with <harness>` gives preconditions and pairs actions with commands and results. `Gotchas` records traps that affect a run.

**User entry point**:
A particular route to a feature, such as the New note button, its keyboard shortcut, or the create command. Evidence identifies the route actually used. Verification of one route leaves the other mapped routes to check.

**Precondition**:
The state a journey needs before its first action, such as a build with a given feature enabled, an account with the required access, or a seeded record. If required seed data is missing, that journey records the failure.

**Mutation proof**:
Evidence of a change from a second, read-only view of the stored result. In the feature-map example, reopening a note from the list shows what persisted after Save.

**Stand-in**:
A substitute verification environment, such as a container used for a fresh VM. The proof identifies any setup the stand-in supplied that the real target still needs to demonstrate.

Sources include [create-verification-skill](../../../skills/create-verification-skill/SKILL.md), the [feature entry contract](../../../skills/create-verification-skill/references/feature-map-example/README.md), and the [create-note example](../../../skills/create-verification-skill/references/feature-map-example/create-note.md).

### Verification skill maintenance

**Source wave**:
The read-only part of a feature-map audit. One source reader per feature returns the behavior, its source entry points, likely documentation drift, and a recipe for the live check.

**Live pass**:
The part of the audit in which one coordinator exercises every mapped feature in the running app. A long-lived app can share an instance across drives. A short-lived CLI uses fresh isolated sessions when its verification skill specifies them.

**Verified-unreachable**:
The feature-level result `verified-unreachable`. The verifier records the route it attempted and the concrete prerequisite that prevented it from reaching the feature, such as an entitlement or an operating system.

**Doc drift**:
A wrong or missing description of actual user-facing behavior in the verification skill or feature map. A route's omitted prerequisite is doc drift even when the verifier correctly reports the route as unreachable.

**Harness gap**:
Working product behavior the current harness cannot reach or exercise. A corrected harness has to demonstrate the same behavior in a live drive.

**Product gap**:
Broken behavior in the app itself. The audit records a product regression as a finding for the operator. Edits from the maintenance run cover the verification skill, its map, and its harness.

**Maintenance outcome**:
The result for the whole product-verification audit. `clean` means every feature received source and live coverage and there is nothing to ship. `changed` means one PR carries proven corrections. `blocked` means the audit could not complete coverage or ship a proven correction safely.

The feature-map audit and its outcomes come from [maintain-verification-skill](../../../skills/maintain-verification-skill/SKILL.md).
