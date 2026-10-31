# Open the preparation record


A preparation outside any spec opens its record before writing durable assets, before the full plan is known:

1. Write the body with `## Problem` alone. For an actual calling playbook, its first line is `Playbook: <title>`. A directly requested method omits that line. Record the symptom or goal in the owner's exact words, or an explicitly marked observation. Keep this section unchanged after opening. Then run `gh issue create --title "<what is wrong or wanted, in a few words>" --label mmw:problem --body-file <file>`, creating the label first when the repository lacks it, from `LABELS` in the **verify-ticket** skill's `scripts/verify-ticket.py`. `mmw:problem` is its kind until the owner says Go, when One ticket's **Ready** step, or for skill text alone Authoring or modifying a skill step 6, changes it to `mmw:ticket`. It carries no status label while you write the plan. `verify-ticket.py --lint` passes it, no worker can claim it without `ready-for-agent`, and no `advance` reaches it, since it sits under no spec.
2. Keep the effort branch supplied by the caller, including an existing PR repair branch or map branch. When none exists, from a checkout of the project branch, `git fetch origin`, then `git worktree add .worktrees/fix-<n> -b fix-<n> origin/<project branch>` and `git -C .worktrees/fix-<n> push -u origin fix-<n>`. The project branch is the branch the owner's work merges into: the one this checkout is on, unless that is the repository's default branch, which takes no work directly; then ask the owner which branch it is. When `fix-<n>` already exists, use it.

A ticket already open keeps its number and its body: its playbook's first step opens only the `fix-<n>` it lacks.

The caller works in the supplied effort worktree. The calling method writes its preparation assets there and commits and pushes them before execution. Implementation code and scripts are written by the worker; Authoring's skill-text exception stays with its own method. Filling the plan is the independent writing entry, not this opening call.

A problem a session encounters while doing something else is registered with the **register-problem** skill rather than opened here.

An issue someone else opened is not worked as it stands. Open an issue of our own whose `## Problem` quotes it with its link, and leave the original as it is. Opening a PR closes it once the pull request merges. A child issue keeps its number and becomes a ticket in place on the owner's Go, through One ticket's **Ready** step of the **mmw-mode** skill (`playbooks/one-ticket.md`). Preserve its opening ``A `<kind>` child of #<n>`` line when writing its plan, because **Ready** reads the original ticket number there.


Done when the existing or newly opened problem record and its effort branch are available to the caller. Return their identities; do not fill or execute a ticket in this entry.
