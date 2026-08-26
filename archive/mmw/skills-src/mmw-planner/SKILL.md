---
name: mmw-planner
description: Turn one tracer-bullet ticket into a plan a zero-context worker can execute. Used by the planner role dispatched from `/mmw-to-plan`.
user-invocable: false
---

# Planner

Write one plan for the ticket in your task. A `worker` will read the whole file in order and implement it.

Read the spec, the ticket, and the artifact refs the task names. Resolve each ref with `mmw artifact path` and read the index plus the files it lists. `none` or `[]` means skip. Copy those refs into the plan frontmatter as `artifact_refs`.

Confirm existing paths and symbols in the current source. Mark new files `Create`.

Write the plan to the path in Goal. Follow [plan-body.md](plan-body.md). Then run `mmw artifact check`. If it exits non-zero, fix the artifact-ref declarations first.

If you cannot write the plan — missing facts, ticket and spec disagree, a criterion has no proof, the direction does not hold in this codebase — stop and say what blocked you. Do not invent placeholders.

Write only that plan file. Leave spec, tickets, other plans, and source code as they are. Do not commit.
