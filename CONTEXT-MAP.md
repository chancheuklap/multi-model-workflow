# Context map

The bounded contexts defining MMW's shared language. Each term has one definition in its owning context; component entries use the skill's `name` or the Playbook's title and explain what that component is.

The glossaries live under `docs/contexts/`, outside the installed skill directories. They describe the repository's domain; skill instructions, command recipes, configuration schemas and decision history remain with their respective sources. A component's entry links to its live source. An upstream concept used unchanged retains its definition in that skill's native glossary.

Each context has a short scope description and a `## Language` section. An entry uses `**Name**:`, a one- or two-sentence definition and, where a real ambiguity exists, an `_Avoid_:` line. A family of related machine identifiers has one entry identifying its shared meaning rather than copying every field or command option.

## Contexts

- [Skill set](./docs/contexts/skill-set/CONTEXT.md). Component kinds, `mmw-mode`, every `principle-*` skill, Authoring or modifying a skill, Eval, writing standards and skill-set review vocabulary.
- [Toolbox](./docs/contexts/toolbox/CONTEXT.md). MMW as an install target, consuming repositories, hosts, configuration, shared prompts, hooks and repository setup.
- [Development](./docs/contexts/development/CONTEXT.md). Develop a change, discussion, investigation, decision maps and reusable diagnostic, performance and refactoring methods.
- [Tickets](./docs/contexts/tickets/CONTEXT.md). `to-spec`, `to-tickets`, maps, specs, independent and spec tickets, acceptance criteria, publication and queue labels.
- [Ticket run](./docs/contexts/ticket-run/CONTEXT.md). Work a ticket, `verify-ticket`, `code-review`, `advisor`, claims, events, criteria evidence and ticket closeout.
- [Night](./docs/contexts/night/CONTEXT.md). One ticket, Run a night, `dispatch`, sessions, branches, watches, landing, Opening a PR, recovery and retrospective feedback.
- [UI acceptance](./docs/contexts/ui-acceptance/CONTEXT.md). Design a UI, `prototype`, `prepare-ui-acceptance`, `test-audit`, product and formal verification methods, feature maps, acceptance targets, behavior pins and product control.
- [Task board](./docs/contexts/task-board/CONTEXT.md). The local task board, its issue presentation, freshness, server lifecycle and settings sheet.
- [Release](./docs/contexts/release/CONTEXT.md). `exe-release`, product packaging, release manifests, release-engine state, repair findings and delivery records.

## Relationships

- **Skill set → all**. Defines the component kinds and cross-task judgments that the other contexts compose. The mode selects the requested result; a Playbook owns its task workflow and a skill returns its bounded result.
- **Toolbox → all**. Installation supplies the shared skill set and user-level prompt. Host hooks point to the consuming repository's glossary and the installed MMW glossary; configuration selects how dispatched work runs.
- **Development → Tickets**. Evidence, settled decisions and baselines become an independent ticket or a spec batch through to-spec and to-tickets. Requested diagnoses, decisions and reports can end without an implementation ticket.
- **Tickets → Ticket run, Night**. A ready independent ticket enters One ticket; a ready spec batch enters Run a night. Both executors dispatch Work a ticket for implementation and preserve existing scope and authority.
- **UI acceptance ↔ Development, Tickets**. Prototype verdicts, feature descriptions and prepared tests supply implementation baselines. Product verification recipes supply executable evidence; test-audit supplies testing judgments and methods.
- **Ticket run → Night**. Ticket events carry worker and reviewer results to the relay. The executor lands passing work, handles unfinished results and returns a delivery for owner acceptance.
- **Night → Development, Skill set**. Retrospective records analysis without implementing it. Owner-approved backlog decisions return ordinary changes to their development preparation and skill-set changes to Authoring or modifying a skill.
- **Task board → Tickets, Ticket run, Night, Toolbox**. The page presents tracker records and runtime configuration using their existing meanings. Its display states are distinct from the records it presents.
- **Release → UI acceptance**. exe-release packages committed product inputs and returns an installer for the owner's install test. It is distinct from Toolbox's promotion and installation of MMW itself.
