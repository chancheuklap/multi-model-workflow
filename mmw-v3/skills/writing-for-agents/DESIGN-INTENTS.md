# MMW design intents

What MMW's skill set is built to keep true, and the standard a change to it is held to. **Authoring or modifying a skill** reads it at **Place it** to name the intent a change serves; **Review the skill set** traces each intent that bears on its scope. A change that breaks an intent is not made without the owner's word; MMW's deliberate departures from its upstreams, listed below, are decisions, not gaps.

Each intent says what is kept, the upstream intents it takes from [`UPSTREAM-INTENTS.md`](UPSTREAM-INTENTS.md) (kept as upstream has it, or adapted, and how), and its home: the files whose text carries the rule an agent acts on. This file is an index: the rule itself is written in its home, where the acting agent reads it. A change that adds, changes or drops an intent, or moves its home, changes its entry here in the same commit.

## Purpose and who it serves

1. **The owner, who does not read code, can trust a closed ticket and a shipped product.** Every other intent serves this one.
   Takes: P1, adapted (quality is sought so the owner can let go without reading the code, not to run more agents); P2, adapted (the unit trusted is a closed ticket, not an agent).
   Home: `mmw-v3/prompt/shared.md`.
2. **The set serves one owner.** No team and no human code review: every human gate falls on the owner, so gates are few and placed in the day where possible.
   Takes: P23, kept (pstack is the base, made the owner's own: `mmw-mode`); M5, adapted (control stays with the owner's product decisions, not with orchestrating each step).
   Home: `mmw-v3/prompt/shared.md`; `mmw-mode` `## Autonomy`.
3. **Product decisions are the owner's, engineering decisions the agent's.** Only the owner's decisions are asked; reversible work is done and then reported; no is an acceptable answer.
   Takes: M1, adapted (only product decisions go to the person); M17, adapted (the owner still approves the ticket breakdown; seams are the agent's); P6, adapted (adds the list of the owner's decisions, and the default an unattended session takes and records).
   Home: `mmw-v3/prompt/shared.md`; `mmw-mode` `## Autonomy`.
4. **A reply to the owner leads with principle and effect, and every claim carries its evidence or its label,** so the owner can judge it without reading code. The rules every reply shares are written once, in the mode; a playbook's Reply holds only what is unique to it.
   Takes: P14, adapted (written for an owner who does not read code); P34, kept.
   Home: `mmw-mode` `## Writing the reply`.

## How the set is built and runs

5. **One entry routes each task to one playbook.** Every session reads the mode because it is told to read the file, not because a person types a command or the model recalls it: a session the owner opens is told by the hook, a session a script starts by the first sentence of its start prompt. The mode names; other components hold the how; its sections are divided by the moment they are used.
   Takes: P4, kept (`mmw-mode` has `poteto-mode`'s seven sections in its order); P38, adapted (forced by hook and start prompt instead of a host's reminder field); P30, kept (only the mode is read every time); M7, adapted (the trunk's stages became playbooks behind route lines); M27, adapted (the route lines are the one router).
   Home: `mmw-mode` `## Playbooks`; `mmw-mode` `scripts/mode-hook.py`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## mode`.
6. **A text goes in the component that answers who needs it and at which moment, not the one its type suggests:** mode, playbook, principle, skill, reference, script, subagent prompt, configuration, user-level prompt. References and scripts hang under the skill that uses them.
   Takes: P29, adapted (adds the user-level prompt and configuration; no subagent definitions); M24, adapted (one skill, one directory; shared material placed by the moment it is used).
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The components and where they live`, `## The method`.
7. **A playbook is not a skill.** It is opened only by a route line or another playbook, has a fixed shape, and every step ends on `Done when`. The order of a task lives only in its playbook.
   Takes: P31, adapted (every step carries its completion criterion); M6, adapted (orchestrating skills became playbooks; disciplines stay skills).
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## playbook`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Rules and completion criteria`.
8. **A rule enters the session at the moment it applies.** One principle per skill, one index line in the mode, read in full when applied and named in the reply; references split by branch; material every run uses stays in the main file; context is finite.
   Takes: P5, P32 and P33, kept; P25, adapted (only the rule that a subagent's brief states what it returns and how long); M13, kept (a pointer's wording decides when material is reached; progressive disclosure); M14, kept (`handoff` and Pause safely point to existing artifacts).
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`; `mmw-mode` `## Principles`, `## Subagents`.
9. **Most skills run only when named; a few the model picks up by their description.** An always-loaded description costs context, so it holds only the trigger.
   Takes: M26, adapted (the same trade, split as named-only against picked-by-description rather than person- against model-invoked); P30, adapted (pstack leaves 1 of 50 skills to the model, MMW 13 of 52); M6, adapted (the split has a different axis).
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Descriptions`; [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md) `## Invocation`.
10. **Skills are peers composed by name.** A skill hands work to another by naming it and the job; it never copies or restates the other's rules, and names no install path. A hard setup dependency gets one line naming what to run; a soft one, a mention.
    Takes: M25, adapted (the skill's name only, not a host's Skill tool; any skill can be named by any other); M24, kept (shared material lives in the skill that owns it); M28, kept; P37, kept (delegate by name, never restate); M33, kept (reading a glossary is a pointer; building the model names `domain-modeling`).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 6 and 7, `### Hand-offs`.
11. **A rule sits in the text the acting agent reads at the moment it acts.** A worker's rule written in another skill, a script comment, the glossary or an ADR reaches no worker. A pointer comes at or before the first step that needs it. What people read (the course, the ADRs) is kept apart from what agents read.
    Takes: M13, adapted (adds placement by the acting agent); P39, kept.
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`.
12. **A hand-off is an edge with one shape.** What one step leaves is what the next reads, under the same name; every outcome has a reader; between sessions there is a completion signal the next one receives; each event has one instruction across the set; no choice is left to the model's habits.
    Takes: M14, adapted (hand-off documents became a ticket's fixed headings and events); M9, adapted (what is handed over lives on the tracker).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`.
13. **A start prompt carries only data** (the ticket, a base commit, where the task came from); rules arrive through the mode and the playbook it loads. A subagent's brief holds everything it needs and states what it returns and how long.
    Takes: P35, adapted (no subagent definition; the start prompt makes a session read the mode); P17, adapted (a subagent's brief is complete).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Prompts written for other agents`.
14. **Models by strength.** Work that needs another model or must run outside the turn is a session role, started by `dispatch` and listed in `roles.json`; everything else uses the host's general-purpose subagent, and the set defines none. Each role's model is recorded only in `~/.mmw/models.json`, changed only through `models.py`.
    Takes: P3, adapted (another model means another session; the second opinion is the advisor session); P36, adapted (configuration in `models.json`, not in a host rule); P17, adapted (the worker keeps its session for its one fix).
    Home: `mmw-mode` `## Subagents`; the `dispatch` skill's `roles.json` and `scripts/models.py`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## subagent`.
15. **One home per fact, registered in the same change.** A new playbook gets its route line, a new principle its index line, a new reference or script is named by the step that uses it, and copied text gets its row in `mmw-v3/imports.tsv` with every edit. `check_wiring.py`, `check_imports.py` and `check-interfaces.py` hold this at the start of every test suite.
    Takes: M18, adapted (kept in step by checks); M29, adapted (no buckets: every directory with a `SKILL.md` is installed); P37, adapted (the frontmatter and link checks run first in every suite).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Redundancy and bloat`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 6.
16. **From an upstream, take the content, not only the shape.** Before writing a component, read the upstream component doing the closest job; where both sides do one job, read both whole and keep the one that does more (pstack is not the default winner); a component only an upstream has comes in when a step needs it.
    Takes: P23, adapted (the owner's own mode on pstack's base, taken piece by piece after comparison).
    Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 1, 2 and 8; [`UPSTREAM-INTENTS.md`](UPSTREAM-INTENTS.md).
17. **A skill hands over understanding, then trusts the model.** It says what the work is for, who depends on it and what a shallow result costs, with the reason beside each rule; then it states the goal, the constraints, the judgement calls and the completion criterion, and leaves the ordinary moves to the model.
    Takes: M22, adapted (Matt trusts the model with very short text; MMW writes the full criterion where a night has nobody to ask); P37, kept (keep only prose that changes a decision).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 1 and 4.
18. **A change to the skill text is proven by a fresh agent walking a real task with only its trigger;** tests prove the scripts, not the text.
    Takes: P37, adapted (structural changes get a walk rather than only a test); P23, adapted (a walk on a real task rather than a blind eval).
    Home: [`WALKING-A-SKILL-SET.md`](WALKING-A-SKILL-SET.md); **Authoring or modifying a skill** step 5.
19. **Text for an agent leaves no branch without a way on and no choice unguided;** examples use a neutral domain; a refusal puts the next step in its first lines.
    Takes: M13, adapted (adds the set's placement and writing rules).
    Home: `writing-for-agents` `SKILL.md`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`, `### Examples`, `### Refusals and output an agent reads`.

## The day

20. **A fact that can be looked up or run is looked up or run by the agent;** understanding comes before changing; only steps a person alone can take become a script that walks them through.
    Takes: M1, kept (facts are the agent's); P6, adapted (only "run it rather than ask"); P24, kept (`how`, `why`, `teach`); M15, kept (`wizard`, `to-questionnaire`).
    Home: `mmw-mode` `## Autonomy`; the `how`, `why`, `teach`, `wizard` and `to-questionnaire` skills.
21. **Align before acting: grill until the questions run out.** Engineering decisions such as the data shape and the seam are the agent's, written in the spec.
    Takes: M1, adapted (a round of questions waits for the fact-finding subagent); M17, adapted (seams are not put to the owner); P19, adapted (the data shape is an engineering decision in the spec).
    Home: the `grilling` skill; **Write a spec** step 3.
22. **The day settles every decision the owner holds, into the spec and the tickets; the night has nobody to ask.** The night copies what the day settled and does not improve on it; where a copy does not hold, it opens a child saying so.
    Takes: P13, adapted (the unattended contract became the ticket and its criteria; an owner's decision met at night is recorded with its options and default); M9, adapted (decisions live in the spec and tickets on the tracker).
    Home: `mmw-mode` `## Autonomy` (**Unattended**); **Write a spec**; **Cut tickets**; `principle-baseline-is-the-contract`.
23. **The day's trunk: write a spec, cut it into narrow tickets through every layer (a task graph), implement, review once, retro.** A written plan is kept.
    Takes: M7, kept; M8, adapted (tickets carry Owns, Seam and runnable criteria); M3, kept (test first is the `tdd` skill's; the red-green loop's other half is intent 27); P20, adapted (the unit of delivery is the ticket, not the PR).
    Home: **Write a spec**; **Cut tickets**; **Work a ticket**; **Review a ticket**; the `retro` skill.
24. **A shared language and ADRs, and what they point to exists.**
    Takes: M2, kept (the glossary is `CONTEXT.md`); M31, kept (triage reads `.out-of-scope/` first).
    Home: the `domain-modeling` skill; `CONTEXT-MAP.md`; `docs/adr/`; the `triage` skill.
25. **Claude Design is the one source of a product's screens; a prototype is a throwaway question.**
    Takes: M16, adapted (signed-off screens moved from code prototypes to Claude Design); P19, adapted (options are compared in prototypes and Claude Design).
    Home: **Design in Claude Design**; **Pull a design**; the `prototype` skill.
26. **Each repository is set up once and skills only read the setup;** the repository's files are placed by how long they stay true.
    Takes: M19, adapted (`setup-mmw` also writes `.mmw/` and the standing files).
    Home: the `setup-mmw` skill.

## Proof

27. **A criterion is a command.** It goes red on the old code first and can fail for the defect it guards. A judgement goes to review, a person's reaction to a ticket for a person, and what cannot yet be reached gets a tool built to reach it first.
    Takes: M3, adapted (the red-green loop became a ticket's criteria, run by a script); P7, adapted (the decidable condition is `CHECK:` and `EXPECT:`); P11, adapted (build the tool to reach it); P13, kept (never relax the condition to pass).
    Home: the `verify-ticket` skill's `references/ticket-format.md`; `principle-a-check-must-be-able-to-fail`; `principle-fix-the-product-not-the-check`.
28. **A bug fix starts from a reproduction that goes red, every changed line has runtime evidence, and the fix lands as one ticket.**
    Takes: M12, kept; P18, adapted (the fix lands through **Run one ticket**).
    Home: **Bug fix**; the `diagnosing-bugs` skill.
29. **Proof happens on the real product, from every entry of the feature.** Every product can be started, health-checked, driven and captured, and the knowledge of driving it lives in the product's repository.
    Takes: P7, kept; P9, adapted (`control-ui` and `control-cli` taken from `cursor-team-kit`); M3, kept (the browser is a feedback loop).
    Home: the `ui-acceptance` skill; `mmw-mode` `references/feature-map.md`; `principle-prove-it-works`.
30. **The writer is not the judge, and a conclusion is judged once.** The worker runs the criteria, another session reviews once, the worker fixes once, and closing only checks the record; a later step reads that record and never judges the same conclusion again. A review finding is fixed by default or refuted with evidence. The worker runs the final criteria itself, a trade ADR 0026 accepted.
    Takes: M10, adapted (three axes, Spec, Standards and Tests, plus UI for a ticket with interface acceptance); P8, adapted (only the independent review and the doubt toward review comments); P16, adapted (the orchestrator writes no code).
    Home: **Work a ticket**; **Review a ticket**; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `## Editing`.
31. **Start from what exists, then decide whether to write;** less code, deep modules, delete before changing, no defence for what has not happened; the weight of the process follows the size of the task.
    Takes: P1, kept (`principle-laziness-protocol`); M4, kept; P21, adapted (a small change takes no spec and no ticket); P37, kept (when in doubt, delete).
    Home: `principle-start-from-what-exists`; `principle-laziness-protocol`; the `codebase-design` skill; **Make a small change**.

## The night's machinery

32. **Code lands only through a ticket.** Parallel work rests on one writer per file; merging follows the remote; a ticket bounces once, and the second time goes to the morning's triage.
    Takes: P2, adapted (one workspace per ticket rather than per agent); P22, adapted (one writer per file, written in the ticket's Owns); M8, kept (blocking edges between tickets); M23, adapted (the machine merges into the night's branch; the default branch stays the owner's).
    Home: the `verify-ticket` skill's `references/ticket-format.md` (Owns); the `dispatch` skill's `dispatch.sh land`.
33. **A ticket's state is a fold of its events; each fact has one record, written by the step that changes it.** Standing files are updated in the flow; the tracker and the repository's files each hold their own facts.
    Takes: M9, adapted (state from events, not labels); M18, adapted (kept in step extends to every standing file); P22, adapted (one record per fact).
    Home: the `verify-ticket` skill's `scripts/events.py`; `mmw-mode` `references/feature-map.md`; the `setup-mmw` skill; `docs/adr/0038-repository-files-are-layered-by-lifetime.md`.
34. **Wake, never poll; the night has no clock;** whether a session is alive is judged by processes that spend no tokens.
    Takes: P13, adapted (woken only by events, no heartbeat).
    Home: the `dispatch` skill's `scripts/relay.py` and `scripts/watchdog.py`; **Run a night**.
35. **No gate is silent:** a check that ran and did nothing is found.
    Takes: P7, adapted (inconclusive is not a pass, extended to every gate).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Scripts and judgement`; `principle-a-check-must-be-able-to-fail`.
36. **A script is a tool and judgement is the agent's;** a rule a script enforces is not written again as prose.
    Takes: P10, adapted (lessons go into structure, enforced by scripts); P11, adapted (the tool is the agent's lever; judgement is not handed to it); M21, adapted (Matt has no runtime; MMW's mechanical rules are enforced by scripts).
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 2, `### Scripts and judgement`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 5.
37. **The owner understands a night in a few minutes in the morning.** The night is finished only after the owner accepts it; merging into the default branch is the owner's release decision.
    Takes: P13, adapted (the cross-model review of the decision log became the night summary and the retro); M23, kept.
    Home: **Run a night**; the `dispatch` skill's `scripts/status.py`.

## Learning and rules

38. **A lesson goes into a mechanism first:** a mechanical mistake becomes a check, a judgement call goes into `CODING_STANDARDS.md`, prose comes last; a rule changes with the owner's approval. The default is to edit what exists or delete, not to add a component.
    Takes: M11, adapted (the retro runs when the night closes, and its proposals have fixed destinations the owner approves); P10, kept.
    Home: the `retro` skill; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 4 and 5.

## The toolbox

39. **One set serves every host.** Nothing is packaged; one text serves every host and runner, and a difference is written as a capability; the runner sits behind one boundary. Skills take effect from the installed checkout; a change is released by commit, `main`, the installed checkout and a push, and releasing is the owner's call.
    Takes: M5, kept (small, editable, composable, not tied to a model); M25, kept (no host-specific way of invoking); M30, adapted (no plugin: `install.sh` symlinks one installed checkout).
    Home: `mmw-v3/install.sh`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Paths and host neutrality`; the repository's `AGENTS.md` `## Gotchas`.
40. **When this repository changes itself, the running version is frozen;** the version being changed never takes over the run that changes it.
    Takes: no upstream intent.
    Home: the repository's `AGENTS.md` `## Self-hosting boundary`.
41. **Memory is kept per repository;** a worker reads the retrieved index when it starts.
    Takes: no upstream intent.
    Home: `mmw-mode` `references/memory.md`.

## Departures

What an upstream does and MMW deliberately does not, with the intents that decide it. A finding that proposes one of these back names what changed about the reason.

| Upstream | Not taken | Why |
| --- | --- | --- |
| P12 | No written plan; the code is the spec | The owner does not read code; the spec and the tickets are what the owner can accept (1, 23) |
| P15 | Steps copied verbatim into a to-do list | Progress is read from the events (33) |
| P26 | Bound to Cursor: its subagent types, `/loop`, cloud agents, rule files | One text serves every host, with the host's general-purpose subagent (39, 14) |
| P27 | Work starts from a sentence in the conversation; the PR is the unit | The unit is the ticket and the tracker is the work queue (32, 33) |
| P8, P20 (the rest) | PRs, one verdict per PR bound to the patch, a contiguous verified stack | No PRs; code lands only through a ticket; judged once (30, 32) |
| P13 (the rest) | A decision-log file reviewed by another vendor's model before hand-back | Decisions are posted on the ticket; the night's facts are events and the night summary (33, 37) |
| P13 (the rest) | Long-running Orchestrate, Autonomous run, `figure-it-out`, Session pickup | **Run a night** and the ticket's events carry it (34, 37) |
| P19, P3 (the rest) | `architect`, `arena`, `swarm`, `interrogate`: competing designs and cross-model adversarial review | Judged once; designs are settled in the day's grilling, prototypes and Claude Design (21, 25, 30) |
| P9 (the rest) | A feature map kept true by periodic review | Standing files are updated by the step that changes the fact; a review runs when the owner asks (33) |
| P17 (the rest) | A new subagent for every new round of work | The worker keeps its session for its one fix; its context is what the fix needs (30) |
| P23 (the rest) | `automate-me` builds the mode from the user's history | `mmw-mode` is kept by the retro and by **Authoring or modifying a skill** (38) |
| P25 (the rest) | The `guard-the-context-window` principle itself | `mmw-mode` `## Subagents` carries it, keeping only what a brief returns and how long (8) |
| P35 (the rest) | A shipped subagent definition that forces a read of the mode | A session role reads the mode from its start prompt; a subagent gets a complete prompt from its skill and does not need the mode (13, 14) |
| P36 (the rest) | The model configuration as a host's standing rule | Configuration lives only in `~/.mmw/models.json`, changed through `models.py` (14) |
| P38 (the rest) | The mode kept in effect by a host's reminder field | The hook and the start prompt force the read, on every host (5, 39) |
| M5 (the rest), M20 | The person picks the entry, orchestrates each step and remembers the skills (the person is the index) | The owner does not read code and is away at night; the mode is the one router and index, and the night is orchestrated by the machine (2, 5, 22) |
| M6 (half) | Orchestrating skills never call each other | The playbooks form the trunk: Write a spec ends by running Cut tickets, Bug fix runs Run one ticket (23) |
| M17 (the rest) | The person confirms the seams | A seam is an engineering decision (3, 21) |
| M21 | No runtime; the person triggers every step | Mechanical rules are enforced by scripts, and the night is driven by the machine (36) |
| M22 | Very short skills that leave the how to the model | Copied skills keep upstream's text; a playbook must finish at night with nobody to ask, so each step states its criterion (22, 17) |
| M27 (the rest) | A router skill | The mode's route lines are the one router (5) |
| M29 (the rest) | Buckets: promoted, in progress, rarely used, deprecated | One owner and no published set; every directory with a `SKILL.md` is installed (2, 15) |
| M30 (the rest) | The plugin as a read-only subscription | Nothing is packaged; a change reaches the installed checkout through the release steps (39) |
| M32 | Versioned releases with changesets and a changelog | One owner and no subscribers; every release step is a git commit or push (2, 39) |
| P40 | Unattended work fired by Cursor's automation files | A night is started by `dispatch` and woken by the relay, on any host (34, 39) |
| P41 | One shared closing step that opens a PR | No PRs; how each playbook commits follows its situation (32, 15) |

## Taken, without a home yet

- **P28, a broken skill is not worked around.** Its home is to be a line in `mmw-mode` `## Non-negotiables`: skill or playbook text found wrong mid-task is neither worked around nor folded into the change in hand; in the day it is fixed on its own through **Authoring or modifying a skill**, at night it is left for the retro. The only sentence that says anything now, in the Owns paragraph of the `verify-ticket` skill's `references/ticket-format.md`, is read by no daytime session and has a night edit the installed skill directly; it is replaced in the same change.
