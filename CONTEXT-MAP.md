# Context Map

One vocabulary, seven bounded contexts. A term is defined in one of them, and the entry is right when another text disagrees with it. The contexts live under `docs/contexts/` rather than beside their code because the code of most of them is a skill directory symlinked whole into every host, which holds only what the agent holding the skill reads or runs.

How to read an entry, in each context: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. An entry does not repeat what a file states (a field list, an exit code, a command's switches, the branches of a behaviour).

What is written here is acted on, not just read: specs and tickets take their wording from these entries, a night worker names code after them without anyone to ask, and review holds a diff to them. So write a definition only once the user has settled it, and put a word under `_Avoid_` only when it is actually wrong in this repository's text: every word listed there becomes a correction someone will make.

## Contexts

- [Toolbox](./docs/contexts/toolbox/CONTEXT.md): MMW as a repository and install target — the mode, its playbooks and principles, skills, upstream snapshots and the import record, install locations, prompts, hosts and ADRs
- [Tickets](./docs/contexts/tickets/CONTEXT.md): what a spec and a ticket are, how they are written, published and linted, and the kind and status labels they carry
- [Ticket run](./docs/contexts/ticket-run/CONTEXT.md): one ticket being worked from claim to close — events on the ticket, criteria runs, code review, the worker's final run, the advisor, the closing steps and the closeout
- [Night](./docs/contexts/night/CONTEXT.md): dispatching sessions onto tickets, runners and adapters, workspaces and worktrees, base and project branches, the relay, the watchdog and the turn guard, and the orchestrator's commands
- [UI acceptance](./docs/contexts/ui-acceptance/CONTEXT.md): local prototypes, design freeze, API fakes and mount points, product environment tools and verification skills, feature maps and e2e tests
- [Task board](./docs/contexts/task-board/CONTEXT.md): the local browser page, its registry and supervisor
- [Release](./docs/contexts/release/CONTEXT.md): shipping an installable package for a product on the current branch — the release manifest, the release engine and its release loop, and the diagnosis and repair of a failed build

## Relationships

- **Tickets → Ticket run**: a published ticket (sections, criteria, labels), with the spec sections and baselines it names, is what the worker works from; the run writes its events back onto it as comments
- **Ticket run → Night**: the events a run posts (`ticket.passed`, `ticket.returned`, `reviewer.reported`, …) are what the relay turns into wakes and what `advance` lands
- **Night → Tickets**: `advance` reads the frontier off ticket labels and blocking edges; `reverify` hands a red landed ticket back to `needs-triage`, awaiting the owner's decision
- **Tickets ↔ UI acceptance**: daytime ticket-writing sessions use the winner prototype as baseline, write e2e tests and pins, and copy each CHECK line from the product's `verify-<product>` Launch section; existing behavior is described in its feature map
- **UI acceptance → Night**: workers run product-target e2e CHECK lines against isolated product runs and checkout-local back-end stacks; verification assets and the winner prototype stay read-only, and a wrong test or design returns through a `contract` child for daytime correction
- **Task board → Ticket run, Night**: the task board reads ticket state through `events.py`, `issue_tree.py` and `ghlist.py`, and writes the same `models.json` as `models.py config`, with the roles `roles.json` lists
- **Toolbox → all**: `install.sh`, the `mmw-mode` skill and `models.json` decide what every other context runs on; `host`, `subagent`, playbook and principle are shared vocabulary defined here
