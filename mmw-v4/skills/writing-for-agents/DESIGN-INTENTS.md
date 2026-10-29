# MMW design intents

What MMW's skill set is built to keep true, and the standard a change to it is held to. **Authoring or modifying a skill** reads it at **Judge it against the design** to name the intent a change serves. A change that breaks an intent is not made without the owner's word; MMW's deliberate departures from its upstreams, listed below, are decisions, not gaps.

Each intent says what is kept and its home: the files whose text carries the rule an agent acts on. The upstream mapping lives in [`UPSTREAM.md`](UPSTREAM.md). This file is an index: the rule itself is written in its home, where the acting agent reads it. A change that adds, changes or drops an intent, or moves its home, changes its entry here in the same commit.

## Purpose and who it serves

1. **The owner, who does not read code, can trust a closed ticket and a shipped product.** Every other intent serves this one.
   Home: `mmw-v4/prompt/shared.md`.
2. **The set serves one owner.** No team and no human code review: every human gate falls on the owner, so gates are few and placed in the day where possible.
   Home: `mmw-v4/prompt/shared.md`; `mmw-mode` `## Autonomy`.
3. **Product decisions are the owner's, engineering decisions the agent's.**
   Home: `principle-never-block-on-the-human`; `mmw-mode` `## Autonomy`.
4. **A reply to the owner leads with principle and effect, and every claim carries its evidence or its label,** so the owner can judge it without reading code.
   Home: `mmw-mode` `references/handling-a-request.md` `## Writing the reply`; `wait-what`.

## How the set is built and runs

5. **One entry routes each task to one playbook.**
   Home: `mmw-mode`'s description and `## Playbooks`, and its `references/handling-a-request.md`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## mode`; the **Authoring or modifying a skill** route line in `mmw-mode` `references/handling-a-request.md` `## Playbooks`.
6. **A text goes in the component that answers who needs it and at which moment, not the one its type suggests:** mode, playbook, principle, skill, reference, script, subagent prompt, configuration, user-level prompt.
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The components and where they live`, `## The method`.
7. **A playbook is not a skill.**
   Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## playbook`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Rules and completion criteria`.
8. **A rule enters the session at the moment it applies.**
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`; `mmw-mode` `## Principles`, `## Subagents`; `principle-guard-the-context-window`.
9. **Most skills run only when named; a few the model picks up by their description.**
   Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Descriptions`; [`SKILL-MECHANICS.md`](SKILL-MECHANICS.md) `## Invocation`.
10. **Skills are peers composed by name.**
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 6 and 7, `### Hand-offs`.
11. **A rule sits in the text the acting agent reads at the moment it acts.**
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Load and disclosure`.
12. **A hand-off is an edge with one shape.**
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`.
13. **A start prompt carries data and one pointer** (the ticket, a base commit, where the task came from, then `Read the mmw-mode skill in full, then follow <what>.`, <what> being the file the agent works by, then `It is your whole task: …`); rules arrive through the mode and that file. The step that sends the agent names <what>, so the agent never guesses its job. A subagent's prompt opens and ends the same way, names the file or the steps it follows, holds everything else it needs, and states what it returns, where, and how long.
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Prompts written for other agents`. `mmw-mode` `SKILL.md` `## Subagents`; the `dispatch` skill's `roles.json`.
14. **Models by strength.**
    Home: `mmw-mode` `## Subagents` and `references/handling-a-request.md` `## Subagents`; the `dispatch` skill's `roles.json` session roles and `subagents` section, and `scripts/models.py`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## subagent`.
15. **One home per fact, registered in the same change.** `check_wiring.py` and `check_skill_frontmatter.py` hold this at the start of every suite under `mmw-v4/tests/` but `lib`, and the dispatch suite runs `check-interfaces.py`.
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 7, `### Redundancy and bloat`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 6.
16. **From an upstream, take the content, not only the shape.**
    Home: [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 1, 2 and 8; [`UPSTREAM.md`](UPSTREAM.md).
17. **A skill hands over understanding, then trusts the model.**
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) facts 1 and 4.
18. **A change to the skill text is proven by a fresh agent walking a real task with only its trigger when the change alters what an agent does in a task;** tests prove the scripts, not the text.
    Home: [`WALKING-A-SKILL-SET.md`](WALKING-A-SKILL-SET.md); **Authoring or modifying a skill**'s **Prove it, once**.
19. **Text for an agent leaves no branch without a way on and no choice unguided;** examples use a neutral domain; a refusal puts the next step in its first lines.
    Home: `writing-for-agents` `SKILL.md`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Hand-offs`, `### Examples`, `### Refusals and output an agent reads`.

## The day

20. **A fact that can be looked up or run is looked up or run by the agent;** understanding comes before changing; only steps a person alone can take become a script that walks them through.
    Home: `mmw-mode` `## Autonomy`; the `how`, `why` and `teach` skills.
21. **Align before acting: grill until the questions run out.**
    Home: the `grilling` skill; **Grill with docs**; **To spec**; `sharpen`.
22. **The day settles every decision the owner holds, into the spec and the tickets; the night has nobody to ask.**
    Home: `mmw-mode` `## Autonomy` (**Unattended**); **To spec**; **To tickets**; `principle-baseline-is-the-contract`.
23. **The trunk: write a spec, cut it into narrow tickets through every layer (a task graph), implement, review once, deliver one pull request, retro.**
    Home: **To spec**; **To tickets**; **Work a ticket**; the `code-review` skill; **Run a night**; **One ticket**; **Opening a PR**; **Retrospective** (`mmw-mode/playbooks/retrospective.md`); the `retro` skill.
24. **A shared language and ADRs, and what they point to exists.**
    Home: the `domain-modeling` skill; `docs/adr/`.
25. **A prototype is code that answers a question,** kept in the repository, its verdict on the ticket that asked the question; a code shape that reaches beyond one ticket is settled by competing sketches.
    Home: the `prototype` skill; the `prototype` skill's `SKETCH.md`; the `arena` skill. A UI prototype's conclusion lives in the feature file; its winner is the UI baseline, under the `prototype` skill's `UI.md`.
26. **Each repository is set up once and skills only read the setup;** the repository's files are placed by how long they stay true.
    Home: the `setup-mmw` skill; **Set up code checkers**; the repository's `scripts/check`, whose default tier `dispatch.sh land` and `advance` run on each merge result.

## Proof

27. **A criterion is a command.** A judgement goes to review, a person's reaction to a ticket for a person, and what cannot yet be reached gets a tool built to reach it first.
    Home: the `mmw-mode` skill's `references/ticket.md`; the `verify-ticket` skill; **Work a ticket** step **Read yourself in and write the code** (red counts only when the behaviour is absent; a check that will not pass is answered in the code).
28. **A bug fix starts from a reproduction that goes red, every line of the ticket traces to runtime evidence, the fix lands as one ticket, and the reproduction is run again on the same surface.**
    Home: **Bug fix**; the `tdd` skill.
29. **Proof happens on the real product, from every entry of the feature.**
    Home: `principle-prove-it-works`; the `control-cli` and `control-ui` skills; the `create-verification-skill` skill.
30. **The writer is not the judge, and a conclusion is judged once.**
    Home: **Work a ticket**; the `code-review` skill; **One ticket**; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `## Editing`.
31. **Start from what exists, then decide whether to write;** less code, deep modules, delete before changing, no defence for what has not happened; the weight of the process follows the size of the task.
    Home: `principle-start-from-what-exists`; `principle-laziness-protocol`; the `codebase-design` skill; **Feature**; **Improve the architecture** (M4's survey for deepening).

## The night's machinery

32. **Code a worker writes lands only through its ticket.**
    Home: the `mmw-mode` skill's `references/ticket.md` (Owns); the `dispatch` skill's `dispatch.sh land`.
33. **A ticket's state is a fold of its events; each fact has one record, written by the step that changes it.**
    Home: the `verify-ticket` skill's `scripts/events.py`; `docs/adr/0038-repository-files-are-layered-by-lifetime.md`.
34. **Wake, never poll; the night has no clock;** whether a session is alive is judged by processes that spend no tokens.
    Home: the `dispatch` skill's `scripts/relay.py` and `scripts/watchdog.py`; **Run a night**.
35. **No gate is silent:** a check that ran and did nothing is found.
    Home: `principle-fail-loudly`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Scripts and judgement`; **Work a ticket** step **Read yourself in and write the code**.
36. **A script is a tool and judgement is the agent's;** a rule a script enforces is not written again as prose.
    Home: [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) fact 2, `### Scripts and judgement`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` item 5.
37. **The owner understands a night in a few minutes in the morning, from the page the pull request's first line names; the body is the record.**
    Home: **Opening a PR** `**The record.**` and `**The owner's page.**`; **Run a night**; the `dispatch` skill's `scripts/status.py` and `dispatch.sh finish`.

## Learning and rules

38. **A lesson goes where it is enforced or read, a mechanism first:** a mistake a script can catch becomes a check in the repository's `scripts/check`; a judgement that holds in every repository goes into a principle; a fact of one repository goes into its glossary or an ADR. A repository keeps no coding standard of its own, and no skill writes into its `AGENTS.md` or `CLAUDE.md`: the owner, other tools and other agents edit those files, so nothing would keep a skill's lines there true. One exception: `setup-mmw` creates a root `CLAUDE.md` holding only the line `@AGENTS.md` when the repository has none, and never edits one that exists, because Claude Code reads only `CLAUDE.md` when one exists, so a one-line import guarantees `AGENTS.md` reaches it.

    A repository's `AGENTS.md` or `CLAUDE.md` keeps only lines that code, ADRs, a glossary or script headers cannot tell an agent in time, whose violation is costly or irreversible, and that state the owner's rules or facts outside the repository rather than inventories that age as code changes. The file states this rule in its first lines, where the owner, other tools and other agents read it before editing.

    Home: the `correct` skill; the `register-problem` skill; the principles, indexed in `mmw-mode` `## Principles`; [`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md) `## The method` items 4 and 5; `mmw-mode` `references/handling-a-request.md` `## Non-negotiables` (skill text found wrong); **Retrospective** (`mmw-mode/playbooks/retrospective.md`); the `retro` skill.

## The toolbox

39. **One set serves every host.**
    Home: `mmw-v4/install.sh`; [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md) `### Paths and host neutrality`; the repository's `AGENTS.md` `## Gotchas`.
40. **When this repository changes itself, the running version is frozen;** the version being changed never takes over the run that changes it.
    Home: the repository's `AGENTS.md` `## Self-hosting boundary`.
41. **Memory is kept per repository;** a worker reads the retrieved index when it starts.
    Home: none in the set yet; Memory returns with its own block.

## UI acceptance

42. **The winner prototype is the UI's standard answer; e2e tests are written from it in the day and read-only at night.**
    Home: the `prototype` skill's `UI.md`; the `create-verification-skill` skill; **To tickets** step **Write each acceptance criterion**; **Work a ticket** step **Read yourself in and write the code**, the **A file outside Owns** rule; the `mmw-mode` skill's `references/ticket.md`.

## Departures

What an upstream does and MMW deliberately does not, with the intents that decide it. A finding that proposes one of these back names what changed about the reason.

| Upstream | Not taken | Why |
| --- | --- | --- |
| P12 | No written plan; the code is the spec | The owner does not read code; the spec and the tickets are what the owner can accept (1, 23) |
| P15 | Steps copied verbatim into a to-do list, a skipped step kept with its reason | Progress is read from the ticket's events and the branch (33) |
| P26 | Bound to Cursor, with a separate generated directory tree for Claude Code | One text serves every host, with the host's general-purpose subagent (39, 14) |
| P8, P20 (the rest) | A stack of PRs, one verdict per PR bound to its patch | One pull request for a night or for a day's change; a conclusion is judged once (30, 32) |
| P13 (the rest) | A decision log reviewed by another vendor's model before hand-back | No separate decision log is kept: a night's facts are events and the night summary, and a Hillclimb's attempts are comments on its ticket (33, 37) |
| P13 (the rest) | Long-running Orchestrate and Autonomous run | **Run a night** and the ticket's events carry it (34, 37) |
| P19, P3 (the rest) | `interrogate`: cross-model adversarial review | The `code-review` skill's four axes, on one model, judged once (30) |
| P4 (the rest) | Every section's whole body in the mode's `SKILL.md` | The seven headings stay in `SKILL.md`; what only a session holding a request uses (the routes, sending sessions, the reply to the owner) is in `references/handling-a-request.md`, so an agent sent to one file neither routes itself nor writes its hand-back by the owner's reply rules (5, 8) |
| P35 (the rest) | A shipped subagent definition that forces a read of the mode | Every prompt that starts an agent, subagent or session, opens with reading the mode, on any host; the file it names keeps a session holding an assignment to the mode's first layer (5, 13) |
| P36 (the rest) | The model configuration as a host's standing rule | Configuration lives only in `~/.mmw/models.json`, changed through `models.py` (14) |
| P38 (the rest) | The user selects the mode from the menu before each message, relying on the host to attach the skill | The mode's own description asks for the read, and a SessionStart hook on every host prints one pointer to it, since a session the owner opens has no start prompt and the description alone went unread (#1264) (5, 13, 39) |
| M5 (the rest), M20 | The person picks the entry, orchestrates each step and remembers the skills (the person is the index) | The owner does not read code and is away at night; the mode is the one router and index, and the night is orchestrated by the machine (2, 5, 22) |
| M6 (half) | Orchestrating skills never call each other | The playbooks form the trunk: To spec ends by running To tickets, One ticket runs Opening a PR (23) |
| P21 (the rest) | A change one agent can finish skips the ticket, and its session writes it | Every change outside a night goes through one ticket and the owner's go: a worker writes code and scripts, and skill text one ticket carries is written by the Authoring session and judged by a fresh agent's walk, not a reviewer (1, 18, 23, 30); direct-commit exceptions are listed only in the `mmw-mode` skill's `references/handling-a-request.md` `## Playbooks` |
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
| P20, Opening a PR | **Descriptions**, a body briefing a code reviewer, written with `technical-writing` | One owner reads one visual page; the body is the record, and replies carry only their unique facts (2, 4, 33, 37). Owner decision. |
| E7 | Model-driven exploration, bug bash and feature charters | Fixed-step e2e tests written in the day prove the UI; Spec review compares prototype and product screenshots (42). Owner decision. |
| E8 | Migrating an existing test suite into e2e | Deferred until a product with an existing suite needs it (42). Owner decision. |
| E9 (commit rule) | Never commit generated verification assets | Assets generated during a prototype effort are committed to its branch and delivered with its PR; other direct-commit exceptions live in `mmw-mode/references/handling-a-request.md` `## Playbooks` (23, 32). Owner decision. |
