# Context Map

One vocabulary, seven bounded contexts. A term is defined in one of them; its `_Home_` line names the file that states the fact, and that file is right when the two disagree. The contexts live under `docs/contexts/` rather than beside their code because the code of most of them is a skill directory symlinked whole into every host, which holds only what the agent holding the skill reads or runs.

How to read an entry, in each context: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour).

What is written here is acted on, not just read: specs and tickets take their wording from these entries, a night worker names code after them without anyone to ask, and review holds a diff to them. So write a definition only once the user has settled it or its `_Home_` bears it out, and put a word under `_Avoid_` only when it is actually wrong in this repository's text: every word listed there becomes a correction someone will make.

## Contexts

- [Toolbox](./docs/contexts/toolbox/CONTEXT.md): MMW as a repository and install target — skills, subtrees, install locations, prompts, hosts, notes and ADRs
- [Tickets](./docs/contexts/tickets/CONTEXT.md): what a spec and a ticket are, how they are written, published and linted, and the labels and queues they carry
- [Ticket run](./docs/contexts/ticket-run/CONTEXT.md): one ticket being worked from claim to close — events on the ticket, criteria runs, code review, the worker's final run, the advisor, the closing steps and the closeout
- [Night](./docs/contexts/night/CONTEXT.md): dispatching sessions onto tickets, runners and adapters, workspaces and worktrees, base and project branches, the relay, the watchdog and the turn guard, and the orchestrator's commands
- [UI acceptance](./docs/contexts/ui-acceptance/CONTEXT.md): the design side (Claude Design, design package, scenes), the screen contract, the oracles (story, boundary, journey), the lease and `.mmw/target.json`
- [Task board](./docs/contexts/task-board/CONTEXT.md): the local browser page, its registry and supervisor
- [Release](./docs/contexts/release/CONTEXT.md): shipping an installable package for a product on the current branch — the release manifest, the release engine and its release loop, and the diagnosis and repair of a failed build

## Relationships

- **Tickets → Ticket run**: a published ticket (sections, criteria, labels), with the spec sections and baselines it names, is what the worker works from; the run writes its events back onto it as comments
- **Ticket run → Night**: the events a run posts (`ticket.passed`, `ticket.returned`, `reviewer.reported`, …) are what the relay turns into wakes and what `advance` lands
- **Night → Tickets**: `advance` reads the frontier off ticket labels and blocking edges; `reverify` hands a red landed ticket back to the `needs-triage` queue
- **Tickets ↔ UI acceptance**: a page ticket's story and boundary criteria and a critical-flow ticket's journey criteria name the oracles bare and cite the screen contract and design package as baselines; the screen-contract lint runs inside `--lint`
- **UI acceptance → Night**: the lease's product slot is what `worker.queued` waits on and what landing gives back
- **Task board → Ticket run, Night**: the task board reads ticket state through `events.py`, `issue_tree.py` and `ghlist.py`, and writes the same `models.json` as `models.py config`
- **Toolbox → all**: `install.sh`, `skills.txt`, `models.json` and the notes decide what every other context runs on; `host`, `subagent` and `--tools` are shared vocabulary defined here
