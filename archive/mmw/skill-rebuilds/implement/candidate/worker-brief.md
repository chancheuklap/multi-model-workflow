# Worker brief

The task names every path. Open those yourself.

When the task names a plan, follow it. When it names an agent brief and no plan, follow the brief and its seam.

When the Read field lists artifact refs, run `mmw artifact path` for each, then read the index and the files it lists. `none` means skip.

Stay in this worktree's source and tests. Leave `docs/` as they are. Stay inside the ticket and the plan. Use `git add` and `git commit`. Leave history as written. Do not push.

TDD is `/mmw-tdd`. Run the repo `TESTING.md` commands. End with a passing state. Cite the ticket in the commit message.

If ticket, plan, spec, and code disagree, stop and say where. If a type, function, or fixture the task assumes is missing, report it.

End the report with exactly one of:

- **Done** — every acceptance criterion holds; tests passed
- **Done with concerns** — same, plus where you are uneasy and why it waited
- **Missing context** — material you need is not in hand
- **Stuck** — you tried; include what you ran and what is larger than the ticket
