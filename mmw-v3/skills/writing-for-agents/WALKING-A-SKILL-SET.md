# Walking a skill set

A walk is a **cognitive walkthrough** (the usability-inspection method): for each task an agent does with the set, you read and run what that agent would, in its order, holding nothing it would not hold. A **task** is one job an agent is entered into a skill to do (consult an advisor, publish a spec, work one ticket); a skill entered in the middle of a bigger task is walked from its entry to its return. A skill is judged by how an agent uses it inside its tasks and how it joins the skills before and after; a per-file defect count misses both.

### List the tasks

A skill, or a playbook, principle or reference inside one, is entered three ways: a branch its description or its route line triggers on; a prompt that starts an agent into it (built by a script, or written by a model from a template); a sentence in other text or a script that sends the agent to it by name or by step. A principle is also entered by every task its index line's condition in the mode fits. `grep` its name across every skill and script in the set for the third kind, then read the scoped text for entries described without the name.

Done when every entry of everything in scope maps to a task, or is listed as out of scope.

### Walk each task

Start from what the agent holds at entry: the description, the start prompt, or the text that sent it. Open only what the text in front of you points to. Where the text says what a script or CLI does, accepts, reads or prints, check it against the source or `--help`. Record, per step: each file you opened and why, its word count, the skill it belongs to, and which of its sections the step used (a passage that passes fact 1 of [What skill text is for](SKILL-SET-RULES.md#what-skill-text-is-for) is recorded as read by the task, not as unused); each term you had to resolve; each choice you made without guidance; and where the text ends before the task does. Walk the outcomes that happen in use: success, and each failure the history shows or a normal input produces. A principle has no steps of its own: walk it inside a task that applies it, to that task's end.

Done when each task reaches its completion criterion or a recorded finding, and every step has its load recorded.

### A fresh agent's walk

- Green tests prove the scripts, not that the text reads well; report them on a separate line.
- The text is proven by a run: a fresh agent given only the trigger and a real job (one the tracker or the repository's history shows was done with this text; where history has none, one the user would plausibly give, which the walk record calls made up) does the task. Watch which files it opens, where it guesses, and where it stops before the completion criterion. A sentence present in the text is not a behaviour observed; a claim that the text now changes behaviour is unverified until such a run shows it.
- The fresh agent's brief carries the trigger (the user's words or the start prompt), the job (the smallest real instance of the task that reaches the changed text), that it opens only what the text in front of it points to and does the job on paper (it writes nothing, and walks a step that would write as far as deciding what it would write), the record [Walk each task](#walk-each-task) asks for, the checkout the changed text is read from, and a length limit on its report.
- On a host that cannot start a subagent, give the user the trigger and the job to run in a new session, and list the walk as not done until that session's result comes back.

