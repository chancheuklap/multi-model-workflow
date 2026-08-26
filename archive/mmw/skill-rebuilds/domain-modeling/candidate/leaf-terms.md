# project-context.md terms this round changes

Publish `/mmw-domain-modeling` English candidate, then replace these entries in `docs/context/project-context.md`. Leave the rest.

**domain model** (current name `领域模型`):
The project's long-lived language: its concepts, which leaf owns each term, and how bounded contexts relate.
_Avoid_: data model, implementation architecture, 领域模型

**authoritative reference** (current name `权威引用`):
A citation in a non-owning leaf that points at the leaf that owns the term.
_Avoid_: duplicate definition, paraphrase, 权威引用

**canonical term** (current name `canonical 术语`):
The wording the owning leaf fixes for a term.
_Avoid_: phrases listed under `_Avoid_`, invented synonyms, canonical 术语

`Context Map`, `leaf`, `ADR`, and `ADR index` keep those English names. Their definitions stay as they are, except `ADR index` still names the command `mmw artifact index adr`.
