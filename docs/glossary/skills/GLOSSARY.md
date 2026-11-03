# Skills

Every skill in the cloud edition. The heading is the `name` in that skill's frontmatter. Call the skill by that English name.

Do not invent a Chinese name for a skill, or for any term in this file.

## Language

### Workflow

**dispatch**:
The skill that coordinates an authorized spec or one ticket, sends a Worker or a review-axis subagent, or carries out an assigned ticket.
_Avoid_: any invented Chinese name.

**to-spec**:
The skill that turns the current conversation into a spec and publishes it on the project issue tracker.
_Avoid_: any invented Chinese name.

**to-tickets**:
The skill that breaks a plan, a spec, or the current conversation into tickets. Each ticket is a tracer bullet and a vertical slice, and it records which tickets it is Blocked by.
_Avoid_: any invented Chinese name.

**wayfinder**:
The skill that plans work larger than one session as a shared map of decision tickets, and resolves those tickets until the destination is clear.
_Avoid_: any invented Chinese name.

**retro**:
The skill that, after the delivery PR exists, reviews that delivery and makes each repeated agent mistake impossible. The agent that reads the diff for this skill is the retro agent.
_Avoid_: any invented Chinese name.

**pr**:
The skill for writing a PR body.
_Avoid_: any invented Chinese name.

**code-review**:
The skill for reviewing a branch, a PR, or other uncommitted changes.
_Avoid_: any invented Chinese name.

**wait-what**:
The skill that re-pitches a message that did not land. `ketchup` catches up on what changed. `restate` plays the goal back before work starts.
_Avoid_: any invented Chinese name.

**sharpen**:
The skill that makes a task deeper, then rewrites the prompt.
_Avoid_: any invented Chinese name.

### Verification

**create-verification-skill**:
The skill that generates the project-local skill `verify-<app>`, which drives the app the way a user does.
_Avoid_: any invented Chinese name.

**maintain-verification-skill**:
The skill that keeps a project's verification skill and feature map honest, in one live session, with at most one PR of proven corrections.
_Avoid_: any invented Chinese name.

**write-tests**:
The skill that writes tests while landing code, at the seam the task supplies.
_Avoid_: any invented Chinese name.

**diagnosing-bugs**:
The diagnosis loop for hard bugs and performance regressions.
_Avoid_: any invented Chinese name.

**trace-forensics**:
The skill that diagnoses a captured profiling artifact after the fact. The deliverable is a diagnosis.
_Avoid_: any invented Chinese name.

**runtime-forensics**:
The skill that diagnoses a runtime symptom from live instrumentation. The deliverable is a diagnosis.
_Avoid_: any invented Chinese name.

### Release

**exe-release**:
The skill that builds an official install package from the code on the current branch.
_Avoid_: any invented Chinese name.

### Artifacts

**html**:
The skill for one self-contained HTML file, and the router to a specialist when the file is a diagram, a plan, a wireframe, or a mockup.
_Avoid_: any invented Chinese name.

**html-diagram**:
The specialist skill for a self-contained HTML diagram.
_Avoid_: any invented Chinese name.

**html-plan**:
The specialist skill for a self-contained HTML plan.
_Avoid_: any invented Chinese name.

**html-prototype**:
The specialist skill for a mockup or for Prototype, the working-flow fidelity mode.
_Avoid_: any invented Chinese name.

**html-wireframe**:
The specialist skill for a low-fidelity HTML wireframe.
_Avoid_: any invented Chinese name.

**design-artifact**:
The skill for the visual direction of an HTML artifact: palette, type, and layout.
_Avoid_: any invented Chinese name.

**big-pics-little-words**:
The skill that explains the current subject in HTML with large visuals and little text.
_Avoid_: any invented Chinese name.

**prototype**:
The skill that builds a logic demo or a UI prototype, including for a wayfinder:prototype decision ticket. That artifact is not Prototype mode.
_Avoid_: any invented Chinese name.

**wizard**:
The skill that generates an interactive bash wizard for steps only a person can perform.
_Avoid_: any invented Chinese name.

### Code shape

**improve-codebase-architecture**:
The skill that scans a codebase for deepening opportunities and presents them as an HTML report.
_Avoid_: any invented Chinese name.

**codebase-design**:
The skill that sketches types, signatures, and module structure before code. codebase-dic calls this the sketch.
_Avoid_: any invented Chinese name.

**codebase-dic**:
The shared vocabulary for deep modules: module, interface, depth, seam, adapter, leverage, locality. It is a reference, not a session.
_Avoid_: any invented Chinese name.

**refactoring**:
A behavior-preserving change to structure or shape.
_Avoid_: any invented Chinese name.

**unslop**:
The skill that cuts AI tells from writing.
_Avoid_: any invented Chinese name.

**no-comments**:
The skill that spawns Comment Sicko, fixes accepted findings, and offers encodings for claimed constraints.
_Avoid_: any invented Chinese name.

**hillclimb**:
The skill for sustained improvement of one metric against a target, with a measurement before and after each hypothesis and one commit per accepted win.
_Avoid_: any invented Chinese name.

**perf-issue**:
A measured slowness to trace and improve against a baseline.
_Avoid_: any invented Chinese name.

**benchmark-checklist**:
The skill that vets a performance measurement before anyone reports it or acts on it.
_Avoid_: any invented Chinese name.

### Language and teaching

**domain-modeling**:
The skill for building a project's domain model, including a `GLOSSARY.md` and an ADR.
_Avoid_: any invented Chinese name.

**technical-writing**:
The writing standard for docs, PR descriptions, and commit messages. A glossary entry is reference. An ADR is explanation.
_Avoid_: any invented Chinese name.

**writing-for-agents**:
The skill for writing documents an agent will follow, including skills and `AGENTS.md`.
_Avoid_: any invented Chinese name.

**teach**:
The skill that teaches a person a new skill or concept inside a teaching workspace.
_Avoid_: any invented Chinese name.

**research**:
The skill that investigates a question against primary sources and writes the findings as Markdown in the repo.
_Avoid_: any invented Chinese name.

**grilling**:
The skill that stress-tests a plan, a decision, or an idea by questioning the person who holds it.
_Avoid_: any invented Chinese name.

### Principles

**principle-anchor-every-reference**:
The principle that a reference keeps its source name and can be understood where it stands. An English source name stays English.
_Avoid_: any invented Chinese name.

**principle-files-describe-the-present**:
The principle that a file describes its subject as it is now.
_Avoid_: any invented Chinese name.

**principle-explain-the-number**:
The principle for reading a measurement: what decision it informs, what ran, and what the evidence supports.
_Avoid_: any invented Chinese name.

**principle-start-from-what-exists**:
The principle that a new approach starts by searching what already exists.
_Avoid_: any invented Chinese name.

**principle-read-before-you-conclude**:
The principle that a claim about a file waits until that file has been read.
_Avoid_: any invented Chinese name.

**principle-build-the-lever**:
The principle that repeated work becomes the smallest script or skill that can be run again.
_Avoid_: any invented Chinese name.

**principle-baseline-is-the-contract**:
The principle that a settled baseline is followed as written, and a conflict goes back to whoever decided it.
_Avoid_: any invented Chinese name.

**principle-everything-at-hand**:
The principle that an explanation sits beside the thing it explains.
_Avoid_: any invented Chinese name.

**principle-experience-first**:
The principle that a tradeoff favors the person who uses or maintains the result.
_Avoid_: any invented Chinese name.

**principle-minimize-reader-load**:
The principle that a design cuts the layers and the hidden state a reader must hold.
_Avoid_: any invented Chinese name.

**principle-outcome-oriented-execution**:
The principle for a migration: move the callers, remove the old path, and keep an external contract only when that contract was explicitly kept.
_Avoid_: any invented Chinese name.

**principle-sequence-verifiable-units**:
The principle that work advances in small units, each after its own check holds.
_Avoid_: any invented Chinese name.

**principle-type-system-discipline**:
The principle that invalid states are unrepresentable, and external data is parsed at the boundary where it enters.
_Avoid_: any invented Chinese name.

**principle-fix-root-causes**:
The principle that a fix corrects the source of a fault. The baseline, the harness, and the test stay as they are.
_Avoid_: any invented Chinese name.

**principle-write-for-where-it-is-read**:
The principle that a document is written for the reader who will use it, in the context that reader actually has.
_Avoid_: any invented Chinese name.

**principle-subtract-before-you-add**:
The principle that a change first removes redundant work, and stays the smallest change that keeps the required behavior.
_Avoid_: any invented Chinese name.

**principle-separate-before-serializing-shared-state**:
The principle that concurrent actors stop sharing a file, key, or branch when they do not need to, and only then take turns on what they still share.
_Avoid_: any invented Chinese name.

**principle-redesign-from-first-principles**:
The principle that a poor fit is redesigned as if the new requirement had been known from the start.
_Avoid_: any invented Chinese name.

**principle-prove-it-works**:
The principle that a claim of done is checked on the real artifact.
_Avoid_: any invented Chinese name.

**principle-never-block-on-the-human**:
The principle that reversible work continues, and a decision that belongs to the owner waits for the owner.
_Avoid_: any invented Chinese name.

**principle-model-the-domain**:
The principle that domain rules live in the structure of the data, not in scattered conditionals.
_Avoid_: any invented Chinese name.

**principle-make-operations-idempotent**:
The principle that a retried or interrupted operation converges by reconciling the state that is already there.
_Avoid_: any invented Chinese name.

**principle-guard-the-context-window**:
The principle that a large payload is read in pieces, and the active context keeps only what the current step needs.
_Avoid_: any invented Chinese name.

**principle-first-principles-thinking**:
The principle that an unsettled plan is judged from the constraint and the evidence, not from the inherited premise.
_Avoid_: any invented Chinese name.

**principle-encode-lessons-in-structure**:
The principle that a repeated mistake is made impossible by the structure, or is enforced by a mechanism.
_Avoid_: any invented Chinese name.

**principle-boundary-discipline**:
The principle that input is validated where it enters, and business logic stays pure behind that edge.
_Avoid_: any invented Chinese name.
