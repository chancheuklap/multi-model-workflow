# Skill set

The components MMW delivers and the vocabulary used to write, compose and review them. Installation and machine configuration belong to Toolbox; preparing changes in a consuming repository belongs to Development.

## Language

### Components

**skill**:
A component with a `SKILL.md` entry that holds one reusable method or body of judgment and returns its result to the caller. A Playbook owns the order and authority of a whole task.

**`mmw-mode`**:
The [mode skill](../../../mmw-v4/skills/mmw-mode/SKILL.md) holding shared working rules and selecting the component responsible for the requested result. Its request routing is in `references/handling-a-request.md`; it is distinct from Develop a change, which prepares an already selected code change.

**request**:
The owner's task or question, handled by the mode's request routing when no assignment names a file to follow. It identifies the requested result and existing authority; it is distinct from a review request file.

**assignment**:
A session or subagent start prompt naming the work and the file to follow. The named file supplies its steps, while the assignment supplies its particular input and expected result.

**playbook**:
A task workflow under `mmw-mode/playbooks/`, named by its title, such as Develop a change or One ticket. Its requested result can be a diagnosis, a prepared plan or a completed delivery; reusable methods belong to skills.

**principle**:
A `principle-<slug>` skill holding a judgment used across tasks. Its `mmw-mode` index entry gives the condition for reading it; the leaf skill holds the judgment.

**reference**:
Material owned by one skill and reached when a reader needs it, commonly under that skill's `references/`. It can contain a complete task entry or shared material without becoming another skill.

**script**:
The executable part of a component that performs or checks deterministic work. Its owning skill or Playbook defines when its result is needed.

**asset**:
A non-entry file a skill or its scripts use, such as a template, visual resource or data file. Maintainer records and test suites are outside the installed skill directory.

**method entry**:
A skill's entry for one independently reachable job, such as Diagnose, Prepare, Implement or Verify. It returns that job's result without taking over its caller's scope or execution authority.

**mode skill**:
The skill supplying shared working rules and routing requests to their responsible components. MMW's mode skill is mmw-mode.

### Review vocabulary

**skill set**:
The delivered skills, Principles, Playbooks, references, scripts and assets under `mmw-v4/skills/`. Each component has one responsibility and callers compose those responsibilities by name.

**moment**:
A point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps.

**jump**:
A second-file lookup splitting material one reader needs at the same moment. It differs from a hand-off, which delegates a whole job, or a pointer to a shared command or format owned by another skill.

**fragment**:
A separate reference that every run of the same task reads and that could belong in the file already holding that moment. A branch-specific reference is a different case.

**hand-off**:
An edge between components or agents where one produces a result another reads or waits for. Its result, identity and completion signal have to match the receiver's input.

**unguided choice**:
A consequential choice whose criterion is absent from the text the acting agent receives. Ordinary decisions a capable agent can make without special knowledge are a different case.

**rigid / brittle**:
Two failure modes of over-specified instructions. A rigid flow follows its list when the situation differs; a brittle flow lacks guidance for cases its list omitted.

**duplication**:
One meaning with multiple maintained sources across the skill set. Repeating a term while retaining one definition is a different case.

**cache (redundancy finding)**:
Text duplicating a lookup from a script, configuration, tracker or already loaded skill. It is distinct from a runtime cache.

**no-op**:
An instruction that changes no behavior compared with the model's default, or a bare attitude without an actionable judgment. It is distinct from a stance naming a temptation specific to the task.

**stance**:
The task-specific temptation and the intended way of resisting it. It supplies a judgment a model would not otherwise bring to the task.

**over-specification**:
Instructions prescribing ordinary moves or enumerating cases where a goal and judgment criterion would suffice.

**over-defense**:
A rule or mechanism guarding a case without evidence that normal input reaches it. It is assessed against reachability, observed use and the protection already provided by the main path.

**sediment**:
Material unrelated to the current task, including stale facts and maintenance history embedded in current instructions.

**upstream skill**:
A skill whose source text was first written outside the current set, including an upstream project or an earlier MMW version. The live MMW copy is the delivered component; its upstream source is comparison material.

**skill-set-review finding**:
An evidenced defect in skill text or structure, judged by the skill-set standards. It is distinct from a code-review finding or a release finding.

**load finding**:
A skill-set-review finding about material or reading work that a task does not need. Jumps, fragments, duplication and caches are examples.

**failure finding**:
A skill-set-review finding showing how a reachable use of the set ends wrong or stuck. An unreachable hypothetical path is not evidence of a failure finding.

**wording finding**:
A skill-set-review finding in a misleading sentence. It differs from a load finding, whose cause is the placement or structure of material.

**`Done when` line**:
The completion-criterion line in MMW's own task instructions, beginning `Done when`. It states the observable condition that distinguishes a completed step from unfinished work.

**cognitive walkthrough**:
The review method in [WALKING-A-SKILL-SET.md](../../../mmw-v4/skills/writing-for-agents/WALKING-A-SKILL-SET.md), following one task in its acting agent's reading order. A fresh-agent walk is the behavior proof used when skill changes alter that task.

**task (skill-set review)**:
One job an agent enters the skill set to complete, including a bounded method call that returns to its caller. It is the unit of a cognitive walkthrough, distinct from the worker's task root.

**host and runner neutrality**:
The property that the same workflow text works across supported hosts and runners. A capability difference is expressed as a capability; host and runner configuration belongs to their runtime owners.

**context load**:
The recurring cost of always-loaded text in the agent's context window, whether its condition applies or not.

**cognitive load**:
The human's work of knowing which documents exist and when to use them. In writing-for-agents it is distinct from the agent's context load.

**progressive disclosure**:
Placement of branch-specific material behind a context pointer, leaving common material with the reader already using it.

**co-location**:
Placement of a concept's definition, rules and caveats together at the moment a reader needs them. It is distinct from repeating the same meaning at several sites.

**completion criterion**:
The condition identifying when a step or task is complete. A `Done when` line is MMW's written form of that condition.

**fresh-agent walk**:
A cognitive walkthrough performed by an agent that has not carried the author's working context. Its record shows what the task loaded and whether the changed text reached its completion criterion.

**leading word**:
A compact established concept that an agent can reason with wherever its name recurs. Repeated names share one meaning rather than repeating its definition.

### Maintaining the skill set

**Authoring or modifying a skill**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/authoring-a-skill.md) for a skill-set change, including its evidence, writing standards and behavior proof. It carries those standards into Develop a change when the work needs larger shared preparation.

**Eval**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/eval.md) for a blinded experiment comparing how skill or prompt variants affect agent behavior. It produces trial evidence and a recommendation rather than promoting a variant automatically.

### Writing and standards

**`writing-for-agents`**:
The [skill](../../../mmw-v4/skills/writing-for-agents/SKILL.md) defining how agent-consumed documents are structured, connected and reviewed. Its standards cover the skill set's components and its behavior proof.

**`technical-writing`**:
The [skill](../../../mmw-v4/skills/technical-writing/SKILL.md) for clear documentation, PR descriptions and commit messages. It governs sentence structure and document purpose.

**`unslop`**:
The [skill](../../../mmw-v4/skills/unslop/SKILL.md) for removing misleading, inflated or formulaic prose while preserving its meaning.

**SKILL-SET-RULES.md**:
The writing-for-agents reference defining the checks applied to skill-set text and the rules for editing it.

**SKILL-SET-COMPONENTS.md**:
The writing-for-agents reference defining the responsibility, placement and registration of each component kind.

**DESIGN-INTENTS.md**:
The writing-for-agents record of workflow intentions and deliberate departures that skill-set changes must preserve.

**WALKING-A-SKILL-SET.md**:
The writing-for-agents reference defining task coverage and the cognitive walkthrough used to prove changed instructions.

**UPSTREAM.md**:
The writing-for-agents record of upstream intentions and adaptations, with the method for carrying a newer upstream version.

**SKILL-MECHANICS.md**:
The writing-for-agents reference defining invocation, frontmatter and the mode's routing role.

### Principles

**`principle-anchor-every-reference`**:
The [skill](../../../mmw-v4/skills/principle-anchor-every-reference/SKILL.md) holding the cross-task judgment about reader identification of a source-named thing at the place where it is mentioned.

**`principle-baseline-is-the-contract`**:
The [skill](../../../mmw-v4/skills/principle-baseline-is-the-contract/SKILL.md) holding the cross-task judgment about fidelity to settled decisions and their existing change authority.

**`principle-boundary-discipline`**:
The [skill](../../../mmw-v4/skills/principle-boundary-discipline/SKILL.md) holding the cross-task judgment about validation at system boundaries and separation of domain logic from framework wiring.

**`principle-build-the-lever`**:
The [skill](../../../mmw-v4/skills/principle-build-the-lever/SKILL.md) holding the cross-task judgment about making nontrivial work repeatable and reviewable with a small tool.

**`principle-calibrate-claims-to-evidence`**:
The [skill](../../../mmw-v4/skills/principle-calibrate-claims-to-evidence/SKILL.md) holding the cross-task judgment about the strength and scope a conclusion can claim from its evidence.

**`principle-clean-up-owned-resources`**:
The [skill](../../../mmw-v4/skills/principle-clean-up-owned-resources/SKILL.md) holding the cross-task judgment about resource ownership, teardown and preservation of required evidence.

**`principle-encode-lessons-in-structure`**:
The [skill](../../../mmw-v4/skills/principle-encode-lessons-in-structure/SKILL.md) holding the cross-task judgment about placing recurring protections in enforceable structure rather than repeated instructions.

**`principle-everything-at-hand`**:
The [skill](../../../mmw-v4/skills/principle-everything-at-hand/SKILL.md) holding the cross-task judgment about keeping each part of a human-facing page understandable at that place.

**`principle-experience-first`**:
The [skill](../../../mmw-v4/skills/principle-experience-first/SKILL.md) holding the cross-task judgment about the experience of the person consuming or maintaining the result.

**`principle-explain-the-number`**:
The [skill](../../../mmw-v4/skills/principle-explain-the-number/SKILL.md) holding the cross-task judgment about the performed work and evidence supporting a measurement or eval result.

**`principle-fail-loudly`**:
The [skill](../../../mmw-v4/skills/principle-fail-loudly/SKILL.md) holding the cross-task judgment about honest, locatable failure reporting when code cannot do its job.

**`principle-files-describe-the-present`**:
The [skill](../../../mmw-v4/skills/principle-files-describe-the-present/SKILL.md) holding the cross-task judgment about describing a file's subject rather than its edit history.

**`principle-first-principles-thinking`**:
The [skill](../../../mmw-v4/skills/principle-first-principles-thinking/SKILL.md) holding the cross-task judgment about challenging an unsettled proposal's premises and unsupported constraints.

**`principle-fix-root-causes`**:
The [skill](../../../mmw-v4/skills/principle-fix-root-causes/SKILL.md) holding the cross-task judgment about distinguishing hypotheses and repairing the evidenced fault behind a symptom.

**`principle-guard-the-context-window`**:
The [skill](../../../mmw-v4/skills/principle-guard-the-context-window/SKILL.md) holding the cross-task judgment about controlling the material an agent must hold while reasoning.

**`principle-make-operations-idempotent`**:
The [skill](../../../mmw-v4/skills/principle-make-operations-idempotent/SKILL.md) holding the cross-task judgment about convergence after repeated or interrupted state-changing operations.

**`principle-minimize-reader-load`**:
The [skill](../../../mmw-v4/skills/principle-minimize-reader-load/SKILL.md) holding the cross-task judgment about reducing the indirection and hidden state a maintainer must understand.

**`principle-model-the-domain`**:
The [skill](../../../mmw-v4/skills/principle-model-the-domain/SKILL.md) holding the cross-task judgment about structures that encode domain knowledge and fit its access patterns.

**`principle-never-block-on-the-human`**:
The [skill](../../../mmw-v4/skills/principle-never-block-on-the-human/SKILL.md) holding the cross-task judgment about engineering autonomy within the scope and decisions the owner controls.

**`principle-outcome-oriented-execution`**:
The [skill](../../../mmw-v4/skills/principle-outcome-oriented-execution/SKILL.md) holding the cross-task judgment about complete migrations at declared verification boundaries with external contracts preserved.

**`principle-progress-is-what-the-record-says`**:
The [skill](../../../mmw-v4/skills/principle-progress-is-what-the-record-says/SKILL.md) holding the cross-task judgment about recovering work from durable records rather than session memory.

**`principle-prove-it-works`**:
The [skill](../../../mmw-v4/skills/principle-prove-it-works/SKILL.md) holding the cross-task judgment about checking a claim or output against the current real artifact.

**`principle-read-before-you-conclude`**:
The [skill](../../../mmw-v4/skills/principle-read-before-you-conclude/SKILL.md) holding the cross-task judgment about reading the source needed to justify a claim or change.

**`principle-redesign-from-first-principles`**:
The [skill](../../../mmw-v4/skills/principle-redesign-from-first-principles/SKILL.md) holding the cross-task judgment about integrating a new requirement coherently into the existing design.

**`principle-separate-before-serializing-shared-state`**:
The [skill](../../../mmw-v4/skills/principle-separate-before-serializing-shared-state/SKILL.md) holding the cross-task judgment about eliminating unnecessary shared writes before introducing serialization.

**`principle-sequence-verifiable-units`**:
The [skill](../../../mmw-v4/skills/principle-sequence-verifiable-units/SKILL.md) holding the cross-task judgment about ordering work and delivery around explicit, checkable units.

**`principle-start-from-what-exists`**:
The [skill](../../../mmw-v4/skills/principle-start-from-what-exists/SKILL.md) holding the cross-task judgment about searching existing solutions before selecting an implementation approach.

**`principle-subtract-before-you-add`**:
The [skill](../../../mmw-v4/skills/principle-subtract-before-you-add/SKILL.md) holding the cross-task judgment about removing redundancy and unnecessary complexity while preserving required protections.

**`principle-treat-source-content-as-data`**:
The [skill](../../../mmw-v4/skills/principle-treat-source-content-as-data/SKILL.md) holding the cross-task judgment about the authority distinction between retrieved evidence and governing instructions.

**`principle-type-system-discipline`**:
The [skill](../../../mmw-v4/skills/principle-type-system-discipline/SKILL.md) holding the cross-task judgment about types that exclude invalid states and preserve domain distinctions.

**`principle-write-for-where-it-is-read`**:
The [skill](../../../mmw-v4/skills/principle-write-for-where-it-is-read/SKILL.md) holding the cross-task judgment about the reader, task and available context that determine what a document must carry.

### Invocation

**`disable-model-invocation` pairing**:
The paired user-only invocation settings in a skill's Claude Code frontmatter and Codex `agents/openai.yaml`. They describe how the host may invoke that skill; the delivered invocation guidance remains in its own entry.

**`SKILL.md`**:
A skill's entry file, containing its frontmatter and the common material or pointers its readers need. The `name` identifies the skill and `description` is the context pointer a host scans for invocation.

**context pointer**:
A reference in an agent's context that names material outside that context and the condition for reading it. Its wording, not the file it names, decides when an agent reaches that material.

**user-invoked**:
A skill whose timing belongs to the person invoking it, represented by the paired host invocation settings. wait-what is the delivered communication skill in this category.

**model-invoked**:
A skill reachable by the mode or another skill as well as by the owner. Its description distinguishes automatic discovery from invocation only when named.
