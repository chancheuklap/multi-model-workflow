# MMW design intents

What MMW's skill set is built to keep true, and the standard a change to it is held to. **Authoring or modifying a skill** reads it at **Read the standards** to name the intent a change serves. A change that breaks an intent is not made without the owner's word; MMW's deliberate departures from its upstreams, listed below, are decisions, not gaps.

Each intent says what is kept, the upstream intents it takes from [`UPSTREAM-INTENTS.md`](UPSTREAM-INTENTS.md) (kept as upstream has it, or adapted, and how), and its home: the files whose text carries the rule an agent acts on. This file is an index: the rule itself is written in its home, where the acting agent reads it. A change that adds, changes or drops an intent, or moves its home, changes its entry here in the same commit.

## Purpose and who it serves

1. **The owner, who does not read code, can trust a closed ticket and a shipped product.** Every other intent serves this one.
   Takes: P1, adapted (quality is sought so the owner can let go without reading the code, not to run more agents); P2, adapted (the unit trusted is a closed ticket, not an agent).
   Home: `mmw-v4/prompt/shared.md`.
2. **The set serves one owner.** No team and no human code review: every human gate falls on the owner, so gates are few and placed in the day where possible.
   Takes: P23, kept (pstack is the base, made the owner's own: `mmw-mode`); M5, adapted (control stays with the owner's product decisions, not with orchestrating each step).
   Home: `mmw-v4/prompt/shared.md`; `mmw-mode` `## Autonomy`.
3. **Product decisions are the owner's, engineering decisions the agent's.**
   Takes: M1, adapted (only product decisions go to the person); M17, adapted (the owner still approves the ticket breakdown; seams are the agent's); P6, adapted (adds the list of the owner's decisions, and the default an unattended session takes and records).
   Home: `principle-never-block-on-the-human`; `mmw-mode` `## Autonomy`.
4. **A reply to the owner leads with principle and effect, and every claim carries its evidence or its label,** so the owner can judge it without reading code.
   Takes: P14, adapted (written for an owner who does not read code); P34, kept; P42, adapted (as `wait-what ketchup`, using `wait-what`'s voice and the `diagram-design` skill for drawings); P43, adapted (as `wait-what in-your-own-words`, stopping after the restatement for confirmation).
   Home: `mmw-mode` `references/owning-a-task.md` `## Writing the reply`; `wait-what`.

## How the set is built and runs

5. **One entry routes each task to one playbook.**
   Takes: P4, adapted (`mmw-mode` keeps `poteto-mode`'s seven section headings in its order, each section's body split between the two files by reader); P38, adapted (the read is asked by the mode's own description instead of a host's reminder field); P30, kept (only the mode is read every time); M7, adapted (the trunk's stages became playbooks behind route lines); M27, adapted (the route lines are the one router).
   Home: `mmw-mode`'s description and `## Playbooks`, and its `references/owning-a-task.md`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## mode`.
6. **A text goes in the component that answers who needs it and at which moment, not the one its type suggests:** mode, playbook, principle, skill, reference, script, subagent prompt, configuration, user-level prompt.
   Takes: P29, adapted (adds the user-level prompt and configuration; no subagent definitions); M24, adapted (one skill, one directory; shared material placed by the moment it is used).
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The components and where they live`, `## The method`.
7. **A playbook is not a skill.**
   Takes: P31, adapted (every step carries its completion criterion); M6, adapted (orchestrating skills became playbooks; disciplines stay skills).
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## playbook`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Rules and completion criteria`.
8. **A rule enters the session at the moment it applies.**
   Takes: P5, P32 and P33, kept; P25, kept (`principle-guard-the-context-window`); M13, kept (a pointer's wording decides when material is reached; progressive disclosure); M14, kept (Pause safely points to existing artifacts).
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`; `mmw-mode` `## Principles`, `## Subagents`; `principle-guard-the-context-window`.
9. **Most skills run only when named; a few the model picks up by their description.**
   Takes: M26, adapted (the same trade, split as named-only against picked-by-description rather than person- against model-invoked); P30, adapted (pstack leaves 1 of 50 skills to the model, MMW 6 of 70); M6, adapted (the split has a different axis).
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Descriptions`; [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md) `## Invocation`.
10. **Skills are peers composed by name.**
    Takes: M25, adapted (the skill's name only, not a host's Skill tool; any skill can be named by any other); M24, kept (shared material lives in the skill that owns it); M28, kept; P37, kept (delegate by name, never restate); M33, kept (reading a glossary is a pointer; building the model names `domain-modeling`).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 6 and 7, `### Hand-offs`.
11. **A rule sits in the text the acting agent reads at the moment it acts.**
    Takes: M13, adapted (adds placement by the acting agent); P39, kept.
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`.
12. **A hand-off is an edge with one shape.**
    Takes: M14, adapted (hand-off documents became a ticket's fixed headings and events); M9, adapted (what is handed over lives on the tracker).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`.
13. **A start prompt carries data and one pointer** (the ticket, a base commit, where the task came from, then `Read the mmw-mode skill in full, then follow <what>.`, <what> being the file the agent works by, then `It is your whole task: …`); rules arrive through the mode and that file. The step that sends the agent names <what>, so the agent never guesses its job. A subagent's prompt opens and ends the same way, names the file or the steps it follows, holds everything else it needs, and states what it returns, where, and how long.
    Takes: P35, adapted (no subagent definition: the prompt that starts an agent sends it to the mode, which `poteto-agent` did for pstack's subagents); P17, adapted (a subagent's brief is complete).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Prompts written for other agents`. `mmw-mode` `SKILL.md` `## Subagents`; the `dispatch` skill's `roles.json`.
14. **Models by strength.**
    Takes: P3, adapted (another model means another session; the second opinion is the advisor session); P36, adapted (configuration in `models.json`, not in a host rule); P17, adapted (a worker keeps its session for its one fix; each named dispatch starts a fresh subagent).
    Home: `mmw-mode` `## Subagents` and `references/owning-a-task.md` `## Subagents`; the `dispatch` skill's `roles.json` session roles and `subagents` section, and `scripts/models.py`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## subagent`.
15. **One home per fact, registered in the same change.** `check_wiring.py` and `check_skill_frontmatter.py` hold this at the start of every suite under `mmw-v4/tests/` but `lib`, and the dispatch suite runs `check-interfaces.py`.
    Takes: M18, adapted (kept in step by checks); M29, adapted (no buckets: every directory with a `SKILL.md` is installed); P37, adapted (the frontmatter and link checks run first in every suite).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Redundancy and bloat`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 6.
16. **From an upstream, take the content, not only the shape.**
    Takes: P23, adapted (the owner's own mode on pstack's base, taken piece by piece after comparison).
    Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 1, 2 and 8; [`UPSTREAM-INTENTS.md`](UPSTREAM-INTENTS.md).
17. **A skill hands over understanding, then trusts the model.**
    Takes: M22, adapted (Matt trusts the model with very short text; MMW writes the full criterion where a night has nobody to ask); P37, kept (keep only prose that changes a decision).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 1 and 4.
18. **A change to the skill text is proven by a fresh agent walking a real task with only its trigger;** tests prove the scripts, not the text.
    Takes: P37, adapted (structural changes get a walk rather than only a test); P23, adapted (a walk on a real task rather than a blind eval).
    Home: [`WALKING-A-SKILL-SET.md`](WALKING-A-SKILL-SET.md); **Authoring or modifying a skill**'s **Prove it, once**.
19. **Text for an agent leaves no branch without a way on and no choice unguided;** examples use a neutral domain; a refusal puts the next step in its first lines.
    Takes: M13, adapted (adds the set's placement and writing rules).
    Home: `writing-for-agents` `SKILL.md`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`, `### Examples`, `### Refusals and output an agent reads`.

## The day

20. **A fact that can be looked up or run is looked up or run by the agent;** understanding comes before changing; only steps a person alone can take become a script that walks them through.
    Takes: M1, kept (facts are the agent's); P6, adapted (only "run it rather than ask"); P24, kept (`how`, `why`, `teach`); M15, kept in intent only (`wizard` and `to-questionnaire` are not in the set).
    Home: `mmw-mode` `## Autonomy`; the `how`, `why` and `teach` skills.
21. **Align before acting: grill until the questions run out.**
    Takes: M1, adapted (a round of questions waits for the fact-finding subagent); M17, adapted (seams are not put to the owner); P19, adapted (the data shape is an engineering decision in the spec); P44, adapted (named by To spec step **Check that nothing load-bearing is undecided**, with conclusions returned to the owner).
    Home: the `grilling` skill; **Grill with docs**; **To spec**; `sharpen`.
22. **The day settles every decision the owner holds, into the spec and the tickets; the night has nobody to ask.**
    Takes: P13, adapted (the unattended contract became the ticket and its criteria; an owner's decision met at night is recorded with its options and default); M9, adapted (decisions live in the spec and tickets on the tracker).
    Home: `mmw-mode` `## Autonomy` (**Unattended**); **To spec**; **To tickets**; `principle-baseline-is-the-contract`.
23. **The trunk: write a spec, cut it into narrow tickets through every layer (a task graph), implement, review once, deliver one pull request, retro.**
    Takes: M7, kept; M8, adapted (tickets carry Owns, Seam and runnable criteria); M3, kept (test first is the `tdd` skill's; the red-green loop's other half is intent 27); P20, adapted (the unit of work is the ticket; the unit of delivery is one pull request for a night or for a day's change); P27, adapted (the pull request stays the unit of delivery, and the tracker is also the work queue, through specs and tickets); P41, adapted (Opening a PR is written once, and run by One ticket and Run a night step 6; the last step of each playbook that opens a ticket is the hand-back to the owner).
    Home: **To spec**; **To tickets**; **Work a ticket**; the `code-review` skill; **Run a night**; **One ticket**; **Opening a PR**; **Retrospective** (`mmw-mode/playbooks/retrospective.md`); the `retro` skill.
24. **A shared language and ADRs, and what they point to exists.**
    Takes: M2, kept (the glossary is `CONTEXT.md`, or `CONTEXT-MAP.md` and the `CONTEXT.md` of each context it lists: the names the owner's repositories already use, kept by the owner's decision where upstream renamed them `GLOSSARY.md` and `GLOSSARY-MAP.md`); M31, adapted (triage is carried by the label state machine in `mmw-mode/references/github-issues.md` `## Three label sets` and the owner's two decisions in `mmw-mode/references/ticket.md` `## Handing it back`).
    Home: the `domain-modeling` skill; `docs/adr/`.
25. **A prototype is code that answers a question,** kept in the repository with its verdict; a code shape that reaches beyond one ticket is settled by competing sketches.
    Takes: M16, adapted (the verdict, not the code, is what the real build takes); P19, kept (options are compared in prototypes, `architect` sketches and `arena`).
    Home: the `prototype` skill; the `architect` and `arena` skills. A product's signed-off screens live in `design/<product>/`, written by the `design-pages` skill.
26. **Each repository is set up once and skills only read the setup;** the repository's files are placed by how long they stay true.
    Takes: M19, adapted (`setup-mmw` also writes `TESTING.md` and has Set up code checkers write the repository's `scripts/check`).
    Home: the `setup-mmw` skill; **Set up code checkers**; the repository's `scripts/check`, whose default tier `dispatch.sh land` and `advance` run on each merge result.

## Proof

27. **A criterion is a command.** A judgement goes to review, a person's reaction to a ticket for a person, and what cannot yet be reached gets a tool built to reach it first.
    Takes: M3, adapted (the red-green loop became a ticket's criteria, run by a script); P7, adapted (the decidable condition is `CHECK:` and `EXPECT:`); P11, adapted (build the tool to reach it); P13, kept (never relax the condition to pass).
    Home: the `mmw-mode` skill's `references/ticket.md`; the `verify-ticket` skill; **Work a ticket** step **Read yourself in and write the code** (red counts only when the behaviour is absent; a check that will not pass is answered in the code).
28. **A bug fix starts from a reproduction that goes red, every line of the ticket traces to runtime evidence, the fix lands as one ticket, and the reproduction is run again on the same surface.**
    Takes: M12, kept (matt's `diagnosing-bugs` is folded into **Bug fix**: the loop that goes red, the minimised repro, ranked hypotheses with predictions, tagged instrumentation, the missing seam opened as a Refactoring ticket); P18, adapted (the fix goes to a worker through **One ticket**; edits a refuted hypothesis motivated are reverted).
    Home: **Bug fix**; the `tdd` skill.
29. **Proof happens on the real product, from every entry of the feature.**
    Takes: P7, kept; P9, adapted (`control-ui` and `control-cli` taken from `cursor-team-kit`); M3, kept (the browser is a feedback loop).
    Home: `principle-prove-it-works`; the `control-cli` and `control-ui` skills; the `create-verification-skill` skill.
30. **The writer is not the judge, and a conclusion is judged once.**
    Takes: M10, adapted (four axes: Standards, Spec, Tests and Correctness); P8, adapted (only the independent review and the doubt toward review comments); P16, adapted (the orchestrator writes no code).
    Home: **Work a ticket**; the `code-review` skill; **One ticket**; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `## Editing`.
31. **Start from what exists, then decide whether to write;** less code, deep modules, delete before changing, no defence for what has not happened; the weight of the process follows the size of the task.
    Takes: P1, kept (`principle-laziness-protocol`); M4, kept; P21, adapted (a change one ticket can carry takes no spec); P37, kept (when in doubt, delete).
    Home: `principle-start-from-what-exists`; `principle-laziness-protocol`; the `codebase-design` skill; **Feature**; **Improve the architecture** (M4's survey for deepening).

## The night's machinery

32. **Code a worker writes lands only through its ticket.**
    Takes: P2, adapted (one workspace per ticket rather than per agent); P22, adapted (one writer per file, written in the ticket's Owns); M8, kept (blocking edges between tickets); M23, adapted (the machine merges into the night's branch; the default branch stays the owner's).
    Home: the `mmw-mode` skill's `references/ticket.md` (Owns); the `dispatch` skill's `dispatch.sh land`.
33. **A ticket's state is a fold of its events; each fact has one record, written by the step that changes it.**
    Takes: M9, adapted (state from events, not labels); M18, adapted (kept in step extends to every standing file); P22, adapted (one record per fact).
    Home: the `verify-ticket` skill's `scripts/events.py`; `docs/adr/0038-repository-files-are-layered-by-lifetime.md`.
34. **Wake, never poll; the night has no clock;** whether a session is alive is judged by processes that spend no tokens.
    Takes: P13, adapted (woken only by events, no heartbeat).
    Home: the `dispatch` skill's `scripts/relay.py` and `scripts/watchdog.py`; **Run a night**.
35. **No gate is silent:** a check that ran and did nothing is found.
    Takes: P7, adapted (inconclusive is not a pass, extended to every gate).
    Home: `principle-fail-loudly`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Scripts and judgement`; **Work a ticket** step **Read yourself in and write the code**.
36. **A script is a tool and judgement is the agent's;** a rule a script enforces is not written again as prose.
    Takes: P10, adapted (lessons go into structure, enforced by scripts); P11, adapted (the tool is the agent's lever; judgement is not handed to it); M21, adapted (Matt has no runtime; MMW's mechanical rules are enforced by scripts).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 2, `### Scripts and judgement`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 5.
37. **The owner understands a night in a few minutes in the morning, from one pull request.**
    Takes: P13, adapted (the decision log's review became the night summary on the pull request); M23, kept.
    Home: **Run a night**; the `dispatch` skill's `scripts/status.py` and `dispatch.sh finish`.

## Learning and rules

38. **A lesson goes where it is enforced or read, a mechanism first:** a mistake a script can catch becomes a check in the repository's `scripts/check`; a judgement that holds in every repository goes into a principle; a fact of one repository goes into its `TESTING.md`, its glossary or an ADR. A repository keeps no coding standard of its own, and no skill writes into its `AGENTS.md` or `CLAUDE.md`: the owner, other tools and other agents edit those files, so nothing would keep a skill's lines there true. One exception: `setup-mmw` creates a root `CLAUDE.md` holding only the line `@AGENTS.md` when the repository has none, and never edits one that exists, because Claude Code reads only `CLAUDE.md` when one exists, so a one-line import guarantees `AGENTS.md` reaches it.
    Takes: M11, adapted (the retro runs when the night closes, and its proposals have fixed destinations the owner approves; a judgement call goes into a principle, not into a standards file of the repository); P10, kept; P28, adapted (skill text found wrong mid-task is fixed as its own change after the task in the day, and registered through the `register-problem` skill).
    Home: the `correct` skill; the `register-problem` skill; the principles, indexed in `mmw-mode` `## Principles`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 4 and 5; `mmw-mode` `references/owning-a-task.md` `## Non-negotiables` (skill text found wrong); **Retrospective** (`mmw-mode/playbooks/retrospective.md`); the `retro` skill.

## The toolbox

39. **One set serves every host.**
    Takes: M5, kept (small, editable, composable, not tied to a model); M25, kept (no host-specific way of invoking); M30, adapted (no plugin: `install.sh` symlinks one installed checkout).
    Home: `mmw-v4/install.sh`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Paths and host neutrality`; the repository's `AGENTS.md` `## Gotchas`.
40. **When this repository changes itself, the running version is frozen;** the version being changed never takes over the run that changes it.
    Takes: no upstream intent.
    Home: the repository's `AGENTS.md` `## Self-hosting boundary`.
41. **Memory is kept per repository;** a worker reads the retrieved index when it starts.
    Takes: no upstream intent.
    Home: none in the set yet; Memory returns with its own block.

## UI acceptance

42. **The design package is the UI's standard answer; e2e tests are written in the day and read-only at night.**
    Takes: P9, adapted (verification skills are generated per product; tests are written in the day and read-only at night, rather than kept current by review).
    Home: **To tickets** step **Write each acceptance criterion**; **Work a ticket** step **Read yourself in and write the code**, the **A file outside Owns** rule; the `mmw-mode` skill's `references/ticket.md`.

## Departures

What an upstream does and MMW deliberately does not, with the intents that decide it. A finding that proposes one of these back names what changed about the reason.

| Upstream | Not taken | Why |
| --- | --- | --- |
| P12 | No written plan; the code is the spec | The owner does not read code; the spec and the tickets are what the owner can accept (1, 23) |
| P15 | Steps copied verbatim into a to-do list, a skipped step kept with its reason | Progress is read from the ticket's events and the branch (33) |
| P26 | Bound to Cursor, with a separate generated directory tree for Claude Code | One text serves every host, with the host's general-purpose subagent (39, 14) |
| P8, P20 (the rest) | A stack of PRs, one verdict per PR bound to its patch | One pull request for a night or for a day's change; a conclusion is judged once (30, 32) |
| P13 (the rest) | A decision log reviewed by another vendor's model before hand-back | No decision log is kept; a night's facts are events and the night summary (33, 37) |
| P13 (the rest) | Long-running Orchestrate and Autonomous run | **Run a night** and the ticket's events carry it (34, 37) |
| P19, P3 (the rest) | `interrogate`: cross-model adversarial review | The `code-review` skill's four axes, on one model, judged once (30) |
| P4 (the rest) | Every section's whole body in the mode's `SKILL.md` | The seven headings stay in `SKILL.md`; what only a task's owner uses (the routes, sending sessions, the reply to the owner) is in `references/owning-a-task.md`, so an agent sent to one file neither routes itself nor writes its hand-back by the owner's reply rules (5, 8) |
| P35 (the rest) | A shipped subagent definition that forces a read of the mode | Every prompt that starts an agent, subagent or session, opens with reading the mode, on any host; the file it names keeps a sent agent to the mode's first layer (5, 13) |
| P36 (the rest) | The model configuration as a host's standing rule | Configuration lives only in `~/.mmw/models.json`, changed through `models.py` (14) |
| P38 (the rest) | The user selects the mode from the menu before each message, relying on the host to attach the skill | The mode's own description asks for the read, on every host (5, 39) |
| M5 (the rest), M20 | The person picks the entry, orchestrates each step and remembers the skills (the person is the index) | The owner does not read code and is away at night; the mode is the one router and index, and the night is orchestrated by the machine (2, 5, 22) |
| M6 (half) | Orchestrating skills never call each other | The playbooks form the trunk: To spec ends by running To tickets, One ticket runs Opening a PR (23) |
| P21 (the rest) | A change one agent can finish skips the ticket, and its session writes it | Every change outside a night goes through one ticket: the session writes the plan, the owner says go, a worker writes the change (1, 23, 30); direct-commit exceptions are listed only in the `mmw-mode` skill's `references/owning-a-task.md` `## Playbooks` |
| M17 (the rest) | The person confirms the seams | A seam is an engineering decision (3, 21) |
| M21 | No runtime; the person triggers every step | Mechanical rules are enforced by scripts, and the night is driven by the machine (36) |
| M22 | Very short skills that leave the how to the model | Copied skills keep upstream's text; a playbook must finish at night with nobody to ask, so each step states its criterion (22, 17) |
| M27 (the rest) | A router skill | The mode's route lines are the one router (5) |
| M29 (the rest) | Buckets: promoted, in progress, rarely used, deprecated | One owner and no published set; every directory with a `SKILL.md` is installed (2, 15) |
| M30 (the rest) | The plugin as a read-only subscription | Nothing is packaged; a change reaches the installed checkout through the release steps (39) |
| M32 | Versioned releases with changesets and a changelog | One owner and no subscribers; every release step is a git commit or push (2, 39) |
| P40 | Unattended work fired by Cursor's automation files | A night is started by `dispatch` and woken by the relay, on any host (34, 39) |
| P3 (the rest) | Adjusting each subagent's reasoning and speed to its job | Only the row the step names in `~/.mmw/models.json`, set by the owner, decides its strength (14). Owner decision. |
| P44 (the rest) | User-only `/sharpen`, unspoken framing and immediate work | To spec step **Check that nothing load-bearing is undecided** names `sharpen` and returns its conclusions with that step's questions in one batch (3, 21, 22). MMW names it in only one step, with the owner's decisions and the day's settled scope limiting overspecification. Owner decision. |
| P45 | `figure-it-out` designing a playbook when none matches | Every task matches a route; work one ticket cannot carry goes through To spec (5, 23). Owner decision. |
