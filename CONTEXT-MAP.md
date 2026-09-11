# Context Map

One vocabulary, six bounded contexts. A term is defined in exactly one of them; its `_Home_` line names the file the definition is taken from, and that file wins when the two disagree. The contexts live under `docs/contexts/` rather than beside their code because the code of most of them is a skill directory symlinked whole into every host, which holds only what the agent holding the skill reads or runs.

## Contexts

- [Toolbox](./docs/contexts/toolbox/CONTEXT.md): MMW as a repository and install target — skills, subtrees, install locations, prompts, hosts, notes, ADRs, and the rules on how skill text is written
- [Tickets](./docs/contexts/tickets/CONTEXT.md): what a spec and a ticket are, how they are written, published and linted, and the labels and queues they carry
- [Ticket run](./docs/contexts/ticket-run/CONTEXT.md): one ticket being worked from claim to close — events on the ticket, criteria runs, code review, the verifier, the advisor, the closing steps and the closeout gate
- [Night](./docs/contexts/night/CONTEXT.md): dispatching sessions onto tickets, runners and adapters, workspaces and worktrees, base and project branches, the relay, the watchdog and the turn guard, and the main agent's night commands
- [UI acceptance](./docs/contexts/ui-acceptance/CONTEXT.md): the design side (Claude Design, handoff package, scenes), the screen contract, the judges (story, boundary, journey), the lease and `.mmw/target.json`
- [Task board](./docs/contexts/task-board/CONTEXT.md): the local browser board, its registry and supervisor

## Relationships

- **Tickets → Ticket run**: a published ticket (sections, criteria, labels) is the only input of the worker; the run writes events back onto it and never edits its body
- **Ticket run → Night**: the events a run posts (`ticket.passed`, `ticket.returned`, `reviewer.reported`, …) are what the relay turns into wakes and what `advance` lands; the night reads the fold and never a runner
- **Night → Tickets**: `advance` reads the frontier off ticket labels and blocking links; `reverify` hands a red landed ticket back to the `needs-triage` queue
- **Tickets ↔ UI acceptance**: an interface ticket's story, boundary and journey criteria name the judges bare and cite the screen contract and handoff package as baselines; the contract lint runs inside `--lint`
- **UI acceptance → Night**: the lease's product slot is what `worker.queued` waits on and what landing gives back
- **Task board → Ticket run, Night**: the board reads ticket state through `events.py`, `tree.py` and `ghlist.py`, and writes the same `models.json` as `models.py config`
- **Toolbox → all**: `install.sh`, `skills.txt`, `models.json` and the notes decide what every other context runs on; `host`, `subagent` and `--tools` are shared vocabulary defined here
