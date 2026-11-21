# Skill authoring

mmwstack can capture a recurring task in a skill and an operator's working habits in a personal mode. A blind eval checks how a change to those instructions affects the work an agent produces.

## Language

### Skill scope and discovery

**Task-specific skill**:
A skill for one repeatable job, such as reviewing a database migration. Its scope is the work to perform. A personal mode describes how an operator wants agents to work across tasks.

**Personal skill**:
A skill in the operator's own skills directory, available across their projects.

**Project skill**:
A skill in a repository's skills directory, shared with people and agents working in that project. A project can share a personal mode if its author stores the mode there.

**Skill frontmatter**:
The metadata at the start of a skill. The name identifies the skill. The description says what it does and who calls it or when to select it. Under Write for Where It Is Read, the description must make sense to an agent that can see only the skill listing. The same principle applies to a delegate reading a brief without the main chat. [principle-write-for-where-it-is-read](../../../skills/principle-write-for-where-it-is-read/SKILL.md)

**Trigger scenario**:
A situation in which the skill should apply. The agent selects a skill from its description, so the description gives the agent enough information to recognize that situation. For a skill that should run only on the user's request, the description identifies the caller.

**Progressive disclosure**:
The arrangement in which a skill gives its essential instructions in its main file and links directly to detailed references. An agent reads the detail when the task calls for it.

**Verbatim text**:
Wording the operator supplies for inclusion in a skill. The same words, in the same order, become part of the skill's instructions.

**Degrees of freedom**:
The choices a skill leaves to the agent. High freedom uses prose where several approaches work. Medium freedom supplies a template or preferred pattern. Low freedom prescribes a particular procedure or script where variation can cause failure.

**Skill authoring pattern**:
A way to express a task in a skill. A template fixes the output format. Worked examples show acceptable results. A workflow sets out steps, a conditional workflow selects a path, and a feedback loop repeats a check after a correction. Bug diagnosis uses *feedback loop* for a different thing. [Feedback loop](../investigation/GLOSSARY.md#bug-diagnosis)

**Skill validation**:
The authoring playbook's check that a skill declares its name and description and that its references and cross-skill links resolve. Structural behavior can have test cases. For subjective output, such as a personal mode's voice, the operator reviews the result.

[writing-for-agents](../../../skills/writing-for-agents/SKILL.md) · [create-skill](../../../skills/create-skill/SKILL.md) · [Authoring or modifying a skill playbook](../../../skills/mmw-mode/playbooks/authoring-a-skill.md) · [Routing and delegation](../routing-and-delegation/GLOSSARY.md)

### Personal modes, session reviews, and recurring corrections

**Personal mode skill**:
A skill named for an operator that captures their working conventions, such as when they expect delegation, what evidence they accept, or how they want a reply written. The operator normally activates the mode explicitly.

**Preference signal**:
A statement, correction, or recurring choice in the operator's conversations that may express a working convention. Patterns observed in at least two separate slices of workspace history carry more weight than an isolated instance. The operator can supply preferences directly.

**Update mode**:
The form of a personal-mode revision that examines conversations since the last edit. New evidence can change a rule or justify an addition. Rules the operator has not contradicted remain in the skill.

**Trigger accuracy**:
How reliably a skill's description causes it to be selected for its intended requests. A personal mode can express the operator's preferences accurately yet need a description change if it loads at the wrong time.

**Mistake class**:
A repeated kind of error supported by at least two occurrences in the repository's history. Commits, reverts, review comments, recorded workarounds, and a session the operator names can establish the recurrence.

**Improvement candidate**:
A proposed change to a repository's environment, such as a navigation pointer, an unwired or missing guardrail, a coding standard, a tool optimization, a removed no-op, or wider information access. A session retro, an enforceable finding from a skill review, or a repository audit can surface one. Single-session or standing gaps wait for operator approval; confirmed mistake classes are fixed and proved directly. Distinct from an Arena or Eval *candidate*.
_Avoid_: backlog finding.

**Level of enforcement**:
The means by which a repository prevents or detects a mistake class. Removing the mistaken path through architecture takes precedence. Other levels use types or a lint or CI check that names the fix, then a behavioral test, and finally written guidance for a judgment call. A new check has to fail on a real past instance.

**Agent instruction file**:
A persistent instruction file loaded into every session's context window, such as `AGENTS.md` or `CLAUDE.md` in a repository or global scope. Keep it concise and use it mainly for navigation pointers rather than inline standards or tables.
_Avoid_: steering file.

**Rule table**:
A table in a dedicated repository standards or rules document (such as `CODING_STANDARDS.md` or `docs/RULES.md`) that pairs each rule with what enforces it, linked by a single navigation pointer in the agent instruction file. A repeated correction against an unenforced rule exposes a gap and escalates to a higher level of enforcement. A rule leaves the table once the underlying mistake is impossible.

**Rule exception**:
A human-approved allowance at the line where an enforcement check would otherwise fail. The exception records its reason and expiry date.

**Navigation pointer**:
A context pointer in an agent instruction file that tells the agent where to find a file or doc. Agent instruction files hold little besides these.

**Guardrail**:
An automated check that runs without the agent's help, such as a pre-commit hook or a CI job that runs lint, typecheck, and tests. A repository with none leaves every mistake to review. [Repo checks](../repo-checks/GLOSSARY.md) defines the repository's checks and automatic moments.

**Context pressure**:
The load of exploring, writing, and debugging that an agent carries. The **implementation agent** carries the most. The **review agent** receives a diff and carries the least, so it enforces coding standards for genuine judgment calls.
_Avoid_: reviewer agent.

**Durable learning**:
A finding from a session transcript that will still hold in six months, would change a future agent's decision, and routes to an existing skill the session used or should have fired. The agent running [correct](../../../skills/correct/SKILL.md) ties it to a specific moment in the transcript and proposes an edit on the skill's editable source.

**Missed trigger**:
A skill that was available and suited to the task but did not fire. Its finding routes to tuning the skill's `description`. A body edit concerns a skill the transcript shows the agent used, for example by reading its instructions, naming it in a delegation brief, or running its documented commands.

**Accepted finding**:
A proposed skill edit from a session review, giving its problem, proposed change, target skill, and editable destination. The operator chooses which accepted proposals to apply.

**Rejected finding**:
A session skill proposal the agent drops with a reason, such as guidance the target skill already gives, a drifting detail (SHA, version, count), or a one-off that would not change a future decision. Enforceable code or environment lessons route as improvement candidates rather than skill prose.

[automate-me](../../../skills/automate-me/SKILL.md) · [correct](../../../skills/correct/SKILL.md) · [principle-encode-lessons-in-structure](../../../skills/principle-encode-lessons-in-structure/SKILL.md) · [Make it yours](../../guide/09-make-it-yours.md)

### Blind evaluation

**Eval**:
The playbook for testing how a change to a skill, prompt, or project structure affects agent behavior in a blind trial. The main chat reads every candidate's output and compares its own assessment with the judge's verdict before recommending whether to promote the variant.

**Eval variant**:
The version of the skill, prompt, or structure that a candidate receives for the trial. Candidates work independently on the same task, so differences in their outputs can be assessed against the same criteria.

**Observer effect**:
A change in candidate behavior caused by clues that an evaluation is taking place. A directory named for a benchmark or a request to list every principle applied can reveal what the trial measures.

**Blinding**:
Withholding the evaluation's purpose, its rubric, and the existence of other candidates from each candidate. The judge knows the task is an evaluation and sees the outputs under neutral labels that conceal the model and variant.

**Organic prompt**:
The shared task request written as an operator would ordinarily give it. It describes the desired result without revealing what the judge will measure.

**Sanitized environment**:
A fresh candidate workspace containing its own variant and the material an ordinary task would supply. File and directory names resemble a real project. The coordinator's conversation, other candidates' work, and the judge's rubric stay outside it.

**Eval rubric**:
The three to six concrete criteria written before the trial to define success. Eval requests an independent read-only judge from Arena's cross-judge pool. When two variants are compared, one blinded judge scores both sets of outputs in one pass on the same scale.

**Chain-following**:
Whether the candidate followed the intended sequence of skills or instructions. The execution transcript shows which files the candidate opened, and the completed work shows how it used them. If the transcript is unavailable, the playbook records chain-following as unverified.

[Eval playbook](../../../skills/mmw-mode/playbooks/eval.md) · [arena](../../../skills/arena/SKILL.md) · [Make it yours](../../guide/09-make-it-yours.md)

### Requests, replies, and teaching

**Help question**:
A request for guidance on using mmwstack. The answer gives the relevant explanation, a prompt the operator can send, and the source behind it. The operator decides whether to start that work.

**Goal restatement**:
The agent's account, in its own words, of the operator's goal and the problem behind it. The operator can catch a misunderstanding before the work starts.

**Reply restatement**:
A plain-language restatement of the agent's preceding message, with a little context, in simplified technical English and the project's glossary terms. The input is the answer the operator just read.
_Avoid_: wait-what.

**Rewritten prompt**:
The result of sharpening a task before the operator sends it. It names the original material a professional would inspect, the methods they would use, and an independent check on the result. Choices reserved for the operator remain open.

**Teaching explanation**:
A plain account of what a change or subsystem is, how it works, and why it took that form. A subsystem explanation draws on the mechanics from [how](../../../skills/how/SKILL.md) and the evidence about intent from [why](../../../skills/why/SKILL.md). It preserves the degree of confidence in that evidence. Successive diagrams can introduce the moving parts one at a time.

[mmw-help](../../../skills/mmw-help/SKILL.md) · [in-your-own-words](../../../skills/in-your-own-words/SKILL.md) · [bro](../../../skills/bro/SKILL.md) · [sharpen](../../../skills/sharpen/SKILL.md) · [teach](../../../skills/teach/SKILL.md)

### Documentation and prose

**Document mode**:
The reader's purpose for a document in the Diátaxis framework. Whether the reader needs action or understanding, for learning or for work, determines which of four modes applies.

**Tutorial**:
A learning document in which the reader builds something by following a sequence. Each step gives the learner a result they can recognize.

**How-to**:
A procedure for a reader who already knows the subject and needs to accomplish a specific task. It can include choices that depend on the reader's situation.

**Reference**:
Facts organized for lookup while working, such as a skill's accepted inputs or the meaning of an outcome. Under Files Describe the Present, working documents describe their subject as it is now. A decision record can explain a change and why it was made. [principle-files-describe-the-present](../../../skills/principle-files-describe-the-present/SKILL.md)

**Anchored reference**:
A reference that names its subject where the reader encounters it, using the name from the source or glossary. Under Anchor Every Reference, a path or section heading locates the evidence and the surrounding words explain what it establishes. [principle-anchor-every-reference](../../../skills/principle-anchor-every-reference/SKILL.md)

**Explanation**:
A document about one subject that answers a why question through context, history, constraints, or tradeoffs.

**Technical-writing standard**:
The four layers mmwstack applies to documentation. Diátaxis determines the document mode. Google developer style identifies the actor and writes to the reader. Simplified Technical English (STE) gives each instruction one meaning. Global English makes conditions, modifiers, and references unambiguous.

**AI tell**:
A pattern of generated prose that an editor can remove while preserving the intended meaning and tone. The catalog assigns stable rule numbers to patterns such as synonym cycling, vague attribution, and over-compression.

[technical-writing](../../../skills/technical-writing/SKILL.md) · [unslop](../../../skills/unslop/SKILL.md) · [Make it yours](../../guide/09-make-it-yours.md)
