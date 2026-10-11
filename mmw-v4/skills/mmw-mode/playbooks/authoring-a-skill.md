### Authoring or modifying a skill

**You own one change to the skill set, from the owner's words to its proof on a real task.**

A skill change is a project like any other, with its own standards and its own proof: it runs the general flow for its size, held to the skill set's standards, and is proven once. Every agent that loads the changed text acts on it in cases its writer did not foresee, with no one to ask: a rule written in a second place drifts from the first, and a rule without its reason fails in the case nobody listed. The temptation is to answer each slip with one more sentence; every sentence costs attention on every run that loads the file, so the change deletes before it adds.

1. **Open the ticket.** Open a ticket and its `fix-<n>` as `../references/ticket.md` `## Opening a ticket` says, with `Playbook: Authoring or modifying a skill` and the owner's words under `## Problem`. A ticket that already has its `fix-<n>` keeps them. Done when the ticket is open and `fix-<n>` is on origin.
2. **Read the standards.** Search the skill set for the meaning first. A meaning the text already states as asked needs no change: tell the owner where it says so and whether the installed checkout (the one `~/.mmw/installed-root` names) carries it yet, close the ticket with that answer, and stop. Otherwise everything this change writes, text and scripts alike, keeps to these standards:
   - The entry in the `writing-for-agents` skill's `DESIGN-INTENTS.md` for the intent the change serves. A change that would break an intent, or bring back one of its departures, is not made: tell the owner which intent and why, and wait for their word.
   - Which component, and so which file, each passage belongs in: the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md`.
   - How text is written: the `writing-for-agents` skill's `SKILL.md` whole, since each of its levers bears on every passage, and the `writing-for-agents` skill's `SKILL-SET-RULES.md` `## Checks` and `## Editing`.

   Done when the intent the change serves is named and every passage you will write has one component and one file, or the owner has heard that the text already states the change.
3. **Write the ticket, by size.** Text and scripts take the same flow.
   - A change one ticket can carry: fill the ticket in as `../references/ticket.md` `## Opening a ticket` says. **What to build** names each passage, the component and file it goes in, and the standards of step 2 it keeps to, which are baselines under **Read first**. The acceptance criteria are the checks of **Prove it, once** below that a command decides and that read a file this change touches; the worker writes the text.
   - A larger one: hand it back as too big for one ticket, and on the owner's word run the To spec playbook (`playbooks/to-spec.md`), which hands on to To tickets. Each Implementation Decisions subsection that changes the skill set cites the standards of step 2, so To tickets copies them into its tickets' **Read first**, and Testing Decisions turns each check of **Prove it, once** that a command decides into an acceptance criterion of every ticket that changes a file the check reads. The spec states decisions; the night's tickets write the text, from the files as they stand.

   Done when every section below `## Problem` is filled, or the change is named as too big for one ticket.
4. **Hand it back.** As `../references/ticket.md` `## Handing it back` says. Done when the owner has said go and One ticket runs, or To spec runs, or the ticket is in `needs-triage` or closed.

**Prove it, once.** One ticket step 4 runs this once the ticket passed, in `.worktrees/issue-<n>`; for a larger change, once the owner has accepted the night and `finish` has run. From the repository root, run each check that applies:
- When a script changed, the suites **principle-run-the-smallest-test-set** picks (`bash mmw-v4/tests/<name>/run.sh`).
- `uv run -q mmw-v4/tests/lib/check_skill_frontmatter.py` exits 0: every skill's frontmatter holds only what the `writing-for-agents` skill's `SKILL-SET-RULES.md` `### Descriptions` allows.
- `python3 mmw-v4/tests/lib/check_wiring.py` prints `WIRING OK`.
- The `grep` of the `writing-for-agents` skill's `SKILL-SET-RULES.md` `### Paths and host neutrality` finds no hit that section does not pass.
- When a playbook a session is sent to, a start prompt, the relay's wakes, a `RESUME:` step or the role table changed, `python3 mmw-v4/skills/dispatch/scripts/check-interfaces.py` prints `INTERFACES OK`.

Then have one fresh agent walk one real task the change touches, on the changed text read from that checkout, as the `writing-for-agents` skill's `WALKING-A-SKILL-SET.md` `### List the tasks` and `### A fresh agent's walk` say. Its record of the walk is the task's load. A place where the agent ended wrong, stopped short of the completion criterion, or guessed at a sentence this change wrote fails the check: the change does not land. Every other guess goes into the Reply as a finding for a later change: each fresh agent finds a new guess somewhere, and fixing each one adds a sentence that raises the next.

**A ticket that came back.** When the owner picks it from `needs-triage`, read why on the ticket and go back to step 2 with that evidence.

When in doubt, delete. Keep only prose that changes a decision. Match tone to scope. Point at structural sources (types, READMEs, config) per the **encode-lessons-in-structure** principle skill. Delegate to other skills by name. Don't restate. A workflow you keep hitting but isn't captured → propose a new skill. A skill describes what is true now, with no history of its own edits (**principle-files-describe-the-present**).

**Reply:** the intent the change serves; each passage the ticket asks for and the component it goes to; what it deletes; the criteria; for a larger change, that it goes to To spec and why; when a skill's `description` changes, that it takes effect in a new session. The checks and the walk of **Prove it, once**, with their commands, results and the walk's load, are what One ticket reports.
