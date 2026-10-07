# Task board prototype (#318)

## Question

What does the task board of #318 show and how does it respond: which lamp, pill and line each ticket gets from its fold, how a task's tree is laid out on the canvas, and what the detail panel says about each kind of card?

## Current conclusion

Settled in #318 sections 3 to 7 and 11 to 17: three columns (tasks, canvas, detail); a vertical trunk of containers that open to the right into their issues; one lamp answering "does this need me" (orange needs you, green running, ink done, hollow not dispatched); one pill naming the current step; blocking drawn as smooth curves coloured by how the wait stands (grey walked, green with a travelling light where the blocked ticket is running, red where the blocker has not landed).

`Component · 详情` shows a ticket the way variant A of `prototypes/board-orchestration/sidebar-events/UI/` (README section "The three variants", **A · Phase blocks**) shows it: its history as one block per phase, every event under a human-readable name, and the payload fields one click behind each event. A spec, the map and a decision ticket keep the column they had.

## Current baseline

The signed-off Claude Design handoff package is `prototypes/task-board/claude-design/`. It contains five component pages, one app page, 44 offline scenes, the data files that drew those scenes, and the compiled design system. `docs/specs/task-board/screen-contract.yaml` binds that package to the product's mounts, calls, shown values, states and failures.

The product implementation is `mmw-v2/board/`. Its ticket detail column uses phase blocks, human-readable event names, event payload disclosure, status summary, dependency rows and sub-issue rows. The map, spec and decision-ticket detail layouts remain unchanged.
