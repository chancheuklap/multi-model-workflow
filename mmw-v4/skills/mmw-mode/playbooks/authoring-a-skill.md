### Authoring or modifying a skill

**You own one change to the skill set, from the owner's words to its proof on a real task.**

A skill change is a project like any other, with its own standards and its own proof: it runs the general flow for its size, held to the skill set's standards, and is proven once. Every agent that loads the changed text acts on it in cases its writer did not foresee, with no one to ask: a rule written in a second place drifts from the first, and a rule without its reason fails in the case nobody listed. The temptation is to answer each slip with one more sentence; every sentence costs attention on every run that loads the file, so the change deletes before it adds.

1. **Read the standards.** Search the skill set for the meaning first: a meaning the text already states as asked needs no change: tell the owner where it says so and whether the installed checkout (`~/.mmw/installed-root`) carries it yet, and stop. Otherwise everything this change writes, text and scripts alike, keeps to these standards:
   - The intent of the `writing-for-agents` skill's `DESIGN-INTENTS.md` the change serves, and its entry there. A change that would break an intent, or bring back one of its departures, is not made: tell the owner which intent and why, and wait for their word.
   - Which component, and so which file, each passage belongs in: the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md`.
   - How text is written: the `writing-for-agents` skill's `SKILL.md` whole, since each of its levers bears on every passage, and the `writing-for-agents` skill's `SKILL-SET-RULES.md` `## Checks` and `## Editing`.

   Done when the intent the change serves is named and every passage you will write has one component and one file, or the owner has heard that the text already states the change.
2. **Write it, by size.** Text and scripts take the same flow.
   - A change one session can write: write it here, committing each verifiable unit.
   - A larger one: run the To spec playbook (`playbooks/to-spec.md`), which hands on to To tickets. Each Implementation Decisions subsection that changes the skill set cites the standards of step 1, so To tickets copies them into its tickets' **Read first**, and Testing Decisions makes each check of step 3 that a command decides a criterion of the tickets whose files it reads. The spec states decisions; the night's tickets write the text, from the files as they stand.

   Done when the change is committed, or To tickets has published the batch.
3. **Prove it, once.** A change written here runs this step now; a larger one once the owner has accepted the night and `finish` has run. From the repository root, run each check that applies, and rerun it after each fix:
   - When a script changed, the suites **principle-run-the-smallest-test-set** picks (`bash mmw-v4/tests/<name>/run.sh`).
   - `uv run -q mmw-v4/tests/lib/check_skill_frontmatter.py` exits 0: every skill's frontmatter holds only what the `writing-for-agents` skill's `SKILL-SET-RULES.md` `### Descriptions` allows.
   - `python3 mmw-v4/tests/lib/check_wiring.py` prints `WIRING OK`.
   - The `grep` of the `writing-for-agents` skill's `SKILL-SET-RULES.md` `### Paths and host neutrality` finds no hit that section does not pass.
   - When a playbook a session is sent to, a start prompt, the relay's wakes, a `RESUME:` step or the role table changed, `python3 mmw-v4/skills/dispatch/scripts/check-interfaces.py` prints `INTERFACES OK`.

   After a night, the tickets' criteria have run the commands; run the `grep` alone. Then have one fresh agent walk one real task the change touches, on the changed text read from this checkout, as the `writing-for-agents` skill's `WALKING-A-SKILL-SET.md` `### List the tasks` and `### A fresh agent's walk` say. Its record of the walk is the task's load. Fix each place where the agent ended wrong, stopped short of the completion criterion, or guessed at a sentence this change wrote, through the checks above, and commit the fix; the fix is not walked again. Every other guess goes into the Reply as a finding for a later change, unfixed: each fresh agent finds a new guess somewhere, and fixing each one adds a sentence that raises the next.
   Done when every check that applies passes on the final text, with its command and output kept for the Reply, and the walk has run once, each place where the agent ended wrong, stopped short or guessed at a sentence this change wrote is fixed and committed, and every other guess is in the Reply; or the Reply lists the walk as not done.
4. **Deliver it.** A change written here: run Shared closing (`playbooks/shared-closing.md`), with step 3 as its proof. A larger one was delivered by its night's pull request.
   Done when Shared closing is done, or the night's pull request is merged.

When in doubt, delete. Keep only prose that changes a decision. Match tone to scope. Point at structural sources (types, READMEs, config) per the **encode-lessons-in-structure** principle skill. Delegate to other skills by name. Don't restate. A workflow you keep hitting but isn't captured → propose a new skill. A skill describes what is true now, with no history of its own edits (**principle-files-describe-the-present**).

**Reply:** what you wrote and the component each part went to; what you deleted; for a larger change, the spec's number and its batch, and that **Prove it, once** runs after the owner accepts the night; each check with its command and result; the walk, with where the agent guessed or stopped and its load, or that it is not done; when a skill's `description` changed, that it takes effect in a new session.
